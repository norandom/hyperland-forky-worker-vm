"""Hosts to deploy to (SSH key login + passwordless sudo expected).

    TARGET_HOSTS=10.0.0.62,10.0.0.63 TARGET_USER=alice uv run pyinfra inventory.py deploy.py

The SSH user is also the desktop user (tty1 autologin, Hyprland, hypr-rdp).
For your own fixed hosts, copy this file to inventory.local.py (git-ignored)
and edit HOSTS / USER there.
"""
import os

USER = os.environ.get("TARGET_USER", "debian")
HOSTS = [h for h in os.environ.get("TARGET_HOSTS", "").split(",") if h] or ["thin-client.example.lan"]

hosts = [
    (h, {"ssh_user": USER, "desktop_user": USER, "desktop_home": f"/home/{USER}"})
    for h in HOSTS
]
