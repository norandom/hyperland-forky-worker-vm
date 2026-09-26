"""Minimal base: purge full desktops, install the few tools we need."""
from pyinfra.operations import apt

apt.packages(
    name="No GNOME / KDE / other desktops or display managers",
    packages=[
        "task-desktop", "task-gnome-desktop", "task-kde-desktop", "task-xfce-desktop",
        "task-lxqt-desktop", "task-cinnamon-desktop", "task-mate-desktop",
        "gnome-core", "gnome-shell", "plasma-desktop", "plasma-workspace",
        "gdm3", "sddm", "lightdm",
    ],
    present=False,
    purge=True,
    _sudo=True,
)

apt.packages(
    name="Base tools",
    packages=[
        "sudo", "curl", "ca-certificates", "git", "jq", "unzip", "htop", "btop",
        "dbus-user-session", "systemd-zram-generator", "earlyoom", "qemu-guest-agent",
    ],
    no_recommends=True,
    _sudo=True,
)
