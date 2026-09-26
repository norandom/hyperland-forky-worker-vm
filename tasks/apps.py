"""Applications (system packages, no recommends)."""
from io import StringIO

from pyinfra.operations import apt, files, server

apt.packages(
    name="Office, browser, tools",
    packages=[
        # LibreOffice Calc with the GTK3 (native Wayland) UI
        "libreoffice-calc", "libreoffice-gtk3", "fonts-crosextra-carlito",
        # Chromium for MCP (chrome-devtools / playwright MCP servers use it)
        "chromium", "chromium-driver",
        "git", "atop",
        # free ICC profiles, incl. Adobe RGB (1998) compatible (see rdp_icc_profile)
        "icc-profiles-free",
        # Neovim + what LazyVim expects
        "neovim", "ripgrep", "fd-find", "fzf", "lazygit", "tree-sitter-cli", "gcc", "make", "unzip",
        # Node.js + npm (user-level globals via ~/.npmrc prefix, see user_tools)
        "nodejs", "npm",
        # Second terminal: multi-line paste opens an editable review dialog
        "xfce4-terminal",
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
