# Copyright 2014 Canonical, Ltd.
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

""" re-usable widgets """

from __future__ import unicode_literals

import logging
from urwid import (Button, LineBox, ListBox, Pile, AttrWrap,
                   RadioButton, SimpleListWalker, Text, WidgetWrap,
                   BoxAdapter, Divider)
from collections import OrderedDict
from cloudinstall.ui.dialog import Dialog

log = logging.getLogger('cloudinstall.ui')


class InfoDialog(WidgetWrap):

    """A widget that displays a message and a close button."""

    def __init__(self, message, close_func):
        self.close_func = close_func
        button = Button("Close", self.do_close)
        box = LineBox(Pile([Text(message),
                            button]),
                      title="Info")
        super().__init__(box)

    def do_close(self, sender):
        self.close_func(self)


class Selector(Dialog):

    """
    Simple selector box

    :param str title: title of selections
    :param list opts: items to select
    :param cb: callback
    :returns: item selected from dialog
    """

    def __init__(self, title, opts, cb):
        super().__init__(title, cb)
        for item in opts:
            self.add_radio(item)
        self.show()

    def submit(self, button):
        for item in self.input_items.keys():
            _item = self.input_items[item]
            if _item.get_state():
                selected_item = _item.label
        self.emit_done_signal(selected_item)


class SelectorWithDescription(Dialog):

    """
    Simple selector box

    :param str title: title of selections
    :param list opts: items to select
    :param cb: callback
    :returns: item selected from dialog
    """

    def __init__(self, title, opts, cb):
        super().__init__(title, cb)
        self.radio_items = OrderedDict()
        for item, desc in opts:
            self.add_radio(item, desc)
        self.show()

    def add_radio(self, item, desc, group=[]):
        self.radio_items[item] = (RadioButton(group, item), desc)

    def _build_widget(self, **kwargs):
        total_items = []
        for _item in self.radio_items.keys():
            desc = AttrWrap(
                Text("  {}".format(
                    self.radio_items[_item][1])), 'input', 'input focus')
            total_items.append(
                AttrWrap(self.radio_items[_item][0], 'input', 'input focus'))
            total_items.append(AttrWrap(desc, 'input'))
            total_items.append(Divider('-'))

        self.input_lbox = ListBox(SimpleListWalker(total_items[:-1]))
        self.add_buttons()

        self.container_box_adapter = BoxAdapter(self.input_lbox,
                                                len(total_items))
        self.container_lbox = ListBox(
            [self.container_box_adapter,
             Divider(),
             self.btn_pile])

        return LineBox(
            BoxAdapter(self.container_lbox,
                       height=len(total_items) + 3),
            title=self.title)

    def submit(self, button):
        for item in self.radio_items.keys():
            _item = self.radio_items[item][0]
            if _item.get_state():
                selected_item = _item.label
        self.emit_done_signal(selected_item)


class PasswordInput(Dialog):

    """ Password input dialog
    """

    def __init__(self, title, cb):
        super().__init__(title, cb)
        self.add_input('password', 'Password: ', mask='*')
        self.add_input('confirm_password', 'Confirm Password: ',
                       mask='*')
        self.show()


class MaasServerInput(Dialog):

    """ Maas Server input dialog
    """

    def __init__(self, title, cb):
        super().__init__(title, cb)
        self.add_input('maas_server', 'MAAS Server IP: ')
        self.add_input('maas_apikey', 'MAAS API Key: ')
        self.show()


class LandscapeInput(Dialog):

    """ Landscape input dialog
    """

    def __init__(self, title, cb):
        super().__init__(title, cb)
        self.add_input('admin_email', 'Admin Email: ')
        self.add_input('admin_name', 'Admin Name: ')
        self.add_input('maas_server', 'MAAS Server IP: ')
        self.add_input('maas_apikey', 'MAAS API Key: ')
        self.show()


class DhcpRangeInput(Dialog):

    """ DHCP Range dialog
    """

    def __init__(self, low, high, title, cb):
        super().__init__(title, cb)
        self.add_input('dhcp_low', 'DHCP IP range low: ', edit_text=low)
        self.add_input('dhcp_high', 'DHCP IP range high: ', edit_text=high)
        self.add_input('static_low', 'Static IP range low (optional): ')
        self.add_input('static_high', 'Static IP range high (optional): ')
        self.show()
