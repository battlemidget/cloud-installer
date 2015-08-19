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
from urwid import Pile, Columns, Text, ListBox
from cloudinstall.view import ViewPolicy
from cloudinstall.ui.buttons import confirm_btn, cancel_btn
from cloudinstall.ui.widgets import (Password,
                                     ConfirmPassword,
                                     OpenstackRelease)
from cloudinstall.ui.utils import Color, Padding


log = logging.getLogger("cloudinstall.u.v.i.single")


class SingleInstallViewException(Exception):
    "Problem in Single Install View"


class SingleInstallView(ViewPolicy):
    def __init__(self, model, signal):
        self.model = model
        self.signal = signal
        body = [
            Padding.center_79(self._build_form()),
            Padding.line_break(""),
            Padding.center_79(self._build_buttons())
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
        self.password = Password()
        self.confirm_password = ConfirmPassword()
        self.openstack_release = OpenstackRelease()

        password_input = Columns([("weight", 0.2, Text("Password")),
                                  self.password])
        confirm_password_input = Columns([
            ("weight", 0.2, Text("Confirm Password")),
            self.confirm_password])
        openstack_release_input = Columns([
            ("weight", 0.2, Text("OpenStack Release")),
            self.openstack_release])

        return Pile([
            password_input,
            confirm_password_input,
            openstack_release_input
        ])

    def done(self, result):
        result = {
            "password": self.password.value,
            "openstack_release": self.openstack_release.value
        }
        self.signal.emit_signal('install:single:start', result)

    # def _build_status_indicators(self):
    #     """ Displays the status columns for each task running """
    #     col = [
    #         ("weight", 0.2, Color.body(Text("Initializing Environment"))),
    #         ("weight", 0.2, Color.body(Text("Creating Container"))),
    #         ("weight", 0.2, Color.body(Text("Initializing Container"))),
    #         ("weight", 0.2, Color.body(Text("Installing Dependencies"))),
    #         ("weight", 0.2, Color.body(Text("Bootstrapping Juju")))
    #     ]
    #     return Columns(col)
