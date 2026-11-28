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
                    "hypr-rdp-0.1.6-5/hypr-rdp-clearcodec_0.1.6-5_amd64.deb")
hypr_rdp_deb_sha256 = "226a069f58a65ff60cd04a95de413563dafab75175d676160e11694878cc4aaa"
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

# Serial console: a login on ttyS0 and the kernel console on it too (the latter after a
# reboot). The way back when the network is gone, e.g. an egress firewall that denies too
# much: Proxmox UI -> the VM's "Console" with serial0, or `qm terminal <vmid>` on the host.
# The VM needs the device: `qm set <vmid> -serial0 socket` on the host (stop/start once).
serial_console = True

# Egress firewall: snitchd (github.com/norandom/snitch, tasks/snitchd.py), from boot in monitor
# mode; deny only as a bounded trial (`sudo snitchd trial 10m`, reverted at boot), the serial
# console above is the way back. False: service and boot revert stopped and disabled, files kept.
snitchd_enabled = True
snitchd_version = "1.2.0"       # tag without the v; sha256 = the snitchd asset's digest
snitchd_sha256 = "132ab7c23f2b73f37bdfe7fe7ba4ef3ced97339830668b6a2f9686b1ab8ee0b2"  # the snitchd asset of v1.2.0
snitchd_learn = False           # True: -learn, learned rules in /var/lib/snitch/learned.toml (reviewed by hand, never deployed)

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
safe_chain_version = "1.5.30"
safe_chain_installer_sha256 = "c2e65ef2ae0d51cd120866297089dde88a148a0e8a4816a111c43bd60ab8293d"

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
    "zellij": ("https://github.com/zellij-org/zellij/releases/download/v0.46.1/zellij-x86_64-unknown-linux-musl.tar.gz",
               "1633211357c236053b51d1ae6415c23f7ff71aaae8e087315e499ceca1b17fa4"),
    "upmd": ("https://github.com/rezigned/upmd/releases/download/v0.2.8/upmd-x86_64-unknown-linux-gnu.tar.xz",
             "9befb2bd007e8425602c144f039326dc2a94a117019aca12c959b9b9ebc982ea"),
    # Kubernetes: kubectl from dl.k8s.io (Debian's is 4 minor versions behind; kubectl should
    # be within one minor version of the cluster), helm (not in Debian)
    "kubectl": ("https://dl.k8s.io/release/v1.37.1/bin/linux/amd64/kubectl",
                "65691ff77eb6fa44c908b77a1082c9f092c3b9733b5cefabec0d1104890e21a8"),
    "helm": ("https://get.helm.sh/helm-v4.3.0-linux-amd64.tar.gz",
             "86584a54def73570558f66f5111cc53dfed56689637ae32c1201205d494f54fb"),
    # Kubernetes TUIs: k9s (browse / act: logs, shell, edit, scale), ktop (btop-like live
    # node / pod usage; also `kubectl ktop`); sha256 from the projects' checksum files
    "k9s": ("https://github.com/derailed/k9s/releases/download/v0.51.0/k9s_Linux_amd64.tar.gz",
            "c3752ad51a5a4015a113819c4eeb6e55a4d0e4b8e652494797532f6fc8161dd7"),
    "ktop": ("https://github.com/vladimirvivien/ktop/releases/download/v0.7.9/ktop_v0.7.9_linux_amd64.tar.gz",
             "4b47308a97068266e364c84493e163395f4e362f7bbe2129881e90168f6fe7f0"),
    # Bitwarden CLI: the standalone build from the GitHub release, not npm (@bitwarden/cli
    # 2026.4.0 on npm was backdoored for 93 minutes, Apr 2026); sha256 = GitHub's digest
    "bw": ("https://github.com/bitwarden/clients/releases/download/cli-v2026.9.1/bw-linux-2026.9.1.zip",
           "84289eaf59d691f04242605112f21b00e8dba65acdedbc60dde001a2860f2097"),
    # rc: the RustFS CLI (S3 + RustFS admin; also works with MinIO / AWS S3), github.com/rustfs/cli
    "rc": ("https://github.com/rustfs/cli/releases/download/v0.1.38/rustfs-cli-linux-amd64-v0.1.38.tar.gz",
           "9741028f46f5f5a152da1e3257980e9c7be2714c21b5b14a8bb5ac7d93f882e9"),
    # rclone (not in forky right now); sha256 from downloads.rclone.org/v1.75.2/SHA256SUMS
    "rclone": ("https://github.com/rclone/rclone/releases/download/v1.76.0/rclone-v1.76.0-linux-amd64.zip",
               "b00f00b3266c3764413afe599d3ec316f6f43b3e0ea8a0bc1d186d2133e46df7"),
}

# rclone FUSE mounts (systemd user services): remote name -> folder in $HOME.
# Set up the remote once on the host (rclone config, name "onedrive", type
# "onedrive", personal); until then the service is skipped.
rclone_mounts = {"onedrive": "OneDrive"}

# Font rendering: "rgb" = ClearType-like subpixel (RDP shown 1:1, RGB display),
# "grayscale" = no colour fringes when the RDP client scales (Retina/HiDPI).
font_rendering = "rgb"

# --- Applications ------------------------------------------------------------------
# Neovim config: github.com/norandom/nvim-simple at this commit (replaces LazyVim)
nvim_simple_commit = "70717b469ce15ade8b1186c3650a484a5202cb75"
# Obsidian .deb from github.com/obsidianmd/obsidian-releases (sha256 = GitHub's asset digest)
obsidian_version = "1.15.1"
obsidian_sha256 = "f77b6dfc8c040214f2febad2b1b9b051b6a838a47b0f4fb90a31cfcb79b8fcec"
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

