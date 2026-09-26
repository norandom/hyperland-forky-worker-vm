"""Omarchy's generated theme files for CLI tools (Cream Blue), activated the way
Omarchy does it: btop color_theme, Claude Code custom theme, Chromium policy."""
from pyinfra import host
from pyinfra.operations import files, server

home = host.data.desktop_home

# btop: theme file + color_theme in btop.conf (btop writes the rest itself)
files.put(name="btop theme (Omarchy Cream Blue)", src="files/themes/btop-cream-blue.theme",
          dest=f"{home}/.config/btop/themes/cream-blue.theme", mode="644")
server.shell(
    name="btop uses it",
    commands=[f"""f={home}/.config/btop/btop.conf; touch "$f"
grep -q '^color_theme' "$f" && sed -i 's|^color_theme = .*|color_theme = "cream-blue"|' "$f" || echo 'color_theme = "cream-blue"' >> "$f\""""],
)

# Claude Code: custom theme file (hot-reloaded) + settings.json "theme"
files.put(name="Claude Code theme (Omarchy Cream Blue)", src="files/themes/claude-omarchy.json",
          dest=f"{home}/.claude/themes/omarchy.json", mode="600")
server.shell(
    name="Claude Code uses it (settings.json theme = custom:omarchy)",
    commands=[f"""f={home}/.claude/settings.json
[ -s "$f" ] || echo '{{}}' > "$f"
t=$(mktemp) && jq '.theme = "custom:omarchy"' "$f" > "$t" && mv "$t" "$f\""""],
)

# Chromium: browser frame colour via managed policy (as omarchy-theme-set-browser-policy does)
files.put(name="Chromium theme colour policy (cream)", src="files/themes/chromium-policy.json",
          dest="/etc/chromium/policies/managed/debian-hypr-theme.json", mode="644", _sudo=True)
