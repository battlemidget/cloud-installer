# Copyright 2014, 2015 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from urwid import (WidgetWrap, Text, Pile)
from cloudinstall.ui.utils import Color


class HeaderWidget(WidgetWrap):

    TITLE_TEXT = "Ubuntu OpenStack Installer - Dashboard"

    def __init__(self):
        self.text = Text(self.TITLE_TEXT)
        self.widget = Color.frame_header(self.text)
        self.pile = Pile([self.widget, Text("")])
        self.set_show_add_units_hotkey(False)
        super().__init__(self.pile)

    def set_openstack_rel(self, release):
        self.text.set_text("{} ({})".format(self.TITLE_TEXT, release))

    def set_show_add_units_hotkey(self, show):
        self.show_add_units = show
        self.update()

    def update(self):
        menu_list = ['(S)tatus Screen \N{BULLET}']
        if self.show_add_units:
            menu_list.append('(A)dd Services \N{BULLET}')
        menu_list.append('(H)elp \N{BULLET}')
        menu_list.append('(R)efresh \N{BULLET}')
        menu_list.append('(Q)uit')
        tw = Color.frame_subheader(Text(" ".join(menu_list),
                                        align='center'))
        self.pile.contents[1] = (tw, self.pile.options())


class InstallHeaderWidget(WidgetWrap):

    TITLE_TEXT = "Ubuntu Openstack Installer - Software Installation"

    def __init__(self):
        self.text = Text(self.TITLE_TEXT)
        self.widget = Color.frame_header(self.text)
        w = [
            Color.frame_header(self.widget),
            Color.frame_subheader(Text(
                '(Q)uit', align='center'))
        ]
        super().__init__(Pile(w))

    def set_openstack_rel(self, release):
        self.text.set_text("{} ({})".format(
            self.TITLE_TEXT, release))
