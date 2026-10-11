#!/usr/bin/env python3
"""Have newer versions of the pinned dependencies been published?

    tools/pin-check.py              # table of every pin, outdated ones marked
    tools/pin-check.py --markdown   # only the outdated ones, as a Markdown list (CI issue body)

Reads the pins from group_data/all.py and asks each upstream for its latest stable release
(GitHub via `gh api`, so it needs `gh` logged in or GH_TOKEN; Go, Kubernetes, Little Snitch
from their own sites). Only reports; bumping a pin (version + sha256) stays a manual commit.
Exit 0: all current, 1: updates found, 2: a lookup failed (and no updates).
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

PRE = re.compile(r"(alpha|beta|rc|pre|nightly|dev)", re.I)


def gh(path):
    return json.loads(subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout)


def http(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return r.read().decode()


def gh_latest(repo, prefix=""):
    """Newest non-draft, non-prerelease release whose tag starts with prefix."""
    for r in gh(f"repos/{repo}/releases?per_page=50"):
        tag = r["tag_name"]
        if not r["draft"] and not r["prerelease"] and tag.startswith(prefix) and not PRE.search(tag[len(prefix):]):
            return tag
    raise LookupError(f"no stable release with prefix {prefix!r}")


def pins(d):
    """(name, pinned tag, function returning the latest tag, where the pin lives)"""
    gh_url = re.compile(r"https://github\.com/([^/]+/[^/]+)/releases/download/([^/]+)/")
    urls = [(n, u, "release_tools") for n, (u, _) in d["release_tools"].items()]
    urls += [(n, u, "extra_fonts") for n, (u, _) in d["extra_fonts"].items()]
    for name, url, table in urls:
        if m := gh_url.match(url):
            repo, tag = m.groups()
            prefix = re.match(r"^\D*", tag).group()   # "v", "cli-v", ...
            yield name, tag, lambda r=repo, p=prefix: gh_latest(r, p), f"{table}[{name!r}]"
        elif name == "kubectl":
            yield name, url.split("/")[4], lambda: http("https://dl.k8s.io/release/stable.txt").strip(), "release_tools"
        elif name == "helm":
            yield name, re.search(r"helm-(v[\d.]+)-", url).group(1), lambda: gh_latest("helm/helm", "v"), "release_tools"
    rel = [  # (name, repo, tag prefix, pinned version, variable)
        ("hypr-rdp (upstream)", "MuNeNICK/hypr-rdp", "v", d["hypr_rdp_version"], "hypr_rdp_version"),
        ("safe-chain", "AikidoSec/safe-chain", "", d["safe_chain_version"], "safe_chain_version"),
        ("nerd-fonts", "ryanoasis/nerd-fonts", "v", d["nerd_font_version"], "nerd_font_version"),
        ("obsidian", "obsidianmd/obsidian-releases", "v", d["obsidian_version"], "obsidian_version"),
        ("ghostty (forky .deb)", "mkasberg/ghostty-ubuntu", "", d["ghostty_release"], "ghostty_release"),
        ("bitwarden desktop", "bitwarden/clients", "desktop-v", d["bitwarden_version"], "bitwarden_version"),
        ("ax", "google/ax", "", d["ax_version"], "ax_version"),
        ("snitch", "norandom/snitch", "v", d["snitch_version"], "snitch_version"),
        *[(n, f"storytold/{n}", "v", v, "artcraft_apps") for n, (v, _sha) in d["artcraft_apps"].items()],
    ]
    for name, repo, prefix, ver, var in rel:
        if ver:
            yield name, prefix + ver, lambda r=repo, p=prefix: gh_latest(r, p), var
    cd = d.get("client_debs", {})
    if "quarto" in cd:
        yield ("quarto", "v" + cd["quarto"][0], lambda: gh_latest("quarto-dev/quarto-cli", "v"), "client_debs['quarto']")
    if "positron" in cd:
        yield ("positron", re.search(r"Positron-(.+)-x64\.deb", cd["positron"][1]).group(1),
               lambda: json.loads(http("https://cdn.posit.co/positron/releases/deb/x86_64/releases.json"))["version"],
               "client_debs['positron']")
    if "code" in cd:
        yield ("vscode", cd["code"][0].split("-")[0],
               lambda: json.loads(http("https://update.code.visualstudio.com/api/releases/stable"))[0], "client_debs['code']")
    if d.get("ax_go_toolchain"):
        yield ("go toolchain (ax)", d["ax_go_toolchain"],
               lambda: json.loads(http("https://go.dev/dl/?mode=json"))[0]["version"], "ax_go_toolchain")
    if d.get("littlesnitch_version"):
        yield ("littlesnitch", d["littlesnitch_version"], lambda: max(
            re.findall(r"littlesnitch_([\d.]+)_amd64\.deb", http("https://obdev.at/products/littlesnitch-linux/download.html")),
            key=lambda v: [int(x) for x in v.split(".")]), "littlesnitch_version")
    if d.get("nvim_simple_commit"):
        yield ("nvim-simple (commit)", d["nvim_simple_commit"][:12],
               lambda: gh("repos/norandom/nvim-simple/commits/HEAD")["sha"][:12], "nvim_simple_commit")


def main():
    d = {}
    exec((Path(__file__).resolve().parent.parent / "group_data/all.py").read_text(), d)
    rows, outdated, failed = [], [], []
    for name, pinned, latest, var in pins(d):
        try:
            new = latest()
        except Exception as e:  # report and go on: one dead upstream must not hide the rest
            new, mark = f"? {e}".splitlines()[0][:60], "?"
            failed.append(name)
        else:
            mark = "" if new == pinned else "UPDATE"
            if mark:
                outdated.append((name, pinned, new, var))
        rows.append((mark, name, pinned, new))
    if "--markdown" in sys.argv:
        for name, pinned, new, var in outdated:
            sha = "" if var in ("ax_go_toolchain", "nvim_simple_commit") else "; bump the sha256 too"
            print(f"- [ ] **{name}**: `{pinned}` → `{new}` (group_data/all.py: `{var}`{sha})")
        for name in failed:
            print(f"- lookup failed: {name}")
    else:
        w = max(len(r[1]) for r in rows)
        for mark, name, pinned, new in rows:
            print(f"{mark:6} {name:{w}}  {pinned:24} {new}")
        print(f"\n{len(outdated)} update(s), {len(failed)} lookup failure(s), {len(rows)} pins")
    sys.exit(1 if outdated else 2 if failed else 0)


if __name__ == "__main__":
    main()
