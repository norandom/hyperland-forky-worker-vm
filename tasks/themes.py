"""Themes for CLI tools, one per Terminator profile (default = cobalt, navy, fixedsys,
cream). hypr-termtheme switches them together with the terminal; Chromium keeps the cream frame."""
from pyinfra import host
from pyinfra.facts.server import Hostname
from pyinfra.operations import files, server

home = host.data.desktop_home
themes = ("cobalt", "navy", "fixedsys", "cream", "petrol")

for t in themes:
    files.put(name=f"btop theme ({t}, transparent background)", src=f"files/themes/btop-{t}.theme",
              dest=f"{home}/.config/btop/themes/{t}.theme", mode="644")
    files.put(name=f"Claude Code theme ({t})", src=f"files/themes/claude-{t}.json",
              dest=f"{home}/.claude/themes/{t}.json", mode="600")

# Sublime Text colour schemes (hypr-termtheme sets color_scheme + font in Preferences)
for t in themes:
    files.put(name=f"Sublime Text colour scheme ({t})", src=f"files/sublime/debian-hypr-{t}.sublime-color-scheme",
              dest=f"{home}/.config/sublime-text/Packages/User/debian-hypr-{t}.sublime-color-scheme",
              mode="644", create_remote_dir=True)

# Ghostty + foot themes (hypr-termtheme copies the current one to ghostty/theme, foot/theme.ini)
for t in themes:
    files.put(name=f"Ghostty theme ({t})", src=f"files/ghostty/themes/{t}",
              dest=f"{home}/.config/ghostty/themes/{t}", mode="644", create_remote_dir=True)
    files.put(name=f"Ghostty tab bar ({t})", src=f"files/ghostty/themes/{t}.css",
              dest=f"{home}/.config/ghostty/themes/{t}.css", mode="644", create_remote_dir=True)
    files.put(name=f"foot theme ({t})", src=f"files/foot/themes/{t}.ini",
              dest=f"{home}/.config/foot/themes/{t}.ini", mode="644", create_remote_dir=True)
# Ghostty's old config name (the base config is config.ghostty now)
files.file(name="Ghostty: remove old ~/.config/ghostty/config", path=f"{home}/.config/ghostty/config", present=False)

# VS Code + Positron (client role): the debian-hypr themes as a local extension (tools/vscodetheme.py),
# settings the deploy owns: no telemetry, no self-update (the pinned .deb is the update path),
# native title bars (the Hyprland ones, in the host colour). hypr-termtheme sets theme + font.
if host.get_fact(Hostname) in host.data.get("client_hosts", []):
    for data, conf in ((".vscode", "Code"), (".positron", "Positron")):
        files.sync(name=f"{conf}: debian-hypr themes extension", src="files/vscode/debian-hypr-themes/",
                   dest=f"{home}/{data}/extensions/debian-hypr.debian-hypr-themes-1.0.0", delete=True)
        server.shell(
            name=f"{conf}: telemetry off, no self-update, native title bar",
            commands=[f"""python3 - {home}/.config/{conf}/User/settings.json <<'EOF'
import json, os, re, sys
path = sys.argv[1]
try:
    prefs = json.loads(re.sub(r",(\\s*[}}\\]])", r"\\1", re.sub(r"^\\s*//.*$", "", open(path).read(), flags=re.M)))
except FileNotFoundError:
    prefs = {{}}
except ValueError:
    sys.exit(0)  # leave a file we can't parse alone
want = {{"telemetry.telemetryLevel": "off", "update.mode": "none", "window.titleBarStyle": "native",
        "workbench.enableExperiments": False, "extensions.ignoreRecommendations": True}}
if any(prefs.get(k) != v for k, v in want.items()):
    prefs.update(want)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(prefs, f, indent=4)
        f.write("\\n")
EOF"""],
        )

# btop.conf needs a color_theme line for hypr-termtheme to rewrite (btop writes the rest).
server.shell(
    name="btop: color_theme line present",
    commands=[f"""f={home}/.config/btop/btop.conf; mkdir -p "${{f%/*}}"; touch "$f"
grep -q '^color_theme' "$f" || echo 'color_theme = "cobalt"' >> "$f\""""],
)
# Claude Code (settings.json "theme", hot-reloaded), btop and Sublime Text follow the current terminal profile.
server.shell(
    name="Claude Code, btop, Ghostty, foot, Sublime Text use the current terminal profile's theme (hypr-termtheme apply)",
    commands=[f"{home}/.local/bin/hypr-termtheme apply"],
)

# Chromium: browser frame colour via managed policy (as omarchy-theme-set-browser-policy does)
files.put(name="Chromium theme colour policy (cream)", src="files/themes/chromium-policy.json",
          dest="/etc/chromium/policies/managed/debian-hypr-theme.json", mode="644", _sudo=True)
