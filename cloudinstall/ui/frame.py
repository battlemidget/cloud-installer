# Copyright 2015 Canonical, Ltd.
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

""" Base Frame Widget """

from urwid import Frame, WidgetWrap
from .anchors import (InstallHeader,
                      InstallFooter,
                      StatusHeader,
                      StatusFooter,
                      Body)
import logging


log = logging.getLogger('subiquity.ui.frame')

# COMMON
key_conversion_map = {'tab': 'down', 'shift tab': 'up'}


class OpenstackInstallUI(WidgetWrap):
    """ Base UI for the install portion of the application
    """
    def __init__(self, header=None, body=None, footer=None):
        self.header = header if header else InstallHeader()
        self.body = body if body else Body()
        self.footer = footer if footer else InstallFooter()
        self.frame = Frame(self.body, header=self.header, footer=self.footer)
        super().__init__(self.frame)

    def keypress(self, size, key):
        key = key_conversion_map.get(key, key)
        return super().keypress(size, key)

    def set_header(self, title=None, excerpt=None):
        self.frame.header = InstallHeader(title, excerpt)

    def set_footer(self, message):
        self.frame.footer = InstallFooter(message)

    def set_body(self, widget):
        self.frame.body = widget


class OpenstackStatusUI(WidgetWrap):
    """ Base UI for the status portion of the application
    """

    def __init__(self, header=None, body=None, footer=None):
        self.header = header if header else StatusHeader()
        self.body = body if body else Body()
        self.footer = footer if footer else StatusFooter()
        self.frame = Frame(self.body, header=self.header, footer=self.footer)
        super().__init__(self.frame)

    def keypress(self, size, key):
        key = key_conversion_map.get(key, key)
        return super().keypress(size, key)

    def set_header(self, title=None, excerpt=None):
        self.frame.header = StatusHeader(title, excerpt)

    def set_footer(self, message):
        self.frame.footer = StatusFooter(message)

    def set_body(self, widget):
        self.frame.body = widget
