"""Rootless, daemonless podman with docker / docker compose / docker-compose aliases."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import apt, files, server

user = host.data.desktop_user

if host.data.containers:
    apt.packages(
        name="podman (rootless) + docker CLI alias + podman-compose",
        packages=[
            "podman", "podman-docker", "podman-compose", "crun", "passt", "uidmap",
            "netavark", "aardvark-dns", "catatonit", "containers-storage",
        ],
        no_recommends=True,
        _sudo=True,
    )

    files.put(name="Silence podman-docker's 'emulate Docker CLI' notice",
              src=StringIO(""), dest="/etc/containers/nodocker", mode="644", _sudo=True)

    files.put(
        name="Short image names resolve to docker.io (like Docker)",
        src=StringIO('# Managed by debian-hypr\nunqualified-search-registries = ["docker.io"]\n'
                     'short-name-mode = "permissive"\n'),
        dest="/etc/containers/registries.conf.d/50-debian-hypr.conf",
        mode="644",
        _sudo=True,
    )

    files.put(
        name="`docker compose` / `podman compose` use podman-compose (no daemon, no socket)",
        src=StringIO('# Managed by debian-hypr\n[engine]\ncompose_providers = ["podman-compose"]\n'
                     "compose_warning_logs = false\n"),
        dest="/etc/containers/containers.conf.d/50-debian-hypr.conf",
        mode="644",
        _sudo=True,
    )

    files.link(
        name="docker-compose -> podman-compose",
        path="/usr/local/bin/docker-compose",
        target="/usr/bin/podman-compose",
        _sudo=True,
    )

    server.shell(
        name=f"Linger for {user}: containers run independent of the login session",
        commands=[f"[ -e /var/lib/systemd/linger/{user} ] || loginctl enable-linger {user}"],
        _sudo=True,
    )

    # CPU priority: rootless containers live in the user manager's user.slice;
    # Hyprland/hypr-rdp in session.slice, terminals/agents in app.slice (weight 100).
    weight = files.put(
        name=f"Containers get CPU weight {host.data.container_cpu_weight} (desktop/RDP/terminals: 100)",
        src=StringIO(f"# Managed by debian-hypr\n[Slice]\nCPUWeight={host.data.container_cpu_weight}\n"),
        dest=f"{host.data.desktop_home}/.config/systemd/user/user.slice.d/50-debian-hypr-cpu.conf",
        mode="644",
    )
    server.shell(
        name="Apply CPU weight (user manager reload)",
        commands=["systemctl --user daemon-reload"],
        _if=weight.did_change,
    )

    # podman-tui talks to the API socket; socket-activated, so the podman
    # service only runs while a client (podman-tui) is connected.
    server.shell(
        name="podman.socket (user, for podman-tui)",
        commands=["systemctl --user is-enabled -q podman.socket || systemctl --user enable --now podman.socket"],
    )
