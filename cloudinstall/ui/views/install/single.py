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

""" Single Install View

Diagram:

Ubuntu OpenStack Installer - Single Install

                  Performing Single Install...

[## Initializing Env ##][Creating Container][Initializing Container]

[#### Progress 20%                                                 ]

----------------------------- Output -------------------------------

Console logging...
etc etc...


"""

import logging
from urwid import (Pile, Columns, Text, ListBox, Divider)
from cloudinstall.view import ViewPolicy
from cloudinstall.ui.buttons import confirm_btn, cancel_btn
from cloudinstall.ui.widgets import (Password,
                                     ConfirmPassword)
from cloudinstall.ui.utils import Color, Padding


log = logging.getLogger("cloudinstall.u.v.i.single")


class SingleInstallViewException(Exception):
    "Problem in Single Install View"


class SingleInstallView(ViewPolicy):
    def __init__(self, model, signal):
        self.model = model
        self.signal = signal
        self.password = Password()
        self.confirm_password = ConfirmPassword()
        self.password_info = Text("Enter a new password:")
        body = [
            Padding.center_79(self.password_info),
            Padding.center_79(
                Color.info_minor(Text("This is your password to be used "
                                      "when logging into Horizon"))),
            Padding.center_79(Divider('-', 0, 1)),
            Padding.center_50(self._build_form()),
            Padding.line_break(""),
            Padding.center_20(self._build_buttons())
        ]
        super().__init__(ListBox(body))

    def _build_buttons(self):
        buttons = [
            Color.button_secondary(
                confirm_btn(on_press=self.done),
                focus_map="button_secondary focus"),
            Color.button_secondary(
                cancel_btn(on_press=self.cancel),
                focus_map="button_secondary focus")
        ]
        return Pile(buttons)

    def _build_form(self):
        password_input = Columns([
            ("weight", 0.2, Text("Password", align="right")),
            ("weight", 0.3, Color.string_input(self.password))
        ], dividechars=4)
        confirm_password_input = Columns([
            ("weight", 0.2, Text("Confirm Password", align="right")),
            ("weight", 0.3, Color.string_input(self.confirm_password))
        ], dividechars=4)
        return Pile([
            password_input,
            confirm_password_input
        ])

    def _set_password_info(self, msg):
        existing_text = self.password_info.get_text()[0]
        self.password_info.set_text(
            "{}: {}".format(existing_text, msg))

    def done(self, result):
        result = {
            "password": self.password.value,
            "confirm_password": self.confirm_password.value
        }
        if result['password'] != result['confirm_password']:
            self._set_password_info("Passwords do not match.")
        else:
            self.signal.emit_signal('install:single:start', result)

    def cancel(self, button):
        self.signal.emit_signal(self.model.get_previous_signal)
