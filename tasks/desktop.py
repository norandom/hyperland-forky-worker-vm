"""Hyprland desktop without Omarchy: packages, config, theme, fonts, Terminator."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import apt, files, server
from pyinfra.operations.util import any_changed

home = host.data.desktop_home

apt.packages(
    name="Hyprland + minimal desktop (no recommends)",
    packages=[
        # compositor, session, title bars, portals
        "hyprland", "hyprland-plugin-hyprbars", "hyprland-guiutils", "uwsm",
        "xdg-desktop-portal-hyprland", "xdg-desktop-portal-gtk", "xwayland",
        # software rendering (no GPU in the VM)
        "libgl1-mesa-dri", "libegl-mesa0",
        # bar, notifications, launcher, terminal
        "waybar", "mako-notifier", "fuzzel", "terminator",
        # file manager: Xfe (FOX toolkit, few dependencies, tree + file list)
        "xfe",
        # fonts, cursor/icons
        "fonts-jetbrains-mono", "fonts-dejavu-core", "adwaita-icon-theme",
        # audio (hypr-rdp redirects sound to the RDP client via pactl)
        "pipewire", "pipewire-pulse", "wireplumber", "pulseaudio-utils",
        # clipboard + RDP file transfer
        "wl-clipboard", "fuse3",
    ],
    no_recommends=True,
    _sudo=True,
)

server.shell(
    name=f"Title bar style (set once to {host.data.decorations_style}; switch with hypr-deco)",
    commands=[f"[ -s {home}/.config/hypr/decorations-style ] || echo {host.data.decorations_style} > {home}/.config/hypr/decorations-style"],
)

server.shell(
    name=f"Window shadows (set once to {host.data.window_shadows}; switch with hypr-shadow)",
    commands=[f"[ -s {home}/.config/hypr/window-shadows ] || echo {host.data.window_shadows} > {home}/.config/hypr/window-shadows"],
)

server.shell(
    name="Layout mode (set once to dynamic; switch with SUPER+L / hypr-layout)",
    commands=[f"[ -s {home}/.config/hypr/layout-mode ] || echo dynamic > {home}/.config/hypr/layout-mode"],
)

# --- Hyprland config -----------------------------------------------------------
hypr = [
    files.put(
        name=f"Hyprland: {name}",
        src=f"files/hypr/{name}",
        dest=f"{home}/.config/hypr/{name}",
        mode="644",
    )
    for name in (
        "hyprland.lua", "looknfeel.lua", "layouts.lua", "bindings.lua",
        "autostart.lua", "decorations.lua", "aerosnap.lua", "cursorzone.lua",
    )
]
hypr.append(files.template(
    name=f"Hyprland: monitors.lua (RDP output at {host.data.rdp_refresh_hz} Hz)",
    src="templates/hypr/monitors.lua.j2",
    dest=f"{home}/.config/hypr/monitors.lua",
    mode="644",
))
hypr.append(files.template(
    name="Hyprland: input.lua (keyboard layout)",
    src="templates/hypr/input.lua.j2",
    dest=f"{home}/.config/hypr/input.lua",
    mode="644",
))

server.shell(
    name="Reload running Hyprland",
    commands=[
        'sig=$(ls -t "/run/user/$(id -u)/hypr" 2>/dev/null | head -1); '
        '[ -n "$sig" ] && HYPRLAND_INSTANCE_SIGNATURE=$sig hyprctl reload >/dev/null || true'
    ],
    _if=any_changed(*hypr),
)

# A changed keymap drops hypr-rdp's virtual keyboard (RDP input dies until
# hypr-rdp restarts; a connected client reconnects once). Layout switches
# (hypr-kbd) don't change the keymap and need no restart.
server.shell(
    name="Restart hypr-rdp (keyboard config changed)",
    commands=["sleep 1; systemctl --user -q is-active hypr-rdp && systemctl --user restart hypr-rdp || true"],
    _if=hypr[-1].did_change,
)

files.put(
    name="Power button icon (red square, cream Debian swirl)",
    src="files/waybar/power.png",
    dest="/usr/local/share/debian-hypr/power.png",
    mode="644",
    _sudo=True,
)

files.template(
    name="GTK 3 settings (theme, cursor, font rendering)",
    src="templates/gtk-3.0/settings.ini.j2",
    dest=f"{home}/.config/gtk-3.0/settings.ini",
    mode="644",
)

# --- Bar, notifications, launcher, GTK, terminal, top tools ----------------------
for src, dest in (
    ("files/waybar/config.jsonc", ".config/waybar/config.jsonc"),
    ("files/waybar/style.css", ".config/waybar/style.css"),
    ("files/mako/config", ".config/mako/config"),
    ("files/fuzzel/fuzzel.ini", ".config/fuzzel/fuzzel.ini"),
    ("files/terminator/config", ".config/terminator/config"),
    ("files/terminator/plugins/theme_menu.py", ".config/terminator/plugins/theme_menu.py"),
    ("files/littlesnitch.desktop", ".local/share/applications/littlesnitch.desktop"),
    ("files/htop/htoprc", ".config/htop/htoprc"),
    ("files/gtk-3.0/gtk.css", ".config/gtk-3.0/gtk.css"),  # slim Terminator tabs
):
    files.put(name=f"Config: ~/{dest}", src=src, dest=f"{home}/{dest}", mode="644")

server.shell(
    name="Reload waybar (picks up config changes)",
    commands=["systemctl --user is-active -q waybar.service && systemctl --user reload-or-restart waybar.service || true"],
)

# btop writes its full config on first start; only enforce the sort order.
server.shell(
    name="btop sorts by memory",
    commands=[
        f'f={home}/.config/btop/btop.conf; mkdir -p "$(dirname "$f")"; '
        '[ -f "$f" ] || cp /dev/null "$f"; '
        'grep -q "^proc_sorting" "$f" && sed -i \'s/^proc_sorting = .*/proc_sorting = "memory"/\' "$f" '
        '|| echo \'proc_sorting = "memory"\' >> "$f"'
    ],
)

files.put(
    name="XFCE-style app menu (waybar button, SUPER+A) + power menu",
    src="files/bin/hypr-appmenu",
    dest=f"{home}/.local/bin/hypr-appmenu",
    mode="755",
)


files.put(
    name="Layout switcher: hypr-layout dynamic|golden-h|golden-v|golden-spiral|next",
    src="files/bin/hypr-layout",
    dest=f"{home}/.local/bin/hypr-layout",
    mode="755",
)

for script, what in (("hypr-glass", "glass window on|off"), ("hypr-pin", "stay on top on|off"),
                     ("hypr-termtheme", "Terminator theme switch"), ("hypr-term", "Terminator with that theme")):
    files.put(
        name=f"Title bar button: {script} ({what})",
        src=f"files/bin/{script}",
        dest=f"{home}/.local/bin/{script}",
        mode="755",
    )

# Xfe: Windows 3.11 File Manager look (grey, navy selection), folder tree + list.
# Seeded once; Xfe rewrites the file with the user's own changes afterwards.
files.put(
    name="Xfe seed config",
    src="files/xfe/xferc",
    dest="/usr/local/share/debian-hypr/xferc",
    mode="644",
    create_remote_dir=True,
    _sudo=True,
)
server.shell(
    name="Xfe: Windows 3.11 colours (once)",
    commands=[f"mkdir -p {home}/.config/xfe && (grep -q '^basecolor' {home}/.config/xfe/xferc 2>/dev/null "
              f"|| cp /usr/local/share/debian-hypr/xferc {home}/.config/xfe/xferc)"],
)

files.put(
    name="Window shadow switch: hypr-shadow on|off",
    src="files/bin/hypr-shadow",
    dest=f"{home}/.local/bin/hypr-shadow",
    mode="755",
)

files.put(
    name="Keyboard layout switcher: hypr-kbd us|de (aliases kbus, kbde)",
    src="files/bin/hypr-kbd",
    dest=f"{home}/.local/bin/hypr-kbd",
    mode="755",
)

files.put(
    name="Title bar style switcher: hypr-deco win311|mac",
    src="files/bin/hypr-deco",
    dest=f"{home}/.local/bin/hypr-deco",
    mode="755",
)

files.put(
    name="Hyprland session env (llvmpipe threads)",
    src=StringIO(f"# Managed by debian-hypr\nexport LP_NUM_THREADS={host.data.llvmpipe_threads}\n"),
    dest=f"{home}/.config/uwsm/env-hyprland",
    mode="644",
)

# Terminator as the default for xdg-terminal-exec style launchers.
files.put(
    name="Default terminal: Terminator",
    src="files/xdg-terminals.list",
    dest=f"{home}/.config/xdg-terminals.list",
    mode="644",
)
