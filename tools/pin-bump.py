#!/usr/bin/env python3
"""Bump the pins that tools/pin-check.py reports as outdated: new version + new sha256.

    tools/pin-bump.py              # every outdated pin it knows how to bump
    tools/pin-bump.py NAME ...     # only these (names as pin-check prints them)
    tools/pin-bump.py --dry-run    # show what would change, write nothing

Edits group_data/all.py in place. The sha256 always comes from upstream: GitHub's asset digest
for release downloads, the vendor's own metadata for VS Code and Positron (never a hash of a
file we just fetched over the same channel, unless upstream publishes none). Pins it can't bump
safely (patched or self-built ones, other naming schemes) are listed for a manual change.
Afterwards: deploy (the tasks reinstall on a version/sha change), check, commit.
Exit 0: bumped or nothing to do, 1: manual pins left.
"""
import importlib.util
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALL = ROOT / "group_data/all.py"
spec = importlib.util.spec_from_file_location("pin_check", ROOT / "tools/pin-check.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

GH_URL = re.compile(r"https://github\.com/([^/]+/[^/]+)/releases/download/([^/]+)/([^/\"]+)")


def gh_digest(repo, tag, asset):
    """sha256 of a release asset as GitHub reports it."""
    for a in pc.gh(f"repos/{repo}/releases/tags/{tag}")["assets"]:
        if a["name"] == asset:
            if (a.get("digest") or "").startswith("sha256:"):
                return a["digest"].split(":", 1)[1]
            raise LookupError(f"{repo} {tag}: {asset} has no digest")
    raise LookupError(f"{repo} {tag}: no asset {asset}")


def deb_version(url):
    """Version field of a remote .deb, read from its first bytes (control comes first)."""
    req = urllib.request.Request(url, headers={"Range": "bytes=0-1048575"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    pos = 8  # "!<arch>\n", then 60-byte member headers
    while pos + 60 <= len(data):
        name, size = data[pos:pos + 16].decode().strip(), int(data[pos + 48:pos + 58])
        body = data[pos + 60:pos + 60 + size]
        if name.startswith("control.tar"):
            if name.endswith(".zst"):
                try:
                    from compression import zstd  # Python 3.14+
                    raw = zstd.decompress(body)
                except ImportError:
                    raw = subprocess.run(["zstd", "-dc"], input=body, capture_output=True, check=True).stdout
            else:
                import gzip
                import lzma
                raw = lzma.decompress(body) if name.endswith(".xz") else gzip.decompress(body)
            import io
            import tarfile
            with tarfile.open(fileobj=io.BytesIO(raw)) as t:
                control = t.extractfile("./control").read().decode()
            return re.search(r"^Version: (.+)$", control, re.M).group(1)
        pos += 60 + size + (size & 1)
    raise LookupError(f"no control member in the first MiB of {url}")


def entry(text, table, key):
    """(start, end) of `"key": (...)` inside the dict `table = {`."""
    t0 = text.index(f"\n{table} = {{")
    s = text.index(f'\n    "{key}": (', t0) + 1
    m = re.compile(r"\n(    \"|\})").search(text, s)
    return s, m.start() + 1


def sub_in(text, span, pairs, optional=()):
    """Replace each (old, new) inside span; the optional ones may already be gone."""
    s, e = span
    part = text[s:e]
    for old, new in [*pairs, *optional]:
        if old not in part and (old, new) in optional:
            continue
        if old not in part:
            raise LookupError(f"{old!r} not found where expected")
        part = part.replace(old, new)
    return text[:s] + part + text[e:]


def var_lines(text, names):
    """span covering the assignment lines of these variables (plus their trailing comments)."""
    starts = [re.search(rf"^{n} = .*$", text, re.M) for n in names]
    return min(m.start() for m in starts), max(m.end() for m in starts)


def strip(tag):
    """Version from a tag: "cli-v1.2" -> "1.2"."""
    return re.sub(r"^\D*", "", tag)


def bump(text, d, name, pinned, new, var):
    """Return the new text, or raise LookupError (unknown kind) / other errors."""
    if var.startswith(("release_tools[", "extra_fonts[")):
        table = var.split("[")[0]
        url, sha = d[table][name]
        m = GH_URL.match(url)
        if not m:
            raise LookupError("not a GitHub release download")
        repo, tag, asset = m.groups()
        new_asset = asset.replace(strip(tag), strip(new))
        return sub_in(text, entry(text, table, name),
                      [(sha, gh_digest(repo, new, new_asset)), (tag, new)], [(strip(tag), strip(new))])
    if var == "artcraft_apps":
        ver, sha = d["artcraft_apps"][name]
        nv = strip(new)
        digest = gh_digest(f"storytold/{name}", new, f"{name}-{nv}-linux-x86_64.deb")
        return sub_in(text, entry(text, "artcraft_apps", name), [(sha, digest), (f'"{ver}"', f'"{nv}"')])
    simple = {  # var: (repo, tag for version v, asset for version v, sha variable)
        "obsidian_version": ("obsidianmd/obsidian-releases", "v{}", "obsidian_{}_amd64.deb", "obsidian_sha256"),
        "bitwarden_version": ("bitwarden/clients", "desktop-v{}", "Bitwarden-{}-amd64.deb", "bitwarden_sha256"),
        "snitchd_version": ("norandom/snitch", "v{}", "snitchd", "snitchd_sha256"),
        "safe_chain_version": ("AikidoSec/safe-chain", "{}", "install-safe-chain.sh", "safe_chain_installer_sha256"),
    }
    if var in simple:
        repo, tag_f, asset_f, sha_var = simple[var]
        old, nv = d[var], strip(new) if var != "safe_chain_version" else new
        digest = gh_digest(repo, tag_f.format(nv), asset_f.format(nv))
        return sub_in(text, var_lines(text, [var, sha_var]), [(d[sha_var], digest), (old, nv)])
    if var == "client_debs['quarto']":
        ver, url, sha = d["client_debs"]["quarto"]
        nv = strip(new)
        digest = gh_digest("quarto-dev/quarto-cli", new, f"quarto-{nv}-linux-amd64.deb")
        return sub_in(text, entry(text, "client_debs", "quarto"), [(sha, digest), (ver, nv)])
    if var == "client_debs['code']":
        ver, url, sha = d["client_debs"]["code"]
        info = json.loads(pc.http(f"https://update.code.visualstudio.com/api/versions/{new}/linux-deb-x64/stable"))
        dpkg = re.search(r"code_([^_]+)_amd64\.deb", info["url"]).group(1)
        base = "https://vscode.download.prss.microsoft.com/dbazure/download/stable/"
        s, e = entry(text, "client_debs", "code")
        lines = (f'    "code": ("{dpkg}", "{base}"\n'
                 f'             "{info["url"][len(base):]}",\n'
                 f'             "{info["sha256hash"]}"),\n')
        if not info["url"].startswith(base):
            raise LookupError(f"VS Code moved its downloads: {info['url']}")
        return text[:s] + lines + text[e:]
    if var == "client_debs['positron']":
        ver, url, sha = d["client_debs"]["positron"]
        info = json.loads(pc.http("https://cdn.posit.co/positron/releases/deb/x86_64/releases.json"))
        return sub_in(text, entry(text, "client_debs", "positron"),
                      [(sha, info["sha256hash"]), (url, info["url"]), (ver, deb_version(info["url"]))])
    if var == "ax_go_toolchain":  # Go verifies the toolchain itself; only the name is pinned
        return sub_in(text, var_lines(text, [var]), [(d[var], new)])
    if var == "nvim_simple_commit":
        full = pc.gh("repos/norandom/nvim-simple/commits/HEAD")["sha"]
        return sub_in(text, var_lines(text, [var]), [(d[var], full)])
    raise LookupError("manual")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    d = {}
    exec(ALL.read_text(), d)
    text = ALL.read_text()
    bumped, manual = [], []
    for name, pinned, latest, var in pc.pins(d):
        if args and name not in args:
            continue
        try:
            new = latest()
        except Exception as e:
            manual.append((name, pinned, "?", f"lookup failed: {e}".splitlines()[0]))
            continue
        if new == pinned:
            continue
        try:
            text = bump(text, d, name, pinned, new, var)
            bumped.append((name, pinned, new))
        except Exception as e:
            manual.append((name, pinned, new, str(e) if str(e) != "manual" else f"bump by hand: {var}"))
    for name, pinned, new in bumped:
        print(f"bumped  {name}: {pinned} -> {new}")
    for name, pinned, new, why in manual:
        print(f"MANUAL  {name}: {pinned} -> {new} ({why})")
    if not bumped and not manual:
        print("all pins current")
    if bumped and not dry:
        ALL.write_text(text)
        print("\ngroup_data/all.py updated. Next: deploy (uv run pyinfra -y inventory.py deploy.py), check, commit.")
    sys.exit(1 if manual else 0)


if __name__ == "__main__":
    main()
