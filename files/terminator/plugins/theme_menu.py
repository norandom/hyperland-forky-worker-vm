"""Terminator plugin (debian-hypr): right-click menu "Theme" to switch all
terminals between the profiles; the choice also applies to new windows.
The tab bar follows the profile too: its font (family of the profile's font)
and colours are restyled live when ~/.local/state/terminator-profile changes.
The config itself is re-read when ~/.config/terminator/config changes (a deploy
adding a theme), so new profiles work without restarting Terminator."""
import os
import subprocess

from gi.repository import Gdk, Gio, Gtk
import terminatorlib.plugin as plugin
from terminatorlib.config import Config

AVAILABLE = ['ThemeMenu']
SWITCH = os.path.expanduser('~/.local/bin/hypr-termtheme')
STATE = os.path.expanduser('~/.local/state/terminator-profile')
CONFIG = os.path.expanduser('~/.config/terminator/config')

# Tab bar per profile: (bar background, tab text, active tab background, active tab text).
# Base layout (slim tmux-style tabs) is in ~/.config/gtk-3.0/gtk.css.
TAB_COLOURS = {
    'default': ('#00347d', '#8bb4e0', '#f1dc9a', '#00347d'),
    'navy': ('#243b55', '#7b96b4', '#c4933f', '#1a2a3f'),
    'fixedsys': ('#2a2f4c', '#b07838', '#ffa348', '#1f233c'),
    'cream': ('#ebe3d6', '#5b7fa5', '#2b4570', '#fff8f0'),
    'petrol': ('#073642', '#c77a2e', '#ff911d', '#002b36'),
}
TAB = '.terminator-terminal-window notebook > header'


def _font_family(profile):
    font = Config().base.profiles.get(profile, {}).get('font', '') or 'FiraCode Nerd Font 11'
    return font.rsplit(' ', 1)[0] if font.rsplit(' ', 1)[-1].isdigit() else font


class _TabStyle:
    """One CSS provider, rewritten whenever the profile state file changes."""

    def __init__(self):
        self.provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
        self.monitor = Gio.File.new_for_path(STATE).monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.monitor.connect('changed', lambda *_a: self.apply())
        self.cfg_monitor = Gio.File.new_for_path(CONFIG).monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.cfg_monitor.connect('changed', self.reload_config)
        self.apply()

    def reload_config(self, _monitor, _file, _other, event):
        # New or changed profiles (e.g. a theme added by a deploy) without a restart
        if event == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            try:
                Config().base.reload()
            except Exception:  # a half-written file: the next change event retries
                pass
            self.apply()

    def apply(self):
        try:
            with open(STATE) as f:
                profile = f.read().strip() or 'default'
        except OSError:
            profile = 'default'
        bar, fg, active, active_fg = TAB_COLOURS.get(profile, TAB_COLOURS['default'])
        css = f"""
{TAB} {{ background: {bar}; }}
{TAB} tab {{ color: {fg}; font-family: "{_font_family(profile)}"; }}
{TAB} tab:hover {{ color: {active}; }}
{TAB} tab:checked {{ background: {active}; color: {active_fg}; }}
"""
        self.provider.load_from_data(css.encode())


_style = None


class ThemeMenu(plugin.MenuItem):
    capabilities = ['terminal_menu']

    def __init__(self):
        global _style
        plugin.MenuItem.__init__(self)
        if _style is None and Gdk.Screen.get_default() is not None:
            _style = _TabStyle()

    def callback(self, menuitems, menu, terminal):
        item = Gtk.MenuItem.new_with_label('Theme')
        sub = Gtk.Menu()
        current = terminal.get_profile()
        for name in Config().list_profiles():
            entry = Gtk.CheckMenuItem.new_with_label(name)
            entry.set_draw_as_radio(True)
            entry.set_active(name == current)
            entry.connect('activate', lambda _w, n=name: subprocess.Popen([SWITCH, n]))
            sub.append(entry)
        item.set_submenu(sub)
        menuitems.append(item)
