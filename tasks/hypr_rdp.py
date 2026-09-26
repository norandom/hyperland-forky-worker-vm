"""hypr-rdp 1:1 with the Omarchy VM: same source, same 3 patches, same config,
same session helpers (console off, cursor hidden, window rescue, size memory)."""
import hashlib
from pathlib import Path

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server

home = host.data.desktop_home
user = host.data.desktop_user
ver = host.data.hypr_rdp_version
stamp = "/usr/local/share/hypr-rdp/BUILD"
src_dir = f"{home}/.cache/hypr-rdp-src"

apt.packages(
    name="hypr-rdp build + runtime deps",
    packages=[
        "cargo", "rustc", "clang", "libclang-dev", "cmake", "pkg-config", "make", "patch",
        "libva-dev", "libpipewire-0.3-dev", "libxkbcommon-dev", "libwayland-dev",
        "libgbm-dev", "libfuse3-dev", "libpulse-dev", "libssl-dev",
        "jq", "fuse3", "pulseaudio-utils",
    ],
    no_recommends=True,
    _sudo=True,
)

# --- Build only when the version or the patches change ------------------------------
patches = sorted(Path("files/hypr-rdp").glob("*.patch"))
want = f"{ver} " + hashlib.sha256(b"".join(p.read_bytes() for p in patches)).hexdigest()
have = (host.get_fact(Command, command=f"cat {stamp} 2>/dev/null || true") or "").strip()

for f in [*patches, Path("files/hypr-rdp/build.sh"), Path("files/hypr-rdp/hypr-rdp-cursor")]:
    files.put(name=f"Build input: {f.name}", src=str(f), dest=f"{src_dir}/{f.name}", mode="755")

if have != want:
    server.shell(
        name=f"Build + install hypr-rdp {ver} with patches (~15 min)",
        commands=[f"{src_dir}/build.sh {ver} {host.data.hypr_rdp_sha256} {stamp}"],
    )

# --- Config, password, helpers ------------------------------------------------------
server.shell(
    name="RDP password (generated once per host, never in the repo)",
    commands=[
        f"mkdir -p {home}/.config/hypr-rdp && "
        f"[ -s {home}/.config/hypr-rdp/password ] || "
        f"(umask 077; head -c 18 /dev/urandom | base64 | tr -d '/+=' > {home}/.config/hypr-rdp/password)"
    ],
)

cfg = files.template(
    name="hypr-rdp config",
    src="templates/hypr-rdp/config.toml.j2",
    dest=f"{home}/.config/hypr-rdp/config.toml",
    mode="600",
)

scripts = [
    files.put(name=f"Helper: {name}", src=f"files/hypr-rdp/{name}",
              dest=f"{home}/.local/bin/{name}", mode="755")
    for name in ("hypr-rdp-session", "hypr-rdp-sessionwatch", "hypr-rdp-modecache")
]

units = [
    files.put(name=f"User unit: {name}", src=f"files/hypr-rdp/{name}",
              dest=f"{home}/.config/systemd/user/{name}", mode="644")
    for name in ("hypr-rdp.service", "hypr-rdp-sessionwatch.service", "hypr-rdp-modecache.service")
]

# Enable = WantedBy symlinks (works before the user manager ever ran).
for name in ("hypr-rdp.service", "hypr-rdp-sessionwatch.service", "hypr-rdp-modecache.service"):
    files.link(
        name=f"Enable {name}",
        path=f"{home}/.config/systemd/user/graphical-session.target.wants/{name}",
        target=f"{home}/.config/systemd/user/{name}",
    )

# hypr-rdp-sessionwatch reads hypr-rdp's log via journalctl --user.
server.shell(
    name=f"{user} may read the journal",
    commands=[f"id -nG {user} | grep -qw systemd-journal || usermod -aG systemd-journal {user}"],
    _sudo=True,
)

# Apply changes to a running session (restarting hypr-rdp drops an RDP client).
server.shell(
    name="Restart hypr-rdp (running session only)",
    commands=[
        "systemctl --user daemon-reload 2>/dev/null || true",
        "systemctl --user is-active -q graphical-session.target 2>/dev/null && "
        "systemctl --user restart hypr-rdp.service hypr-rdp-sessionwatch.service hypr-rdp-modecache.service || true",
    ],
    _if=lambda: cfg.did_change() or any(op.did_change() for op in scripts + units) or have != want,
)
