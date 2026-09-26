"""Applications (system packages, no recommends)."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import apt, files, server

apt.packages(
    name="Office, browser, tools",
    packages=[
        # LibreOffice Calc with the GTK3 (native Wayland) UI
        "libreoffice-calc", "libreoffice-gtk3", "fonts-crosextra-carlito",
        # Chromium for MCP (chrome-devtools / playwright MCP servers use it)
        "chromium", "chromium-driver",
        "git", "atop",
        # Neovim + what LazyVim expects
        "neovim", "ripgrep", "fd-find", "fzf", "lazygit", "tree-sitter-cli", "gcc", "make", "unzip",
        # Node.js + npm (user-level globals via ~/.npmrc prefix, see user_tools)
        "nodejs", "npm",
        # Second terminal: multi-line paste opens an editable review dialog
        "xfce4-terminal",
        # CLI: multitail, fzf helpers (bat previews, tree for directory previews)
        "multitail", "bat", "tree",
        # downloads: segmented HTTP/FTP/BitTorrent/metalink
        "aria2",
        # Image viewer (Xfce Ristretto) and a tabbed PDF viewer with annotations
        "ristretto", "qpdfview",
    ],
    no_recommends=True,
    _sudo=True,
)

# fd-find installs the binary as fdfind on Debian; LazyVim/snacks look for fd.
files.link(name="fd -> fdfind", path="/usr/local/bin/fd", target="/usr/bin/fdfind", _sudo=True)

# --- GitHub CLI from GitHub's apt repository (not packaged in forky) ------------------
keyring = "/etc/apt/keyrings/githubcli-archive-keyring.gpg"
server.shell(
    name="GitHub CLI apt key",
    commands=[f"[ -s {keyring} ] || (install -d -m 755 /etc/apt/keyrings && "
              f"curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o {keyring} && "
              f"chmod 644 {keyring})"],
    _sudo=True,
)
gh_repo = files.put(
    name="GitHub CLI apt source",
    src=StringIO(f"""# Managed by debian-hypr
Types: deb
URIs: https://cli.github.com/packages
Suites: stable
Components: main
Architectures: amd64
Signed-By: {keyring}
"""),
    dest="/etc/apt/sources.list.d/github-cli.sources",
    mode="644",
    _sudo=True,
)
apt.update(name="apt update (GitHub CLI repo)", _sudo=True, _if=gh_repo.did_change)
apt.packages(name="gh", packages=["gh"], no_recommends=True, _sudo=True)

# --- Little Snitch for Linux (network monitor/firewall, web UI on :3031) --------------
ls_ver = host.data.get("littlesnitch_version")
if ls_ver:
    deb = f"littlesnitch_{ls_ver}_amd64.deb"
    server.shell(
        name=f"Little Snitch {ls_ver} (checksum verified)",
        commands=[f"""[ "$(dpkg-query -W -f='${{Version}}' littlesnitch 2>/dev/null)" = "{ls_ver}" ] || (set -e
install -d -m 755 /var/cache/debian-hypr
curl -fsSL -o /var/cache/debian-hypr/{deb} https://obdev.at/downloads/littlesnitch-linux/{deb}
echo "{host.data.littlesnitch_sha256}  /var/cache/debian-hypr/{deb}" | sha256sum -c --quiet
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends /var/cache/debian-hypr/{deb})"""],
        _sudo=True,
    )
