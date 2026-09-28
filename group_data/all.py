# Settings for every host. Override per host in inventory.py host data.

# The desktop user (autologin, Hyprland session, hypr-rdp) is the SSH user;
# see inventory.py.

debian_suite = "forky"
# Keyboard layouts loaded together; switch with hypr-kbd / kbde / kbus / setxkbmap
# or the ⌨ bar button (first = default). Both stay in one keymap, so hypr-rdp
# follows a switch without reconnecting.
# German = Apple Magic Keyboard (2015) layout, as on the Mac: Option+L = @, Option+5/6 = [ ],
# Option+7 = |, Option+Shift+7 = \, Option+8/9 = { }, Option+E = €, Option+N = ~.
# Left Option is that Option key (lv3:lalt_switch; there is no Alt key then), right Option
# is Super (altwin:swap_ralt_rwin), right Cmd works as Option too.
keyboard_layout = "de,us"
keyboard_variant = "mac_nodeadkeys,"
# keyboard_variant = "nodeadkeys,"   # PC German layout (@ = AltGr+Q)
keyboard_options = "compose:caps,shift:both_capslock_cancel,altwin:swap_ralt_rwin,lv3:lalt_switch"

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
# With a VirGL GPU (Proxmox virtio-gl): Hyprland 13-15 % at 20, 30 or 60 Hz.
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

# --- System limits / VM hygiene -------------------------------------------------
tmp_size = "1G"                 # /tmp is tmpfs (RAM); Debian default is 50% of RAM
nofile_soft = 65536             # open files (Node, Java, agents); default soft limit 1024
nofile_hard = 524288
inotify_max_user_instances = 1024   # file watchers; default 128
soft_lockup_watchdog = False    # False: kernel.watchdog=0 (false alarms when the host is busy)
blacklist_modules = ["floppy", "pcspkr", "joydev"]   # unused in the VM

# JetBrainsMono Nerd Font (same release/files as Omarchy's ttf-jetbrains-mono-nerd-basic);
# Neovim (devicons) and the bar need the patched glyphs.
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
# Single-file fonts: name -> (url, sha256). Fixedsys Core is used by the
# Terminator "fixedsys" profile; both are public domain (Fixedsys Excelsior).
extra_fonts = {
    "FixedsysCore-Regular.ttf": (
        "https://raw.githubusercontent.com/delinx/Fixedsys-Core/cf4b8e99b1e7a357d7cbe5225323d8413b20f611/FixedsysCore-Regular.ttf",
        "43941ca11fc5bb5650d27c70c673bf629ec1491b9695b1b4e8dacc99713509bd"),
    "FSEX302.ttf": (
        "https://github.com/kika/fixedsys/releases/download/v3.09.10/FSEX302.ttf",
        "842f8fbf80f57d867aeb1d2988140d3ea8b4718e5f687035b0a3b66756df3899"),
}

# Single-binary tools from GitHub releases -> /usr/local/bin: name -> (url, sha256)
release_tools = {
    "podman-tui": ("https://github.com/containers/podman-tui/releases/download/v2.0.0/podman-tui-release-linux_amd64.zip",
                   "de1de10344a8ab636c64c2f982bdaa4e05696b642e2dd4692872f56b3254442f"),
    "zellij": ("https://github.com/zellij-org/zellij/releases/download/v0.45.1/zellij-x86_64-unknown-linux-musl.tar.gz",
               "40bcc2e03f5d5ae8e054e39f676081fe12ab70871506996ba595834c3718eefc"),
    "upmd": ("https://github.com/rezigned/upmd/releases/download/v0.2.7/upmd-x86_64-unknown-linux-gnu.tar.xz",
             "101336d7a8f4648a3bf894d5636875f1df3d219719d470096c562e0cf4d6b9aa"),
    # rclone (not in forky right now); sha256 from downloads.rclone.org/v1.75.1/SHA256SUMS
    "rclone": ("https://github.com/rclone/rclone/releases/download/v1.75.1/rclone-v1.75.1-linux-amd64.zip",
               "982b5aa772841168f8e380f139e9e787b2a105403e32b94da8676a0e1c0a13ab"),
}

# rclone FUSE mounts (systemd user services): remote name -> folder in $HOME.
# Set up the remote once on the host (rclone config, name "onedrive", type
# "onedrive", personal); until then the service is skipped.
rclone_mounts = {"onedrive": "OneDrive"}

# Little Snitch for Linux (obdev.at; needs kernel 6.12+ with BTF). Web UI:
# http://localhost:3031/ (in Chromium). None = don't install.
littlesnitch_version = "1.1.0"
littlesnitch_sha256 = "1a4bce4703ada6f74a69aec0386a4e2c96f8ab9ea1ce89303bf2775d5d8d0f1d"

# Font rendering: "rgb" = ClearType-like subpixel (RDP shown 1:1, RGB display),
# "grayscale" = no colour fringes when the RDP client scales (Retina/HiDPI).
font_rendering = "rgb"

# --- Applications ------------------------------------------------------------------
# Neovim config: github.com/norandom/nvim-simple at this commit (replaces LazyVim)
nvim_simple_commit = "70717b469ce15ade8b1186c3650a484a5202cb75"
# Obsidian .deb from github.com/obsidianmd/obsidian-releases (sha256 = GitHub's asset digest)
obsidian_version = "1.13.7"
obsidian_sha256 = "17dc33b49cb3e785ecc27edd2ea0c79e40207798b554fd2886e36ebee7af9ae0"
# Ghostty .deb for Debian forky from github.com/mkasberg/ghostty-ubuntu (sha256 = GitHub's asset digest)
ghostty_release = "1.3.1-0-ppa2"
ghostty_version = "1.3.1-0.ppa2"
ghostty_deb_version = "1.3.1-0~ppa2"
ghostty_sha256 = "d4f9207423ea7957344430a729b52edb13aff620fb27fe69434ed1d8dc80f880"

# Rust coreutils (uutils, Debian's rust-coreutils) first in PATH for the desktop
# user's shells and the Hyprland session. System services and root keep GNU coreutils.
uutils_coreutils = True

# Top bar: CPU / MEM / net with a 50 s history graph (hypr-sparkline) instead of
# plain numbers. Off: waybar's own modules, just the numbers.
bar_graphs = False
