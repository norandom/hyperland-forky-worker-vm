"""Tuning adopted from linux-mint-optimizer, minus huge pages and the parts
that don't apply to a KVM guest. Switches: group_data/all.py."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import files, server, systemd

# --- Network: BBR + fq, Fast Open, buffers -----------------------------------------
if host.data.tune_net:
    net = files.put(
        name="Network sysctls (BBR, fq, Fast Open, buffers)",
        src="files/system/90-net.conf",
        dest="/etc/sysctl.d/90-debian-hypr-net.conf",
        mode="644",
        _sudo=True,
    )
    files.put(name="Load tcp_bbr at boot", src=StringIO("tcp_bbr\n"),
              dest="/etc/modules-load.d/bbr.conf", mode="644", _sudo=True)
    server.shell(name="Apply network sysctls", commands=["modprobe tcp_bbr", "sysctl --system"],
                 _sudo=True, _if=net.did_change)
else:
    files.file(name="No network tuning", path="/etc/sysctl.d/90-debian-hypr-net.conf",
               present=False, _sudo=True)

# --- Root filesystem: noatime,commit=60 -----------------------------------------------
if host.data.tune_noatime:
    server.shell(
        name="Root fs: noatime,commit=60 (fstab + live remount)",
        commands=[r"""set -e
opts=$(awk '$2 == "/" && $1 !~ /^#/ {print $4}' /etc/fstab)
case ",$opts," in *,noatime,*) exit 0 ;; esac
new=$(echo "$opts" | sed -E 's/(^|,)(relatime|atime|strictatime)(,|$)/\1\3/; s/^,//; s/,$//; s/,,/,/')
new="noatime,commit=60${new:+,$new}"
cp /etc/fstab /etc/fstab.bak.debian-hypr
awk -v n="$new" 'BEGIN{OFS="\t"} $2 == "/" && $1 !~ /^#/ { $4 = n } { print }' /etc/fstab.bak.debian-hypr > /etc/fstab
mount -o remount /
"""],
        _sudo=True,
    )

# --- Kernel command line via GRUB -------------------------------------------------------
args = " ".join(host.data.tune_kernel_cmdline)
grub = files.line(
    name=f"GRUB kernel cmdline: quiet {args}".rstrip(),
    path="/etc/default/grub",
    line=r"^GRUB_CMDLINE_LINUX_DEFAULT=.*",
    replace=f'GRUB_CMDLINE_LINUX_DEFAULT="quiet {args}"'.replace(' "', '"').replace('quiet "', 'quiet"'),
    _sudo=True,
)
server.shell(name="update-grub (reboot to apply)", commands=["update-grub"],
             _sudo=True, _if=grub.did_change)

# --- SSH root login with password --------------------------------------------------------
sshd = files.put(
    name="sshd: root login with password" if host.data.ssh_root_password_login else "sshd: Debian defaults",
    src=StringIO("# Managed by debian-hypr\nPermitRootLogin yes\nPasswordAuthentication yes\n"
                 if host.data.ssh_root_password_login else "# Managed by debian-hypr (defaults)\n"),
    dest="/etc/ssh/sshd_config.d/50-debian-hypr.conf",
    mode="644",
    _sudo=True,
)
server.shell(name="Validate sshd config + reload", commands=["sshd -t && systemctl reload ssh"],
             _sudo=True, _if=sshd.did_change)

# --- /tmp tmpfs size ----------------------------------------------------------------------
tmp = files.put(
    name=f"/tmp (tmpfs in RAM) capped at {host.data.tmp_size}",
    src=StringIO(f"""# Managed by debian-hypr
[Mount]
Options=mode=1777,strictatime,nosuid,nodev,size={host.data.tmp_size},nr_inodes=1m,x-systemd.graceful-option=usrquota
"""),
    dest="/etc/systemd/system/tmp.mount.d/50-debian-hypr.conf",
    mode="644",
    _sudo=True,
)
server.shell(
    name="Apply /tmp size now (remount)",
    commands=["systemctl daemon-reload", f"mount -o remount,size={host.data.tmp_size} /tmp"],
    _sudo=True,
    _if=tmp.did_change,
)

# --- open files limits ----------------------------------------------------------------------
limits = f"DefaultLimitNOFILE={host.data.nofile_soft}:{host.data.nofile_hard}\n"
for scope in ("system", "user"):
    files.put(
        name=f"systemd {scope} manager: open files {host.data.nofile_soft}:{host.data.nofile_hard}",
        src=StringIO(f"# Managed by debian-hypr\n[Manager]\n{limits}"),
        dest=f"/etc/systemd/{scope}.conf.d/50-debian-hypr-limits.conf",
        mode="644",
        _sudo=True,
    )
files.put(
    name="PAM login sessions: open files",
    src=StringIO(f"# Managed by debian-hypr\n*    soft nofile {host.data.nofile_soft}\n*    hard nofile {host.data.nofile_hard}\n"),
    dest="/etc/security/limits.d/50-debian-hypr.conf",
    mode="644",
    _sudo=True,
)

# --- kernel limits: inotify, soft-lockup watchdog ---------------------------------------------
klim = files.put(
    name="Kernel limits (inotify instances, soft-lockup watchdog)",
    src=StringIO(f"""# Managed by debian-hypr
fs.inotify.max_user_instances = {host.data.inotify_max_user_instances}
kernel.watchdog = {1 if host.data.soft_lockup_watchdog else 0}
"""),
    dest="/etc/sysctl.d/90-debian-hypr-limits.conf",
    mode="644",
    _sudo=True,
)
server.shell(name="Apply kernel limits", commands=["sysctl --system"], _sudo=True, _if=klim.did_change)

# --- unused kernel modules ------------------------------------------------------------------------
mods = host.data.blacklist_modules
bl = files.put(
    name=f"Blacklist unused modules: {' '.join(mods)}",
    src=StringIO("# Managed by debian-hypr\n" + "".join(f"blacklist {m}\ninstall {m} /bin/false\n" for m in mods)),
    dest="/etc/modprobe.d/50-debian-hypr-blacklist.conf",
    mode="644",
    _sudo=True,
)
server.shell(
    name="Unload them now + rebuild initramfs",
    commands=[" ; ".join(f"modprobe -r {m} 2>/dev/null" for m in mods) + " ; update-initramfs -u >/dev/null"],
    _sudo=True,
    _if=bl.did_change,
)
