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
        # glyph fallback for emoji / symbols the Nerd Fonts lack (✅ ❌ ⚠ …)
        "fonts-noto-color-emoji", "fonts-symbola",
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
bar = [files.put(name="Config: ~/.config/waybar/style.css", src="files/waybar/style.css",
                 dest=f"{home}/.config/waybar/style.css", mode="644")]
for src, dest in (
    ("files/mako/config", ".config/mako/config"),
    ("files/fuzzel/fuzzel.ini", ".config/fuzzel/fuzzel.ini"),
    ("files/terminator/config", ".config/terminator/config"),
    ("files/terminator/plugins/theme_menu.py", ".config/terminator/plugins/theme_menu.py"),
    ("files/applications/littlesnitch.desktop", ".local/share/applications/littlesnitch.desktop"),
    ("files/applications/x3270.desktop", ".local/share/applications/x3270.desktop"),  # GUI, keypad
    ("files/applications/nedit.desktop", ".local/share/applications/nedit.desktop"),
    ("files/applications/foot-server.desktop", ".local/share/applications/foot-server.desktop"),  # hidden
    ("files/applications/footclient.desktop", ".local/share/applications/footclient.desktop"),  # hidden
    # Debian's terminator.desktop fails uwsm's validation (menu launch fails)
    ("files/applications/terminator.desktop", ".local/share/applications/terminator.desktop"),
    ("files/htop/htoprc", ".config/htop/htoprc"),
    ("files/gtk-3.0/gtk.css", ".config/gtk-3.0/gtk.css"),  # slim Terminator tabs
    # X resources: Windows 3.11 look for NEdit and xpdf (Xwayland has no xrdb)
    ("files/x11/Xdefaults", ".Xdefaults"),
    ("files/x11/x3270pro", ".x3270pro"),  # x3270: built-in keypad, key sizes
    ("files/ghostty/config.ghostty", ".config/ghostty/config.ghostty"),  # theme: hypr-termtheme
    ("files/foot/foot.ini", ".config/foot/foot.ini"),
):
    files.put(name=f"Config: ~/{dest}", src=src, dest=f"{home}/{dest}", mode="644")

bar.append(files.template(name=f"Config: ~/.config/waybar/config.jsonc (bar graphs {'on' if host.data.bar_graphs else 'off'})",
               src="templates/waybar/config.jsonc.j2", dest=f"{home}/.config/waybar/config.jsonc", mode="644"))

bar.append(files.put(name="Bar: hypr-launch (start apps via Hyprland, not as waybar children)", src="files/bin/hypr-launch",
          dest=f"{home}/.local/bin/hypr-launch", mode="755"))

bar.append(files.put(name="Bar: hypr-nightmode (night filter: off / green / dark)", src="files/bin/hypr-nightmode",
                     dest=f"{home}/.local/bin/hypr-nightmode", mode="755"))
for shader in ("night-green.glsl", "night-dark.glsl"):
    files.put(name=f"Night filter shader: {shader}", src=f"files/hypr/shaders/{shader}",
              dest=f"{home}/.config/hypr/shaders/{shader}", mode="644", create_remote_dir=True)

bar.append(files.put(name="Bar: hypr-cliphist (clipboard history: pick / wipe / status)", src="files/bin/hypr-cliphist",
                     dest=f"{home}/.local/bin/hypr-cliphist", mode="755"))

bar.append(files.put(name="Bar: hypr-agent-quota (Claude / Codex quota left)", src="files/bin/hypr-agent-quota",
          dest=f"{home}/.local/bin/hypr-agent-quota", mode="755"))

bar.append(files.put(name="Bar: hypr-sparkline (CPU / MEM / net with a history graph)", src="files/bin/hypr-sparkline",
          dest=f"{home}/.local/bin/hypr-sparkline", mode="755"))

