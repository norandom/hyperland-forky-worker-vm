# Settings for every host. Override per host in inventory.py host data.

# Desktop user (autologin, Hyprland session, hypr-rdp)
desktop_user = "mc"
desktop_home = "/home/mc"

debian_suite = "forky"
keyboard_layout = "de"
keyboard_options = "compose:caps,shift:both_capslock_cancel,altwin:swap_ralt_rwin"

# hypr-rdp (built from source with the hypr-rdp-clearcodec patches)
hypr_rdp_version = "0.1.6"
hypr_rdp_sha256 = "6857d170da5d678211eb5318bb03c1bd3ff9503f5c26cf0ea05755fa63ff1d13"
hypr_rdp_codec = "clearcodec"      # clearcodec | planar | avc420
hypr_rdp_fps = 30
hypr_rdp_bind = "0.0.0.0:3389"

# Units stopped + disabled when present (minimal installs usually lack them)
disabled_units = [
    "cups.service", "cups.socket", "cups.path",
    "avahi-daemon.service", "avahi-daemon.socket",
    "bluetooth.service", "ModemManager.service", "power-profiles-daemon.service",
]

# GRUB password: set GRUB_PASSWORD in your local environment to enable.
# Booting stays unattended; editing entries / the console needs the password.
grub_superuser = "admin"

# --- Tuning from linux-mint-optimizer (advanced_performance) --------------------
# Network: BBR + fq, TCP Fast Open, bigger buffers (not tcp_timestamps=0).
tune_net = True
# Root filesystem: noatime,commit=60 (fewer metadata writes).
tune_noatime = True
# Kernel command line (GRUB), needs a reboot. mitigations=off disables
# Spectre/Meltdown protections: accepted for this VM (runs nothing untrusted).
# Not used: elevator= (virtio disk stays on "none"), transparent_hugepage,
# intel_idle.max_cstate (no effect in a KVM guest). Empty list = untouched.
# cpuidle_haltpoll.force=1 + cpuidle.governor=haltpoll: guest polls briefly before
# halting -> lower wake-up latency (snappier RDP), costs a little host CPU.
tune_kernel_cmdline = ["mitigations=off", "audit=0", "cpuidle_haltpoll.force=1", "cpuidle.governor=haltpoll"]

# SSH: allow root login with password (Mint repo's kvm_guest_optimization).
# LAN-only VM behind NAT. False = Debian defaults (keys / no root password login).
ssh_root_password_login = True

# --- Compute profile (tuned-like, automatic) ------------------------------------
# zram tuned for numeric workloads: lz4 is several times faster than zstd and
# float arrays compress poorly anyway; half of RAM, disk swap behind it.
zram_algorithm = "lz4"
zram_size = "ram / 2"
vm_swappiness = 100            # Omarchy desktop value: 150
# CPU weight of the user's container slice (podman rootless) relative to the
# desktop/RDP/terminal slices (100). Only matters when the CPU is saturated.
container_cpu_weight = 200

# Containers: rootless podman, daemonless; docker / docker compose / docker-compose aliases.
containers = True

# --- User tools ------------------------------------------------------------------
# Aikido Safe Chain (pinned installer; checksum from the project's README)
safe_chain_version = "1.5.21"
safe_chain_installer_sha256 = "03641bfdf4d5e3b5f0450120543579d578ed6354a8cff64bcfba8c8485f14474"

# Title bars: "mac" (cream, red/green circles left) or "win311" (navy, ⊟ ⊠ right).
# Only sets the initial style; switch any time on the host: hypr-deco win311|mac
decorations_style = "win311"
# Window shadows "on"/"off" (initial; switch with hypr-shadow). CPU-drawn without a GPU.
window_shadows = "off"

# --- System limits / VM hygiene -------------------------------------------------
tmp_size = "1G"                 # /tmp is tmpfs (RAM); Debian default is 50% of RAM
nofile_soft = 65536             # open files (Node, Java, agents); default soft limit 1024
nofile_hard = 524288
inotify_max_user_instances = 1024   # file watchers; default 128
soft_lockup_watchdog = False    # False: kernel.watchdog=0 (false alarms when the host is busy)
blacklist_modules = ["floppy", "pcspkr", "joydev"]   # unused in the VM