# ax: Google's agentic orchestration runtime CLI (github.com/google/ax), "kubectl for agent
# tasks" on a cluster running Agent Substrate. No release binaries: built with Go at this
# tag (Go fetches the toolchain the tag needs, checksum-verified). None = don't install.
ax_version = "v0.3.1"
ax_go_toolchain = "go1.27.4"

# Bitwarden desktop .deb from github.com/bitwarden/clients (pinned; sha256 = GitHub's digest)
bitwarden_version = "2026.9.1"
bitwarden_sha256 = "da5e0177da10805152268ee9d29cbaf278c4ea10650b0ebcd03c5697537fab82"

# Client role: tools for client work, installed only on the hostnames listed (removed
# elsewhere). ~4.6 GB together: ArtCraft ~880 MB, Quarto 450 MB, Positron 2.3 GB, VS Code 1 GB.
client_hosts = ["debb"]
# ArtCraft apps (github.com/storytold, Apache-2.0, early alpha): PdfCraft (PDF workbench),
# DesignCraft (page layout), GridCraft (Excel-style spreadsheet), LightCraft (Lightroom-style
# photo editor), WordCraft (Word-style), DeckCraft (PowerPoint-style),
# CADCraft (AutoCAD-style). .deb, no new dependencies
# (mesa-vulkan-drivers skipped, EGL is enough).
artcraft_apps = {  # name: (version, sha256 = the release's SHA256SUMS / GitHub digest)
    "pdfcraft": ("0.22.0", "a7e0e781e55adc633b68b417ec9860115ccaa2cc636588f183ae03e66a5edcdb"),
    "designcraft": ("0.21.1", "29e1d9656ac49b8e87ec0b675c89c1357b44657705e347d5e006a26f9ee6a2e6"),
    "gridcraft": ("0.19.1", "3e9b093ee3bed8b1f008ea56c8d60e6a96890e24317be2bbb93e431f3c9d8112"),
    "lightcraft": ("0.21.1", "c91ef47bec44995d99ce58e6c748af9fa6ab1ff1c11de9e290e0b8231176dad1"),
    "wordcraft": ("0.19.1", "9ba913f053ab9cb9160d080f0c8db08c1c9eb94b3bdc7f2c0a0d784e034a5bd5"),
    "deckcraft": ("0.19.1", "a6ebfb4a230e569c8ae8848611bb9813378b351557bc07b6964d8a348d264459"),
    "cadcraft": ("0.20.1", "8e6ad1f487d6cd44dbcb73cd88ef1efb52252a2071094f2c23a468a641a06faa"),
}

# Away lock (tasks/away.py): seconds without an RDP session before sudo and ptrace
# lock (they unlock as soon as the session is back)
away_grace_seconds = 600

# Client role .debs: package -> (dpkg version, url, sha256), no recommends. Quarto
# (quarto-dev/quarto-cli, GitHub digest), Positron (Posit's data science IDE, VS Code-based;
# sha256 from cdn.posit.co/positron/releases/deb/x86_64/releases.json), VS Code (sha256 from
# update.code.visualstudio.com/api/versions/<ver>/linux-deb-x64/stable; Microsoft's apt repo is
# declined). Both editors get the debian-hypr themes (files/vscode, tools/vscodetheme.py).
client_debs = {
    "quarto": ("1.11.9", "https://github.com/quarto-dev/quarto-cli/releases/download/v1.11.9/quarto-1.11.9-linux-amd64.deb",
               "64078d1623d9ab89da766591f3410a0756f3737a37efb0897c7e84b863bf092a"),
    "positron": ("2026.11.1+4-1794024154", "https://cdn.posit.co/positron/releases/deb/x86_64/Positron-2026.11.1-4-x64.deb",
                 "3569815ed54083add81a7856f81b33a2d64b3c8e349e2b0cff8154d8fbf29106"),
    "code": ("1.148.0-1795526052", "https://vscode.download.prss.microsoft.com/dbazure/download/stable/"
             "661626d0e72f97806550790a98fb87116c9db825/code_1.148.0-1795526052_amd64.deb",
             "da33c10565e17b83f93508a365222f31bba116ab5c9e7bef7f562783943fd513"),
}

# Quarto (client role) with Python, no R: code cells run in a uv env with these packages
# (QUARTO_PYTHON points to it, ~/.local/share/quarto-python); PDF output through TinyTeX
# (`quarto install tinytex`, per user in ~/.TinyTeX, ~250 MB). Positron brings its own kernel.
quarto_python = ["nbclient==0.11.0", "nbformat==5.11.1", "ipykernel==7.4.0",
                 "jupyter-client==8.10.0", "pyyaml==6.0.3"]
quarto_tinytex = True

# Start menu icons (hypr-appmenu): Windows 3.1 icons as PNG, fetched at this commit at
# deploy time (Microsoft's icons, no licence in that repo: not copied into this one).
# None = every entry keeps the application's own icon.
win31_icons_repo = "https://github.com/mRB0/many-windows-3.1-icons-in-png-format"
win31_icons_commit = "c351992eadee522c585d2ef87f08fe0e168a80ca"

# Which VM am I on? Title bars and the active border in one colour per host (tools/hostcolor.py,
# white text >= 4.6:1). List the fleet here: the position sets the hue (first 8 clearly apart);
# hosts not listed fall back to a hash of the hostname. decor_colors overrides one host by hand.
fleet_hosts = ["debb"]
decor_colors = {"debb": "#7b1e1e"}  # dark red (was petrol #0b647e from the hash)

