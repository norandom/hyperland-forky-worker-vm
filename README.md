# debian-hypr

A [pyinfra](https://pyinfra.com) deploy that turns a fresh, minimal **Debian
forky** VM into the same Hyprland desktop as the Omarchy VM, **without
Omarchy**. Same window behaviour, same look, the same RDP setup 1:1, and the
same memory tuning, on a minimal footprint (no GNOME/KDE, no display manager,
no recommends).

Deploys over SSH like Ansible, from this machine:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
.venv/bin/pyinfra inventory.py deploy.py            # everything
.venv/bin/pyinfra inventory.py tasks/desktop.py     # one area
```

Target requirements: SSH key login and passwordless sudo for the user in
`inventory.py`. Settings: `group_data/all.py`. Every run is idempotent.

## New VM (recipe)

1. **Proxmox VM**: CPU type `host`, 3+ cores, 6+ GB RAM (ballooning min = max),
   VirtIO SCSI disk with *SSD emulation* + *Discard*, Display *Standard VGA*,
   Options → *QEMU Guest Agent* enabled.
2. **Install Debian forky** from the daily netinst ISO
   (`https://cdimage.debian.org/cdimage/daily-builds/daily/arch-latest/amd64/iso-cd/debian-testing-amd64-netinst.iso`).
   In *Software selection* tick only **SSH server** + standard utilities (no desktop).
   Create the user (e.g. `mc`); a root password is optional.
3. **Prepare access** (once, on the new VM as root):
   ```bash
   echo 'mc ALL=(ALL:ALL) NOPASSWD: ALL' > /etc/sudoers.d/zz-mc-nopasswd && chmod 440 /etc/sudoers.d/zz-mc-nopasswd
   ```
   and from this machine: `ssh-copy-id mc@NEW-IP`.
4. **Add it to `inventory.py`**: `("NEW-IP", {"ssh_user": "mc"})`. Per-host
   overrides go into the host data dict, e.g. `{"ssh_user": "mc", "decorations_style": "mac"}`.
5. **Deploy** (about 25 min, of which about 10 are the hypr-rdp build):
   ```bash
   .venv/bin/pyinfra inventory.py deploy.py --limit NEW-IP
   ```
6. **Reboot** once (kernel options, limits), then connect with RDP:
   user `mc`, password from `ssh mc@NEW-IP cat ~/.config/hypr-rdp/password`.

## What it does

| Task | |
|---|---|
| `apt_forky` | deb822 sources for forky (+updates, security), no recommends/suggests, full upgrade when sources change |
| `base` | purges desktop tasks, GNOME, KDE and display managers if present; a few base tools |
| `memory` | zram (compute profile: **lz4, half of RAM**, priority 100, disk swap behind it) and Omarchy's reclaim sysctls with `swappiness=100` (` `page-cluster=0`, watermarks, `dirty_bytes`); earlyoom (never kills Hyprland/waybar/hypr-rdp, prefers browsers); journald/coredump limits |
| `tuning` | from linux-mint-optimizer: BBR + fq, Fast Open, bigger TCP buffers; root fs `noatime,commit=60`; GRUB `mitigations=off audit=0`; SSH root login with password (all switches in `group_data/all.py`) |
| `containers` | rootless podman (crun, overlay, netavark), `docker` / `docker compose` / `docker-compose` → podman / podman-compose (no daemon, no socket), docker.io short names, linger; containers get CPU weight 200 vs desktop/RDP/terminals 100 |
| `services` | disables cups/avahi/bluetooth/ModemManager/power-profiles if present; qemu-guest-agent |
| `desktop` | Hyprland 0.56 + uwsm, **hyprbars from Debian's `hyprland-plugin-hyprbars`** (version-locked to Hyprland, no hyprpm), waybar, mako, fuzzel, Terminator, JetBrains Mono, Adwaita cursor, PipeWire |
| `hypr_rdp` | builds **hypr-rdp 0.1.6 + the hypr-rdp-clearcodec patches** on the host (only when version/patches change), config, per-host password, session helpers, user units |
| `apps` | LibreOffice Calc (GTK3), Chromium + chromedriver (for MCP), git, **gh** (GitHub's apt repo), atop, Neovim + LazyVim tools (ripgrep, fd, fzf, lazygit, tree-sitter), Node.js + npm, xfce4-terminal |
| `user_tools` | for the user: **uv/uvx** (Astral installer), npm globals in `~/.local` + **pnpm**, **Aikido Safe Chain** (pinned installer, checksum-verified; wraps npm/npx/pnpm/pip/uv/uvx, 48 h minimum package age), **Omarchy's Neovim/LazyVim config** with the cream-blue theme |
| `shell` | Kali-style history: 100k entries, timestamps, shared live between terminals, prefix + Up/Down search; xfce4-terminal in cobalt with the **paste review dialog** (multi-line pastes open an editable window first) |
| `autologin` | tty1 autologin → `.profile` → `uwsm start hyprland.desktop` |
| `grub_password` | optional, see below |

### Same as the Omarchy VM

* **RDP:** ClearCodec (`hypr_rdp_codec`), 30 fps, compositor keymap. On
  connect the console output goes off, Hyprland's cursor is hidden except in
  resize zones, and off-screen windows are pulled back; the RDP size survives
  `hyprctl reload`.
* **Windows:** floating by default, snapping, drag-to-edge half/maximize
  (`aerosnap.lua`), macOS-style title bar buttons, Right Option = Super (de layout).
* **Look:** cream-blue-light for Hyprland, bar, notifications and launcher;
  Terminator cobalt (default) and navy profiles; `#3a3a3a` background.
* **Memory:** `MALLOC_ARENA_MAX=2`, `LP_NUM_THREADS=2`, no animations, blur or
  shadows. The background is Hyprland's own colour: no wallpaper process at all.

### Different on purpose

* waybar / mako / fuzzel instead of Omarchy's quickshell shell (much lighter).
* No lock screen or idle daemon (server VM, same as "stay awake").
* hyprbars comes from the Debian package instead of hyprpm.

## Keys

| Keys | |
|---|---|
| SUPER + Return | Terminator |
| SUPER + SHIFT + Return | xfce4-terminal (paste review) |
| SUPER + A / ☰ Apps | application menu (categories) |
| SUPER + Escape / Power | log out, reboot, shut down |
| SUPER + Space | launcher (search) |
| SUPER + W | close |
| SUPER + F / SUPER + ALT + F | fullscreen / maximize |
| SUPER + T | toggle floating/tiling (one window) |
| SUPER + L / ▦ in the bar | next layout mode |
| SUPER + M | show/hide minimized windows |
| right-click on the desktop | application menu at the cursor |
| SUPER + arrows, ALT + TAB | focus |
| SUPER + left / right drag | move / resize |
| SUPER + ß / ´ (+ SHIFT) | narrower / wider (shorter / taller) |
| SUPER + SHIFT + M | log out |

## GRUB password (optional)

```bash
GRUB_PASSWORD='secret' .venv/bin/pyinfra inventory.py tasks/grub_password.py
```

The PBKDF2 hash is computed locally, so only the hash reaches the host.
Normal boot needs no password; editing entries or opening the GRUB console
does (user `admin`, see `grub_superuser`).

## RDP password

Generated once per host: `ssh mc@HOST cat ~/.config/hypr-rdp/password`.

## Tuning from linux-mint-optimizer

Applied (switches in `group_data/all.py`): journald/coredump limits, qemu-guest-agent,
unneeded services off, network (BBR, fq, Fast Open, buffers), `noatime,commit=60`,
kernel `mitigations=off audit=0` (reboot needed), SSH root login with password.

Not applied, on purpose:

* **Huge pages / THP**: left at Debian defaults.
* **`swappiness=1`, dirty ratios, overcommit**: would undo the zram tuning.
* **tuned `virtual-guest`**: its sysctls (swappiness 30, dirty ratio 30) fight the
  zram settings, it switches THP to `always`, and it keeps a Python daemon
  (~25 MB) running. Its CPU-governor/energy parts do nothing in a guest.
* **irqbalance**: virtio devices use per-queue MSI-X interrupts that the kernel
  already spreads across the vCPUs (managed affinity, which irqbalance can't move).
* **I/O scheduler `mq-deadline`**: the virtual disk stays on `none`; the Proxmox
  host schedules the real disks. Enable "SSD emulation" + "Discard" on the VM disk instead.
* **`tcp_timestamps=0`, `randomize_va_space=1`, C-state limits, CPU governor**:
  no gain in a KVM guest, or a security cost.

## Compute profile

Tuned-like, automatic, no change to how jobs are started (`group_data/all.py`):

* **zram lz4, half of RAM, `swappiness=100`**: numeric data compresses poorly,
  so zstd's better ratio isn't worth its CPU cost; the disk swap partition
  catches overflow when agents need all the memory.
* **CPU weight**: rootless containers (user manager `user.slice`) get weight 200;
  Hyprland/hypr-rdp (`session.slice`) and terminals/agents (`app.slice`) 100.
  Only matters when the CPU is saturated; RDP stays usable, and the quant
  containers get ~2/3 of the CPU.
* Thread counts (`OPENBLAS_NUM_THREADS` etc.) are application settings: set them
  in the container/compose environment.

## Layout modes

`hypr-layout dynamic|golden-h|golden-v|golden-spiral|next` (SUPER + L, or ▦ in the bar):

| Mode | |
|---|---|
| `dynamic` (default) | floating; every app reopens where it was last closed (stored as fractions of the screen) |
| `golden-h` | master left 61.8 %, others stacked right |
| `golden-v` | master top 61.8 %, others stacked below |
| `golden-spiral` | each split 61.8 : 38.2, spiralling in |

When the RDP screen changes size, floating windows are scaled and moved with
it (and back when it grows again); tiled layouts adapt on their own.

## Title bar styles

`hypr-deco win311` (navy bar, ⊟ minimize / ⊠ close on the right) or `hypr-deco mac`
(cream bar, red/green on the left). Minimized windows: SUPER + M.
Initial style: `decorations_style` in `group_data/all.py`.

Window shadows: `hypr-shadow on|off` (off by default: without a GPU they are
drawn by the CPU). With `win311` a hard black drop shadow, otherwise a soft one.

## Themes for CLI tools

Omarchy's generated Cream Blue files, activated as Omarchy does: btop
(`color_theme = "cream-blue"`), Claude Code (`~/.claude/themes/omarchy.json`,
`theme = custom:omarchy`), Chromium frame colour (managed policy), Neovim (LazyVim, aether).

## Shell

* **grml-inspired bash** (`~/.config/bash/grml.bash`; grml's own config is zsh-only):
  prompt `user@host dir (git) $` with red exit code / red root, `cd` keeps a
  directory stack (`d`, `cd -2`), `..`/`...`, autocd, cd typo correction,
  `**` globs, grml aliases (`l la ll lh da j`) and functions (`mkcd cdt bk sll ssearch`),
  bash-completion.
* **Kali-style history**: 100k entries, timestamps, shared live between
  terminals, prefix + Up/Down search.
* **xfce4-terminal** (SUPER + SHIFT + Return): pasting text that contains a
  line break opens an editable review dialog first (Ctrl+Shift+V, right-click
  Paste or middle-click). Single-line pastes go straight in.
