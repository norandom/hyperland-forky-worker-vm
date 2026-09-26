"""Boot straight into Hyprland: tty1 autologin -> login shell -> uwsm -> Hyprland.
No display manager (nothing GNOME/KDE-ish, minimal footprint)."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import files, server

user = host.data.desktop_user
home = host.data.desktop_home

getty = files.put(
    name=f"tty1 autologin for {user}",
    src=StringIO(f"""# Managed by debian-hypr
[Service]
ExecStart=
ExecStart=-/sbin/agetty -o '-p -f -- \\\\u' --noclear --autologin {user} %I $TERM
"""),
    dest="/etc/systemd/system/getty@tty1.service.d/autologin.conf",
    mode="644",
    _sudo=True,
)
server.shell(name="systemd daemon-reload", commands=["systemctl daemon-reload"],
             _sudo=True, _if=getty.did_change)

files.block(
    name="Start Hyprland (via uwsm) on tty1 login",
    path=f"{home}/.profile",
    marker="# {mark} debian-hypr: Hyprland on tty1",
    content=(
        'if [ -z "${WAYLAND_DISPLAY:-}" ] && [ "${XDG_VTNR:-0}" -eq 1 ] && uwsm check may-start >/dev/null 2>&1; then\n'
        "    exec uwsm start -- hyprland.desktop\n"
        "fi"
    ),
    try_prevent_shell_expansion=True,
)
