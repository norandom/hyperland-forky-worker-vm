"""Terminator plugin (debian-hypr): right-click menu "Theme" to switch all
terminals between the profiles; the choice also applies to new windows."""
import os
import subprocess

from gi.repository import Gtk
import terminatorlib.plugin as plugin
from terminatorlib.config import Config

AVAILABLE = ['ThemeMenu']
SWITCH = os.path.expanduser('~/.local/bin/hypr-termtheme')


class ThemeMenu(plugin.MenuItem):
    capabilities = ['terminal_menu']

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
