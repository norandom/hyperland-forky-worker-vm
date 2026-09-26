"""Debian forky + Hyprland desktop for RDP, without Omarchy.

    .venv/bin/pyinfra inventory.py deploy.py            # everything
    .venv/bin/pyinfra inventory.py deploy.py --dry      # show changes only
    .venv/bin/pyinfra inventory.py tasks/hypr_rdp.py    # one area
"""
from pyinfra import local

for task in (
    "apt_forky",      # forky sources, no recommends, full upgrade
    "base",           # minimal packages, purge GNOME/KDE/display managers
    "memory",         # zram like Omarchy, sysctls, earlyoom, journald limits
    "tuning",         # Mint tuning: net/BBR, noatime, kernel cmdline, ssh (switches)
    "services",       # qemu-guest-agent, disable unneeded units
    "containers",     # rootless podman, docker/compose aliases
    "desktop",        # Hyprland, hyprbars, waybar, mako, fuzzel, Terminator, theme
    "hypr_rdp",       # patched hypr-rdp built from source + session helpers
    "apps",           # Calc, Chromium (MCP), gh, atop, Neovim, Node, xfce4-terminal
    "user_tools",     # uv, npm globals + pnpm, Aikido Safe Chain, Omarchy nvim config
    "shell",          # Kali-style history, xfce4-terminal theme + paste dialog
    "themes",         # Omarchy theme files: btop, Claude Code, Chromium
    "autologin",      # tty1 autologin -> uwsm -> Hyprland
    "grub_password",  # optional (GRUB_PASSWORD env var)
):
    local.include(f"tasks/{task}.py")
