"""Debian forky thin client: low-footprint Hyprland desktop over RDP (no GPU needed).

    uv run pyinfra inventory.py deploy.py               # everything
    uv run pyinfra inventory.py deploy.py --dry         # prepare only
    uv run pyinfra inventory.py tasks/hypr_rdp.py       # one area
"""
from pyinfra import local

for task in (
    "apt_forky",      # forky sources, no recommends, full upgrade
    "base",           # minimal packages, purge GNOME/KDE/display managers
    "memory",         # zram like Omarchy, sysctls, earlyoom, journald limits
    "tuning",         # Mint tuning: net/BBR, noatime, kernel cmdline, ssh (switches)
    "services",       # qemu-guest-agent, disable unneeded units
    "containers",     # rootless podman, docker/compose aliases
    "fonts",          # JetBrainsMono Nerd Font (icon glyphs, as on Omarchy)
    "desktop",        # Hyprland, hyprbars, waybar, mako, fuzzel, Terminator, theme
    "hypr_rdp",       # patched hypr-rdp built from source + session helpers
    "apps",           # Calc, Chromium, Vivaldi, Sublime, Typora, Obsidian, Meld, rclone, gh, Neovim, uutils
    "user_tools",     # uv, npm globals + pnpm, Aikido Safe Chain, nvim-simple
    "shell",          # Kali-style history, xfce4-terminal theme + paste dialog
    "themes",         # btop + Claude Code themes per Terminator profile; Chromium frame
    "away",           # away lock: no RDP session -> sudo password, Little Snitch UI closed
    "private",        # private data (private/ or private.tar.age): fonts, license keys
    "autologin",      # tty1 autologin -> uwsm -> Hyprland
):
    local.include(f"tasks/{task}.py")
