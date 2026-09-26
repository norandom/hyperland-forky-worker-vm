"""Memory like Omarchy: zram swap + reclaim sysctls; earlyoom; journald limits."""
from io import StringIO
from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server, systemd

zram = files.put(
    name=f"zram swap: {host.data.zram_size}, {host.data.zram_algorithm}, priority 100",
    src=StringIO(f"""# Managed by debian-hypr (compute profile, see group_data/all.py)
[zram0]
zram-size = {host.data.zram_size}
compression-algorithm = {host.data.zram_algorithm}
swap-priority = 100
"""),
    dest="/etc/systemd/zram-generator.conf",
    mode="644",
    _sudo=True,
)
server.shell(
    name="Recreate zram now (swapoff/on, safe while it holds little)",
    commands=["systemctl daemon-reload", "systemctl restart systemd-zram-setup@zram0.service"],
    _sudo=True,
    _if=zram.did_change,
)

sysctl = files.put(
    name=f"Reclaim sysctls (Omarchy's set, swappiness={host.data.vm_swappiness})",
    src=StringIO(Path("files/system/99-memory.conf").read_text().replace(
        "vm.swappiness=150", f"vm.swappiness={host.data.vm_swappiness}")),
    dest="/etc/sysctl.d/99-debian-hypr-memory.conf",
    mode="644",
    _sudo=True,
)
server.shell(name="Apply sysctls", commands=["sysctl --system"], _sudo=True, _if=sysctl.did_change)

eo = files.put(
    name="earlyoom: never kill the desktop/RDP stack, prefer browsers",
    src="files/system/earlyoom",
    dest="/etc/default/earlyoom",
    mode="644",
    _sudo=True,
)
systemd.service(name="earlyoom enabled", service="earlyoom", running=True, enabled=True, _sudo=True)
systemd.service(name="Restart earlyoom", service="earlyoom", restarted=True, _sudo=True,
                _if=eo.did_change)

jd = files.put(
    name="journald size limits",
    src="files/system/journald.conf",
    dest="/etc/systemd/journald.conf.d/50-debian-hypr.conf",
    mode="644",
    _sudo=True,
)
files.put(
    name="coredump size limits",
    src="files/system/coredump.conf",
    dest="/etc/systemd/coredump.conf.d/50-debian-hypr.conf",
    mode="644",
    _sudo=True,
)
systemd.service(name="Restart journald", service="systemd-journald", restarted=True,
                _sudo=True, _if=jd.did_change)
