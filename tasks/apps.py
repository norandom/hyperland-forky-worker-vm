"""Applications (system packages, no recommends; vendor apt repos for gh, Sublime Text,
Typora, Vivaldi; Obsidian .deb)."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import apt, files, server

apt.packages(
    name="Office, browser, tools",
    packages=[
        # LibreOffice Calc + Writer with the GTK3 (native Wayland) UI; UI in English
        # (built in) or German; spelling, hyphenation, thesaurus for de + en-US
        "libreoffice-calc", "libreoffice-writer", "libreoffice-gtk3", "fonts-crosextra-carlito",
        "libreoffice-l10n-de", "hunspell-de-de", "hunspell-en-us", "hyphen-de", "hyphen-en-us",
        "mythes-de", "mythes-en-us",
        # Chromium for MCP (chrome-devtools / playwright MCP servers use it)
        "chromium", "chromium-driver",
        "git", "atop",
        # Neovim (nvim-simple config, see user_tools) + search/dev tools
        "neovim", "ripgrep", "fd-find", "fzf", "lazygit", "gcc", "make", "unzip",
        # Rust coreutils (uutils); first in PATH for the user's shells + session (shell task)
        "rust-coreutils",
        # Node.js + npm (user-level globals via ~/.npmrc prefix, see user_tools)
        "nodejs", "npm",
        # Second terminal: multi-line paste opens an editable review dialog
        "xfce4-terminal",
        # CLI: multitail, fzf helpers (bat previews, tree for directory previews)
        "multitail", "bat", "tree",
        # downloads: segmented HTTP/FTP/BitTorrent/metalink; sync (rclone: release_tools)
        "aria2", "rsync",
        # graphical diff/merge for files and folders (like WinDiff)
        "meld",
        # TUIs: markdown viewer, HTTP client, network path, disk usage
        "glow", "posting", "trippy", "gdu",
        # Image viewer (Xfce Ristretto) and a tabbed PDF viewer with annotations
        "ristretto", "qpdfview",
    ],
    no_recommends=True,
    _sudo=True,
)

# fd-find installs the binary as fdfind on Debian; tools look for fd.
files.link(name="fd -> fdfind", path="/usr/local/bin/fd", target="/usr/bin/fdfind", _sudo=True)

# --- Vendor apt repositories (key from the vendor, deb822 source pinned to it) -------------
def vendor_repo(name, key_url, key_ext, uri, suite, components="", keyring=None):
    keyring = keyring or f"/etc/apt/keyrings/{name}.{key_ext}"
    server.shell(
        name=f"{name}: apt key",
        commands=[f"[ -s {keyring} ] || (install -d -m 755 /etc/apt/keyrings && "
                  f"curl -fsSL {key_url} -o {keyring} && chmod 644 {keyring})"],
        _sudo=True,
    )
    comp = f"Components: {components}\n" if components else ""
    repo = files.put(
        name=f"{name}: apt source",
        src=StringIO(f"# Managed by debian-hypr\nTypes: deb\nURIs: {uri}\nSuites: {suite}\n{comp}"
                     f"Architectures: amd64\nSigned-By: {keyring}\n"),
        dest=f"/etc/apt/sources.list.d/{name}.sources",
        mode="644",
        _sudo=True,
    )
    apt.update(name=f"apt update ({name} repo)", _sudo=True, _if=repo.did_change)


vendor_repo("github-cli", "https://cli.github.com/packages/githubcli-archive-keyring.gpg", "gpg",
            "https://cli.github.com/packages", "stable", "main",
            keyring="/etc/apt/keyrings/githubcli-archive-keyring.gpg")
apt.packages(name="gh", packages=["gh"], no_recommends=True, _sudo=True)

# Sublime Text 4 (`subl`); the license file comes from the private data (tasks/private.py).
vendor_repo("sublime-text", "https://download.sublimetext.com/sublimehq-pub.gpg", "asc",
            "https://download.sublimetext.com/", "apt/stable/")
apt.packages(name="Sublime Text (subl)", packages=["sublime-text"], no_recommends=True, _sudo=True)

# Typora (Markdown editor); activate with the key from hypr-licenses (Help > My License).
vendor_repo("typora", "https://downloads.typora.io/typora.gpg", "gpg", "https://downloads.typora.io/linux", "./")
apt.packages(name="Typora", packages=["typora"], no_recommends=True, _sudo=True)

# Vivaldi: its postinst would add a second (legacy) apt source; /etc/default/vivaldi stops that.
files.put(name="Vivaldi: don't add its own apt source",
          src=StringIO('repo_add_once="false"\nrepo_reenable_on_distupgrade="false"\n'),
          dest="/etc/default/vivaldi", mode="644", _sudo=True)
vendor_repo("vivaldi", "https://repo.vivaldi.com/archive/linux_signing_key.pub", "asc",
            "https://repo.vivaldi.com/archive/deb/", "stable", "main")
apt.packages(name="Vivaldi", packages=["vivaldi-stable"], no_recommends=True, _sudo=True)

# Obsidian: .deb from GitHub releases (pinned, checksum verified)
obs_ver, obs_sha = host.data.obsidian_version, host.data.obsidian_sha256
obs_deb = f"obsidian_{obs_ver}_amd64.deb"
server.shell(
    name=f"Obsidian {obs_ver} (checksum verified)",
    commands=[f"""[ "$(dpkg-query -W -f='${{Version}}' obsidian 2>/dev/null)" = "{obs_ver}" ] || (set -e
install -d -m 755 /var/cache/debian-hypr
curl -fsSL -o /var/cache/debian-hypr/{obs_deb} https://github.com/obsidianmd/obsidian-releases/releases/download/v{obs_ver}/{obs_deb}
echo "{obs_sha}  /var/cache/debian-hypr/{obs_deb}" | sha256sum -c --quiet
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends /var/cache/debian-hypr/{obs_deb})"""],
    _sudo=True,
)

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

# --- Single-binary tools from GitHub releases (pinned, checksum verified) -------------
for name, (url, sha) in host.data.release_tools.items():
    archive = url.rsplit("/", 1)[1]
    server.shell(
        name=f"{name} ({archive}, checksum verified)",
        commands=[f"""[ "$(cat /usr/local/share/debian-hypr/{name}.sha256 2>/dev/null)" = "{sha}" ] || (set -e
t=$(mktemp -d)
curl -fsSL -o "$t/{archive}" {url}
echo "{sha}  $t/{archive}" | sha256sum -c --quiet
mkdir "$t/x"
case {archive} in *.zip) unzip -q "$t/{archive}" -d "$t/x" ;; *) tar -xf "$t/{archive}" -C "$t/x" ;; esac
install -m 755 "$(find "$t/x" -type f -name {name} | head -1)" /usr/local/bin/{name}
install -d /usr/local/share/debian-hypr; echo "{sha}" > /usr/local/share/debian-hypr/{name}.sha256
rm -rf "$t")"""],
        _sudo=True,
    )
