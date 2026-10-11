#!/usr/bin/env python3
"""Generate the VS Code / Positron colour themes from the Sublime Text schemes.

    python3 tools/vscodetheme.py     # writes files/vscode/debian-hypr-themes/

One local extension ("debian-hypr Cobalt", "… Navy", "… Fixedsys", "… Cream", "… Petrol"):
editor and syntax colours from files/sublime/debian-hypr-<t>.sublime-color-scheme, terminal
colours from files/ghostty/themes/<t>, the workbench (side bar, tabs, status bar) flat in
the same colours. hypr-termtheme picks the one matching the terminal profile.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "files/vscode/debian-hypr-themes"
THEMES = ("cobalt", "navy", "fixedsys", "cream", "petrol")
ANSI = ("Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White")


def palette(theme):
    pal = {}
    for line in (ROOT / f"files/ghostty/themes/{theme}").read_text().splitlines():
        if m := re.match(r"palette = (\d+)=(#[0-9a-fA-F]{6})", line):
            pal[int(m.group(1))] = m.group(2)
    return pal


def theme_json(theme):
    sub = json.loads((ROOT / f"files/sublime/debian-hypr-{theme}.sublime-color-scheme").read_text())
    g, pal = sub["globals"], palette(theme)
    bg, fg, alt = g["background"], g["foreground"], g["line_highlight"]
    dim, acc, acc_fg = g["gutter_foreground"], g["find_highlight"], g["find_highlight_foreground"]
    sel, guide = g["selection"], g["guide"]
    colors = {
        "foreground": fg, "focusBorder": acc, "widget.shadow": "#00000000",
        "editor.background": bg, "editor.foreground": fg, "editorCursor.foreground": g["caret"],
        "editor.selectionBackground": sel, "editor.lineHighlightBackground": alt,
        "editor.findMatchHighlightBackground": acc + "66", "editorLineNumber.foreground": dim,
        "editorLineNumber.activeForeground": fg, "editorWhitespace.foreground": g["invisibles"],
        "editorIndentGuide.background1": guide, "editorIndentGuide.activeBackground1": g["active_guide"],
        "editorBracketMatch.border": g["brackets_foreground"], "editorGutter.background": g["gutter"],
        "editorGutter.addedBackground": g["line_diff_added"], "editorGutter.modifiedBackground": g["line_diff_modified"],
        "editorGutter.deletedBackground": g["line_diff_deleted"],
        "editorWidget.background": alt, "editorWidget.foreground": fg, "editorHoverWidget.background": alt,
        "editorSuggestWidget.background": alt, "editorSuggestWidget.selectedBackground": sel,
        "activityBar.background": alt, "activityBar.foreground": fg, "activityBar.inactiveForeground": dim,
        "activityBarBadge.background": acc, "activityBarBadge.foreground": acc_fg,
        "sideBar.background": alt, "sideBar.foreground": fg, "sideBarTitle.foreground": fg,
        "sideBarSectionHeader.background": bg, "sideBarSectionHeader.foreground": fg,
        "titleBar.activeBackground": alt, "titleBar.activeForeground": fg,
        "titleBar.inactiveBackground": alt, "titleBar.inactiveForeground": dim,
        "statusBar.background": alt, "statusBar.foreground": fg, "statusBar.noFolderBackground": alt,
        "statusBar.debuggingBackground": acc, "statusBar.debuggingForeground": acc_fg,
        "statusBarItem.remoteBackground": acc, "statusBarItem.remoteForeground": acc_fg,
        "editorGroupHeader.tabsBackground": alt, "tab.activeBackground": bg, "tab.activeForeground": fg,
        "tab.inactiveBackground": alt, "tab.inactiveForeground": dim, "tab.border": alt,
        "tab.activeBorderTop": acc, "panel.background": bg, "panel.border": guide,
        "panelTitle.activeForeground": fg, "panelTitle.inactiveForeground": dim, "panelTitle.activeBorder": acc,
        "input.background": alt, "input.foreground": fg, "input.border": guide,
        "dropdown.background": alt, "dropdown.foreground": fg, "dropdown.border": guide,
        "button.background": acc, "button.foreground": acc_fg,
        "badge.background": acc, "badge.foreground": acc_fg,
        "list.activeSelectionBackground": sel, "list.activeSelectionForeground": fg,
        "list.inactiveSelectionBackground": sel, "list.hoverBackground": alt, "list.highlightForeground": acc,
        "menu.background": alt, "menu.foreground": fg, "menu.selectionBackground": sel,
        "menu.selectionForeground": fg, "menubar.selectionBackground": sel,
        "quickInput.background": alt, "quickInputList.focusBackground": sel,
        "scrollbarSlider.background": guide + "80", "scrollbarSlider.hoverBackground": guide,
        "terminal.background": bg, "terminal.foreground": fg, "terminalCursor.foreground": g["caret"],
        "terminal.selectionBackground": sel,
        "gitDecoration.addedResourceForeground": g["line_diff_added"],
        "gitDecoration.modifiedResourceForeground": g["line_diff_modified"],
        "gitDecoration.deletedResourceForeground": g["line_diff_deleted"],
    }
    for i, name in enumerate(ANSI):
        if i in pal:
            colors[f"terminal.ansi{name}"] = pal[i]
        if i + 8 in pal:
            colors[f"terminal.ansiBright{name}"] = pal[i + 8]
    tokens = []
    for r in sub["rules"]:
        settings = {k: v for k, v in (("foreground", r.get("foreground")),
                                      ("fontStyle", r.get("font_style"))) if v}
        tokens.append({"name": r["name"], "scope": [s.strip() for s in r["scope"].split(",")],
                       "settings": settings})
    light = theme == "cream"
    return {"name": label(theme), "type": "light" if light else "dark", "colors": colors,
            "tokenColors": tokens, "semanticHighlighting": False}


def label(theme):
    return f"debian-hypr {theme.capitalize()}"


def main():
    (OUT / "themes").mkdir(parents=True, exist_ok=True)
    pkg = {
        "name": "debian-hypr-themes", "displayName": "debian-hypr themes", "publisher": "debian-hypr",
        "version": "1.0.0", "description": "Managed by debian-hypr (tools/vscodetheme.py): the terminal profile themes",
        "engines": {"vscode": "^1.80.0"}, "categories": ["Themes"],
        "contributes": {"themes": [{"label": label(t), "uiTheme": "vs" if t == "cream" else "vs-dark",
                                    "path": f"./themes/{t}-color-theme.json"} for t in THEMES]},
    }
    (OUT / "package.json").write_text(json.dumps(pkg, indent=2) + "\n")
    for t in THEMES:
        (OUT / f"themes/{t}-color-theme.json").write_text(json.dumps(theme_json(t), indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(THEMES)} themes)")


if __name__ == "__main__":
    main()
