"""Themes for CLI tools, one per Terminator profile (default = cobalt, navy, fixedsys,
cream). hypr-termtheme switches them together with the terminal; Chromium keeps the cream frame."""
from pyinfra import host
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
