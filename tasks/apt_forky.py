"""Pin the host to Debian forky (testing), keep installs minimal, upgrade."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import apt, files

suite = host.data.debian_suite

sources = files.put(
    name=f"APT sources: Debian {suite} (deb822)",
    src=StringIO(f"""# Managed by debian-hypr
Types: deb
URIs: http://deb.debian.org/debian
Suites: {suite} {suite}-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: {suite}-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
"""),
    dest="/etc/apt/sources.list.d/debian.sources",
    mode="644",
    _sudo=True,
)

files.put(
    name="Retire the installer's one-line sources.list",
    src=StringIO("# Replaced by /etc/apt/sources.list.d/debian.sources (debian-hypr)\n"),
    dest="/etc/apt/sources.list",
    mode="644",
    _sudo=True,
)

files.put(
    name="Never install recommends/suggests (minimal footprint)",
    src=StringIO('APT::Install-Recommends "false";\nAPT::Install-Suggests "false";\n'),
    dest="/etc/apt/apt.conf.d/99debian-hypr-minimal",
    mode="644",
    _sudo=True,
)

apt.update(name="apt update", cache_time=3600, _sudo=True)

apt.dist_upgrade(
    name=f"Full upgrade to {suite}",
    _sudo=True,
    _if=sources.did_change,
)
