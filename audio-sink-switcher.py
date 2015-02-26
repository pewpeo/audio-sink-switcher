#!/usr/bin/env python3
#
# Note:
# A re-implementaion (primary for myself) of:
# https://github.com/yktoo/indicator-sound-switcher
# Icon(s) by: https://github.com/yktoo/indicator-sound-switcher
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GLib
from gi.repository import AppIndicator3 as appindicator

import os.path
import subprocess
from collections import OrderedDict

class AudioSinkSwitcher:
    """AudioSinkSwitcher: Ubuntu Appindicator to switch between audio sinks."""

    def __init__(self):
        """Construct AudioSinkSwitcher: create Appindicator."""

        self.ind = appindicator.Indicator.new_with_path("audio-sink-switcher",
            "audio-sink-switcher-icon",
            appindicator.IndicatorCategory.APPLICATION_STATUS,
            os.path.dirname(os.path.realpath(__file__)))
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon("audio-sink-switcher-icon")

        self.menu = Gtk.Menu()
        self.sinks = AudioSinkSwitcher.get_sink_list()
        self.create_menu()

        self.ind.connect("scroll-event", self.scroll)

        # GLib.timeout_add(5000, self.handler_timeout)

    def create_menu(self):
        """Create Appindicator menu."""

       # add sink list to menud
        for label in self.sinks.keys():
            item = Gtk.MenuItem(label)
            item.connect("activate", self.set_sink)
            item.show()
            self.menu.append(item)

        # add menu separator
        item = Gtk.SeparatorMenuItem()
        item.show()
        self.menu.append(item)

        # add quit item
        item = Gtk.MenuItem("Refresh")
        item.connect("activate", self.refresh)
        item.show()
        self.menu.append(item)

        # add quit item
        item = Gtk.MenuItem("Quit")
        item.connect("activate", self.quit)
        item.show()
        self.menu.append(item)

        self.ind.set_menu(self.menu)

    def main(self):
        """Run GTK main."""
        Gtk.main()

    def quit(self, w):
        """Quit application."""
        Gtk.main_quit()

    def scroll(self, ind, steps, direction):
        "Refresh menu items on scroll event."
        self.refresh(None)

    # def handler_timeout(self):
    #     """Refresh on Glib timeout."""
    #     self.refresh(None)
    #     GLib.timeout_add(5000, self.handler_timeout)

    def refresh(self, w):
        """Refresh menu items."""

        self.sinks = AudioSinkSwitcher.get_sink_list()
        
        # remove all menu items
        for child in self.menu.get_children():
            self.menu.remove(child)

        self.create_menu()

    def set_sink(self, w):
        """Set default sink associated to activated menu item."""

        label = w.get_label()

        p1 = subprocess.Popen(["pacmd", "list-sink-inputs"], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "index"], stdin=p1.stdout, stdout=subprocess.PIPE)
        
        grep_index = p2.communicate()[0]

        p1.stdout.close()
        p2.stdout.close()

        grep_index = grep_index.decode("utf-8")
        grep_index = grep_index.splitlines()

        # use pipe and close to suppress output of pacmd
        p1 = subprocess.Popen(["pacmd", "set-default-sink", str(self.sinks[label])], stdout=subprocess.PIPE)
        p1.stdout.close()
        # print("Setting default sink to '{:s}' (index: {:d})".format(label, self.sinks[label]))

        if (grep_index): # list of sink inputs not empty
            for line in grep_index:
                sink_input = line.split()[-1]

                # use pipe and close to suppress output of pacmd
                p1 = subprocess.Popen(["pacmd", "move-sink-input", sink_input, str(self.sinks[label])], stdout=subprocess.PIPE)
                p1.stdout.close()
                # print("Moving sink input '{:s}' to '{:s}' (index: {:d})".format(sink_input, label, self.sinks[label]))

    @staticmethod
    def get_sink_list():
        """Retrieve sink list via pacmd.

        :returns: OrderedDict{sink-name : index} sorted by index
        """

        # get lines from pacmd
        p1 = subprocess.Popen(["pacmd", "list-sinks"], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "index"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1 = subprocess.Popen(["pacmd", "list-sinks"], stdout=subprocess.PIPE)
        p3 = subprocess.Popen(["grep", "device.description"], stdin=p1.stdout, stdout=subprocess.PIPE)

        grep_index = p2.communicate()[0]
        grep_descr = p3.communicate()[0]
        
        p1.stdout.close()
        p2.stdout.close()
        p3.stdout.close()

        # extract indices
        indices = [] # sink indices
        grep_index = grep_index.decode("utf-8")
        grep_index = grep_index.splitlines()
        for line in grep_index:
            splitted = line.split()
            indices.append(int(splitted[-1]))
            # '  * index: <no>' or '    index: <no>'

        # extract descriptions
        descr = [] # sink descriptions
        grep_descr = grep_descr.decode("utf-8")
        grep_descr = grep_descr.splitlines()
        for line in grep_descr:
            idx = line.find(" = ")
            descr.append(line[idx+4:-1])
            # '\t\tdevice.description = "<name>"'

        assert len(indices) == len(descr)

        # create dictionary of sinks
        sinks = {}
        for i in range(0, len(indices)):
            sinks[descr[i]] = indices[i]

        # sort sinks by index
        sinks = OrderedDict(sorted(sinks.items(), key=lambda d: d[1]))
        return sinks

def main():
    gui = AudioSinkSwitcher()
    gui.main()

if __name__ == "__main__":
    main()
