#!/usr/bin/env python3
"""Generate the Ghostty and foot themes from the Terminator profiles.

    python3 tools/themegen.py        # writes files/ghostty/themes/* and files/foot/themes/*

Colours, cursor and font come from files/terminator/config; the Ghostty tab bar
uses the tab colours of files/terminator/plugins/theme_menu.py. Theme name = the
profile name, except "default", which is "cobalt" (as in hypr-termtheme).
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cfg = (ROOT / "files/terminator/config").read_text()
section = cfg.split("[profiles]", 1)[1].split("\n[layouts]", 1)[0]
profiles, cur = {}, None
for line in section.splitlines():
    m = re.match(r"^  \[\[(.+)\]\]$", line)
    if m:
        cur = m.group(1); profiles[cur] = {}; continue
    m = re.match(r"^    (\w+) = (.*)$", line)
    if cur and m:
        profiles[cur][m.group(1)] = m.group(2).strip().strip('"')

plugin = (ROOT / "files/terminator/plugins/theme_menu.py").read_text()
tabs = ast.literal_eval(re.search(r"TAB_COLOURS = (\{.*?\n\})", plugin, re.S).group(1))

CSS = """/* Managed by debian-hypr (tools/themegen.py). Ghostty tab bar for the "{t}" theme: a
   slim line in Terminator's tab colours instead of the tall Adwaita toolbar. */
toolbarview > .top-bar, toolbarview > .bottom-bar {{ min-height: 0; background: {bar}; box-shadow: none; }}
tabbar .box {{ min-height: 0; padding: 0; background: {bar}; border: none; box-shadow: none; }}
tabbar tabbox, tabbar tabbox > tabboxchild {{ min-height: 0; padding: 0; margin: 0; }}
tabbar tab {{ min-height: 20px; padding: 0 10px; margin: 0; border-radius: 0;
             background: transparent; color: {fg}; box-shadow: none; }}
tabbar tab:hover {{ color: {act}; background: transparent; }}
tabbar tab:selected, tabbar tab:selected:hover {{ background: {act}; color: {act_fg}; }}
tabbar tab label {{ font-family: "{font}"; font-size: 9pt; }}
tabbar tab button.image-button {{ min-height: 16px; min-width: 16px; padding: 0; margin: 0; border-radius: 0; }}
tabbar tabbox > separator {{ opacity: 0; }}
tabbar .start-action, tabbar .end-action {{ padding: 0; }}
/* libadwaita rounds the container around each tab (tabboxchild), not the tab */
tabbar tab, tabbar tabbox > tabboxchild {{ border-radius: 0; }}
"""

for prof, p in profiles.items():
    theme = "cobalt" if prof == "default" else prof
    pal = p["palette"].split(":")
    fam, size = p["font"].rsplit(" ", 1)
    bg, fg = p["background_color"], p["foreground_color"]
    cur_bg = p.get("cursor_bg_color") or p.get("cursor_color") or fg
    cur_fg = p.get("cursor_fg_color") or bg
    g = [f"# Managed by debian-hypr (tools/themegen.py). Ghostty theme = Terminator profile \"{prof}\"",
         "# (hypr-termtheme switches it).",
         f"background = {bg}", f"foreground = {fg}",
         f"cursor-color = {cur_bg}", f"cursor-text = {cur_fg}",
         f"selection-background = {pal[8]}", f"selection-foreground = {fg}"]
    g += [f"palette = {i}={c}" for i, c in enumerate(pal)]
    g += [f"font-family = {fam}", f"font-size = {size}", f"gtk-custom-css = themes/{theme}.css"]
    (ROOT / f"files/ghostty/themes/{theme}").write_text("\n".join(g) + "\n")
    bar, tfg, act, act_fg = tabs.get(prof, tabs["default"])
    (ROOT / f"files/ghostty/themes/{theme}.css").write_text(CSS.format(t=theme, bar=bar, fg=tfg, act=act, act_fg=act_fg, font=fam))
    h = lambda c: c.lstrip("#")
    f = [f"# Managed by debian-hypr (tools/themegen.py). foot theme = Terminator profile \"{prof}\" (hypr-termtheme).",
         "[main]", f"font={fam}:size={size}", "", "[cursor]", f"color={h(cur_fg)} {h(cur_bg)}", "", "[colors-dark]",
         f"background={h(bg)}", f"foreground={h(fg)}", f"selection-background={h(pal[8])}", f"selection-foreground={h(fg)}"]
    f += [f"regular{i}={h(c)}" for i, c in enumerate(pal[:8])] + [f"bright{i}={h(c)}" for i, c in enumerate(pal[8:])]
    (ROOT / f"files/foot/themes/{theme}.ini").write_text("\n".join(f) + "\n")
    print(f"{theme:9} bg {bg} fg {fg} cursor {cur_bg}/{cur_fg} font {fam} {size}")