# Only when the bar changed: a reload also kills whatever waybar itself started.
server.shell(
    name="Reload waybar (bar config changed)",
    commands=["systemctl --user is-active -q waybar.service && systemctl --user reload-or-restart waybar.service || true"],
    _if=any_changed(*bar),
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
                     ("hypr-termtheme", "Terminator theme switch"),
                     ("hypr-xfonts", "Fixedsys on the Xwayland font path")):
    files.put(
        name=f"Title bar button: {script} ({what})",
        src=f"files/bin/{script}",
        dest=f"{home}/.local/bin/{script}",
        mode="755",
    )

# Terminator with the chosen theme; system-wide so desktop entries find it on PATH.
files.put(name="hypr-term (Terminator with the chosen theme)", src="files/bin/hypr-term",
          dest="/usr/local/bin/hypr-term", mode="755", _sudo=True)
files.file(name="Remove old ~/.local/bin/hypr-term", path=f"{home}/.local/bin/hypr-term", present=False)

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

uutils_path = ('export PATH="/usr/lib/cargo/bin/coreutils:$PATH"\n'
               if host.data.uutils_coreutils else "")
files.put(
    name="Hyprland session env (llvmpipe threads, uutils in PATH)",
    src=StringIO(f"# Managed by debian-hypr\nexport LP_NUM_THREADS={host.data.llvmpipe_threads}\n{uutils_path}"),
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

# --- Clipboard bridge: X11 apps that offer text only as STRING (NEdit, Motif) ------------
files.put(name="hypr-clip-bridge (STRING-only X11 copies -> UTF-8 text)", src="files/bin/hypr-clip-bridge",
          dest=f"{home}/.local/bin/hypr-clip-bridge", mode="755")
bridge_unit = files.put(
    name="hypr-clip-bridge user service",
    src=StringIO("""# Managed by debian-hypr
[Unit]
Description=Clipboard bridge: STRING-only X11 copies (NEdit) -> UTF-8 text
PartOf=graphical-session.target
After=graphical-session.target

[Service]
ExecStart=%h/.local/bin/hypr-clip-bridge
Restart=on-failure
RestartSec=2

[Install]
WantedBy=graphical-session.target
"""),
    dest=f"{home}/.config/systemd/user/hypr-clip-bridge.service",
    mode="644",
)
server.shell(name="hypr-clip-bridge: systemd user daemon-reload", commands=["systemctl --user daemon-reload"],
             _if=bridge_unit.did_change)
server.shell(name="hypr-clip-bridge enabled and running",
             commands=["systemctl --user enable --now hypr-clip-bridge.service"])

# --- Clipboard history: cliphist in RAM, nightly wipe at 01:00 -----------------------------
ch_units = {
    "hypr-cliphist.service": """[Unit]
Description=Clipboard history recorder (cliphist, in RAM)
PartOf=graphical-session.target
After=graphical-session.target

[Service]
ExecStart=%h/.local/bin/hypr-cliphist watch
Restart=on-failure
RestartSec=2

[Install]
WantedBy=graphical-session.target
""",
    "hypr-cliphist-wipe.service": """[Unit]
Description=Wipe the clipboard history and the current clipboard

[Service]
Type=oneshot
ExecStart=%h/.local/bin/hypr-cliphist wipe --quiet
""",
    "hypr-cliphist-wipe.timer": """[Unit]
Description=Wipe the clipboard history every night at 01:00

[Timer]
OnCalendar=*-*-* 01:00
Persistent=true

[Install]
WantedBy=timers.target
""",
}
ch_ops = [files.put(name=f"Clipboard history unit: {u}", src=StringIO("# Managed by debian-hypr\n" + body),
                    dest=f"{home}/.config/systemd/user/{u}", mode="644") for u, body in ch_units.items()]
server.shell(name="Clipboard history: systemd user daemon-reload", commands=["systemctl --user daemon-reload"],
             _if=any_changed(*ch_ops))
server.shell(name="Clipboard history recorder + nightly wipe enabled",
             commands=["systemctl --user enable --now hypr-cliphist.service hypr-cliphist-wipe.timer"])
