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

from urwid import (WidgetWrap, Text, Filler, Pile)


class BannerWidget(WidgetWrap):

    def __init__(self):
        self.text = []
        self.flash_text = Text('', align='center')
        self.BANNER = [
            "",
            "",
            "Ubuntu OpenStack Installer",
            "",
            "By Canonical, Ltd.",
            ""
        ]
        super().__init__(self._create_text())

    def _create_text(self):
        self.text = []
        for line in self.BANNER:
            self._insert_line(line)

        self.text.append(self.flash_text)
        return Filler(Pile(self.text), valign='middle')

    def _insert_line(self, line):
        text = Text(line, align='center')
        self.text.append(text)

    def flash(self, msg):
        self.flash_text.set_text([('error_major', msg)])

    def flash_reset(self):
        self.flash_text.set_text('')
