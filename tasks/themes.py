"""Themes for CLI tools, activated the way Omarchy does it. Terminal tools use the
terminal's cobalt palette (cream-blue-cobalt); Chromium keeps the cream frame."""
from pyinfra import host
from pyinfra.operations import files, server

home = host.data.desktop_home

# btop: theme file + color_theme in btop.conf (btop writes the rest itself)
files.put(name="btop theme (cobalt, transparent background)", src="files/themes/btop-cobalt.theme",
          dest=f"{home}/.config/btop/themes/cobalt.theme", mode="644")
server.shell(
    name="btop uses it",
    commands=[f"""f={home}/.config/btop/btop.conf; touch "$f"
grep -q '^color_theme' "$f" && sed -i 's|^color_theme = .*|color_theme = "cobalt"|' "$f" || echo 'color_theme = "cobalt"' >> "$f\""""],
)

# Claude Code: custom theme file (hot-reloaded) + settings.json "theme"
files.put(name="Claude Code theme (cobalt)", src="files/themes/claude-cobalt.json",
          dest=f"{home}/.claude/themes/cobalt.json", mode="600")
server.shell(
    name="Claude Code uses it (settings.json theme = custom:cobalt)",
    commands=[f"""f={home}/.claude/settings.json
[ -s "$f" ] || echo '{{}}' > "$f"
t=$(mktemp) && jq '.theme = "custom:cobalt"' "$f" > "$t" && mv "$t" "$f\""""],
)

# Chromium: browser frame colour via managed policy (as omarchy-theme-set-browser-policy does)
files.put(name="Chromium theme colour policy (cream)", src="files/themes/chromium-policy.json",
          dest="/etc/chromium/policies/managed/debian-hypr-theme.json", mode="644", _sudo=True)
