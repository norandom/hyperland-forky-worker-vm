"""Away lock: while nobody is connected over RDP, sudo asks for the password, user processes
cannot reach the Little Snitch UI (no rule changes) and ptrace is restricted. See
files/sbin/hypr-away."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import apt, files, systemd

grace = host.data.get("away_grace_seconds", 600)

apt.packages(name="nftables (nft for the Little Snitch UI fence; no firewall service)",
             packages=["nftables"], no_recommends=True, _sudo=True)

files.put(name="hypr-away (root): lock while no RDP session", src="files/sbin/hypr-away",
          dest="/usr/local/sbin/hypr-away", user="root", group="root", mode="755", _sudo=True)

unit = files.put(
    name="hypr-away.service",
    src=StringIO(f"""# Managed by debian-hypr
[Unit]
Description=hypr-away: lock sudo, the Little Snitch UI and ptrace while nobody is connected over RDP
After=network-online.target littlesnitch.service

[Service]
Environment=AWAY_USER={host.data.desktop_user} GRACE={grace}
ExecStart=/usr/local/sbin/hypr-away
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""),
    dest="/etc/systemd/system/hypr-away.service", mode="644", _sudo=True)

systemd.service(name="hypr-away running", service="hypr-away.service", running=True, enabled=True,
                restarted=unit.changed, daemon_reload=unit.changed, _sudo=True)
