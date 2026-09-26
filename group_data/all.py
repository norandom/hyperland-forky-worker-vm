# Settings for every host. Override per host in inventory.py host data.

# The desktop user (autologin, Hyprland session, hypr-rdp) is the SSH user;
# see inventory.py.

debian_suite = "forky"
keyboard_layout = "de"
keyboard_options = "compose:caps,shift:both_capslock_cancel,altwin:swap_ralt_rwin"

# hypr-rdp with the patches in files/hypr-rdp.
#   "release": install the .deb built by CI (Dagger) from this repo's GitHub release
#   "build":   compile on the host (needs the Rust toolchain there, ~10 min)
hypr_rdp_source = "release"
hypr_rdp_deb_url = ("https://github.com/norandom/hyperland-forky-worker-vm/releases/download/"
                    "hypr-rdp-0.1.6-3/hypr-rdp-clearcodec_0.1.6-3_amd64.deb")
hypr_rdp_deb_sha256 = "be531865fd2236ada117d31158e5985bb9dddb76690b03982c631206d2033b05"
hypr_rdp_version = "0.1.6"
hypr_rdp_sha256 = "6857d170da5d678211eb5318bb03c1bd3ff9503f5c26cf0ea05755fa63ff1d13"
hypr_rdp_codec = "clearcodec"      # clearcodec | planar | avc420
# RDP refresh: Hyprland output rate and hypr-rdp frame rate. Mouse movement CPU
# without a GPU: 60 Hz 177 %, 30 Hz 140 %, 20 Hz 85 % (pointer stays smooth).
rdp_refresh_hz = 20
hypr_rdp_fps = 20
# llvmpipe rasterizer threads for Hyprland and GL clients. Measured at 3198x1264@20:
# 1 thread scrolls at ~half the CPU of 2-3 threads (fewer threads to sync per frame).
llvmpipe_threads = 1
hypr_rdp_bind = "0.0.0.0:3389"

# Units stopped + disabled when present (minimal installs usually lack them)
disabled_units = [
    "cups.service", "cups.socket", "cups.path",
    "avahi-daemon.service", "avahi-daemon.socket",
    "bluetooth.service", "ModemManager.service", "power-profiles-daemon.service",
]


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
# Wallpaper from files/wallpaper/<name>.jpg (swaybg), or None for the plain
# background colour. Sea of Lanterns: from Enlightenment's backgrounds (BSD-2).
wallpaper = "sea-of-lanterns"

# --- System limits / VM hygiene -------------------------------------------------
tmp_size = "1G"                 # /tmp is tmpfs (RAM); Debian default is 50% of RAM
nofile_soft = 65536             # open files (Node, Java, agents); default soft limit 1024
nofile_hard = 524288
inotify_max_user_instances = 1024   # file watchers; default 128
soft_lockup_watchdog = False    # False: kernel.watchdog=0 (false alarms when the host is busy)
blacklist_modules = ["floppy", "pcspkr", "joydev"]   # unused in the VM

# JetBrainsMono Nerd Font (same release/files as Omarchy's ttf-jetbrains-mono-nerd-basic);
# Neovim/LazyVim icons need the patched glyphs.
nerd_font_version = "3.5.1"
# Nerd Fonts release archives: name -> (sha256, font files to install)
nerd_fonts = {
    "JetBrainsMono": ("04d5e8f903693f9dd13e16f867e994834e681eb3c72c0d337a770dcda09010cf",
                      ["Regular", "Bold", "Italic", "BoldItalic"]),
    # Fira Code (github.com/tonsky/FiraCode) for the terminals
    "FiraCode": ("68e3bd6164864b8b514605bc34e3a87ac401c8c48682fcce6478c70263340207",
                 ["Light", "Regular", "Retina", "Medium", "SemiBold", "Bold"]),
}
terminal_font = "FiraCode Nerd Font"

# Font rendering: "rgb" = ClearType-like subpixel (RDP shown 1:1, RGB display),
# "grayscale" = no colour fringes when the RDP client scales (Retina/HiDPI).
font_rendering = "rgb"
