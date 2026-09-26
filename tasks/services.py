"""Guest agent on; unneeded units off (only if present)."""
from pyinfra import host
from pyinfra.operations import server

units = " ".join(host.data.disabled_units)
server.shell(
    name="Stop + disable unneeded units that exist",
    commands=[f"""for u in {units}; do
  systemctl cat "$u" >/dev/null 2>&1 || continue
  systemctl disable --now "$u" >/dev/null 2>&1 || true
done"""],
    _sudo=True,
)

# qemu-guest-agent is started by udev once Proxmox exposes the virtio port
# (VM Options -> QEMU Guest Agent: Enabled, then a full stop/start).
server.shell(
    name="Start qemu-guest-agent if the virtio port exists",
    commands=["[ -e /dev/virtio-ports/org.qemu.guest_agent.0 ] && systemctl start qemu-guest-agent || true"],
    _sudo=True,
)
