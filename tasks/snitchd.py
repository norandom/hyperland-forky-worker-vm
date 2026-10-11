"""Egress firewall: snitchd (github.com/norandom/snitch, Go + BPF LSM; replaces Little Snitch) from
a pinned release. The service always starts in monitor mode and follows the trial and kept files
under /var/lib/snitch: deny-by-default only as a bounded trial started by hand (`sudo snitchd trial
10m`), ended at boot by snitchd-trial-boot.service; the serial console (tasks/tuning.py) is the way
back. This task never passes a mode or a duration to the daemon, never starts the boot-revert
oneshot (it would end a live trial) and never touches the kill switch, the trial or the kept file.
Switches in group_data/all.py: snitchd_enabled, snitchd_version + snitchd_sha256, snitchd_learn."""
from io import StringIO

from pyinfra import host
from pyinfra.facts.files import Sha256File
from pyinfra.facts.systemd import SystemdEnabled, SystemdStatus
from pyinfra.operations import files, server, systemd

version, sha = host.data.snitchd_version, host.data.snitchd_sha256
binary = "/usr/local/sbin/snitchd"
units = ("snitchd.service", "snitchd-trial-boot.service")
dropin_dir = "/etc/systemd/system/snitchd.service.d"
dropin = f"{dropin_dir}/learn.conf"

# --- Rules: on and off, so the file stays current (the daemon reloads a changed file itself) --
files.directory(name="/etc/snitch", path="/etc/snitch", mode="755", _sudo=True)
files.put(name="snitchd rules", src="files/snitchd/rules.toml", dest="/etc/snitch/rules.toml", mode="644",
          _sudo=True)

if host.data.snitchd_enabled:
    # --- The operator: the desktop user may use the API's write verbs (trial, rule edits). The
    # daemon ignores the file unless root-owned and not group/other-writable, so 644 root:root.
    # Written before the binary so it exists on the first start.
    files.put(name="snitchd operator (the desktop user may use the API's write verbs)",
              src=StringIO(host.data.desktop_user + "\n"), dest="/etc/snitch/operator",
              user="root", group="root", mode="644", _sudo=True)

    # --- The pinned release: downloaded to a temp dir, digest compared before `install`; a mismatch
    # names the seen and the expected digest and replaces nothing. The gate runs at execution time
    # against the installed binary's digest (a shell op is always "will change" at parse time).
    install = server.shell(
        name=f"snitchd v{version} installed (sha256 verified)",
        commands=[
            f"set -e; t=$(mktemp -d); trap 'rm -rf \"$t\"' EXIT; "
            f'curl -fsSL -o "$t/snitchd" https://github.com/norandom/snitch/releases/download/v{version}/snitchd; '
            f"got=$(sha256sum \"$t/snitchd\" | cut -d' ' -f1); "
            f'[ "$got" = "{sha}" ] || {{ echo "snitchd v{version}: sha256 $got, expected {sha}" >&2; exit 1; }}; '
            f'install -m 755 -o root -g root "$t/snitchd" {binary}'
        ],
        _if=lambda: host.get_fact(Sha256File, path=binary) != sha,
        _sudo=True,
    )

    # --- On the path: sudo's secure_path and the user's PATH lack /usr/local/sbin, so `sudo snitchd …`
    # and the root-less `snitchd check` need links (the units keep the real path; kept when off).
    for link in ("/usr/sbin/snitchd", "/usr/local/bin/snitchd"):
        files.link(name=f"snitchd on the path ({link})", path=link, target=binary, _sudo=True)

    # --- Units: verbatim copies of snitch/systemd/*.service (files/snitchd/, one header line) ------
    unit_ops = [files.put(name=u, src=f"files/snitchd/{u}", dest=f"/etc/systemd/system/{u}", mode="644", _sudo=True)
                for u in units]

    # --- Learning (snitchd_learn): a drop-in adds -learn; its absence is the plain unit. The learned
    # file is reviewed by hand and merged into files/snitchd/rules.toml, never deployed.
    if host.data.snitchd_learn:
        files.directory(name="snitchd.service.d", path=dropin_dir, mode="755", _sudo=True)
        learn = files.put(
            name="snitchd learning drop-in",
            src=StringIO("# Managed by debian-hypr\n[Service]\nExecStart=\n"
                         "ExecStart=/usr/local/sbin/snitchd -rules /etc/snitch/rules.toml -learn -learned /var/lib/snitch/learned.toml\n"),
            dest=dropin, mode="644", _sudo=True)
    else:
        learn = files.file(name="snitchd learning drop-in absent", path=dropin, present=False, _sudo=True)

    # --- Services. The boot-revert oneshot is enabled, never started here (running=False on an
    # inactive oneshot is a no-op). No restarted= on the service: the restart is its own step below.
    reload = any(op.changed for op in (*unit_ops, learn))
    systemd.service(name="snitchd-trial-boot enabled (never started by the deploy)",
                    service="snitchd-trial-boot.service", enabled=True, running=False, daemon_reload=reload, _sudo=True)
    systemd.service(name="snitchd running", service="snitchd.service", running=True, enabled=True,
                    daemon_reload=reload, _sudo=True)
    # Restart when the binary, a unit or the drop-in changed (a list of _if callables means all, so one
    # lambda over any), decided at execution time; never for the rules file. The trial and kept files
    # are left alone: the daemon reads them again after the restart.
    server.shell(name="snitchd restarted (binary, unit or drop-in changed)",
                 commands=["systemctl restart snitchd.service"],
                 _if=lambda: any(op.did_change() for op in (install, *unit_ops, learn)), _sudo=True)
else:
    # --- Off: stop and disable both units; the binary, the rules and the state files stay, so
    # enabling again needs no download. Runs only while something is still enabled or active.
    server.shell(name="snitchd off: stopped and disabled (files kept)",
                 commands=[f"systemctl disable --now {' '.join(units)}"],
                 _if=lambda: any(host.get_fact(fact, services=list(units)).get(u, False)
                                 for fact in (SystemdEnabled, SystemdStatus) for u in units),
                 _sudo=True)
