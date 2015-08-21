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
"""

import logging
from urwid import (Pile, Columns, Text, ListBox, Divider)
from cloudinstall.view import ViewPolicy
from cloudinstall.ui.buttons import confirm_btn, cancel_btn
from cloudinstall.ui.widgets import (Password,
                                     ConfirmPassword,
                                     PlainStringEditor)
from cloudinstall.ui.utils import Color, Padding


log = logging.getLogger("cloudinstall.u.v.i.single")


class SingleInstallViewException(Exception):
    "Problem in Single Install View"


class SingleInstallView(ViewPolicy):
    def __init__(self, model, signal, advanced=False):
        self.model = model
        self.signal = signal
        self.confirm_password = ConfirmPassword()
        self.inputs = {
            'settings': {
                'password': Password(),
                'install_only': PlainStringEditor(edit_text="no"),
                'use_upstream_ppa': PlainStringEditor(edit_text="no"),
                'upstream_ppa': PlainStringEditor(),
                'apt_mirror': PlainStringEditor(),
                'upstream_deb': PlainStringEditor()
            },
            'settings.proxy': {
                'http_proxy': PlainStringEditor(),
                'https_proxy': PlainStringEditor(),
                'apt_proxy': PlainStringEditor(),
                'apt_https_proxy': PlainStringEditor(),
                'no_proxy': PlainStringEditor()
            },
            'settings.openstack': {
                'tip': PlainStringEditor(edit_text="no"),
                'release': PlainStringEditor(edit_text="kilo"),
                'use_next_charms': PlainStringEditor(edit_text="no"),
                'use_nclxd': PlainStringEditor(edit_text="no")
            },
            'settings.image_sync': {
                'release': PlainStringEditor(edit_text="trusty"),
                'arch': PlainStringEditor(edit_text="amd64")
            }
        }

        self.password_info = Text("Enter a new password")
        body = [
            Padding.center_79(self.password_info),
            Padding.center_79(
                Color.info_minor(Text("This is your password to be used "
                                      "when logging into OpenStack services "
                                      "such as Horizon"))),
            Padding.center_79(Divider('-', 0, 1)),
            Padding.center_50(self._build_form()),
            Padding.line_break("")
        ]
        if advanced:
            body.append(self._build_form_advanced())
            body.append(Padding.line_break(""))
        body.append(Padding.center_20(self._build_buttons()))
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

    def gen_inputs(self, label, desc, key):
        rows = []
        rows.append(Padding.center_79(Text(label)))
        rows.append(Padding.center_79(
            Color.info_minor(Text(desc))))
        rows.append(Padding.center_79(Divider('-', 0, 1)))
        for k, v in self.inputs[key].items():
            if k == 'password':
                continue
            rows.append(Padding.center_50(Columns([
                ("weight",
                 0.2,
                 Text(k.replace("_", " ").capitalize(),
                      align="right")),
                ("weight",
                 0.3,
                 Color.string_input(v, focus_map="string_input focus"))
            ], dividechars=4)))
        return Pile(rows)

    def _build_form_advanced(self):
        sections = [
            ("Settings", "Additional settings for this installer", "settings"),
            ("Proxy", "Define your HTTP/S APT/S proxy settings",
             "settings.proxy"),
            ("OpenStack", "Settings specific to how OpenStack is deployed",
             "settings.openstack"),
            ("Glance", "Settings for the Glance Simplestreams Sync charm",
             "settings.image_sync")
        ]
        return Pile([self.gen_inputs(label, desc, k)
                     for label, desc, k in sections])

    def _build_form(self):
        return Pile([
            Columns([
                ("weight", 0.2, Text("Password", align="right")),
                ("weight", 0.3,
                 Color.string_input(self.inputs['settings']['password'],
                                    focus_map="string_input focus"))
            ], dividechars=4),
            Columns([
                ("weight", 0.2, Text("Confirm Password", align="right")),
                ("weight", 0.3, Color.string_input(
                    self.confirm_password,
                    focus_map="string_input focus"))
            ], dividechars=4)
        ])

    def _set_password_info(self, msg=None):
        text = self.password_info
        if msg:
            self.password_info.set_text((text, ('error_major', msg)))
            self.signal.emit_signal('refresh')

    def done(self, button):
        password = self.inputs['settings']['password'].value
        confirm_password = self.confirm_password.value

        # Validate proxy ------------------------------------------------------
        http_proxy = self.inputs['settings.proxy']['http_proxy'].value
        https_proxy = self.inputs['settings.proxy']['https_proxy'].value
        if http_proxy and not https_proxy:
            self.inputs['settings.proxy']['https_proxy'].set_result(
                http_proxy)
        if https_proxy and not http_proxy:
            self.inputs['settings.proxy']['http_proxy'].set_result(
                http_proxy)

        # Validate Password ---------------------------------------------------
        if password != confirm_password:
            self._set_password_info("Passwords do not match.")
        elif not password or not confirm_password:
            self._set_password_info("Password can not be blank")
        elif password.isdigit():
            self._set_password_info(
                "Password must contain a mix of letters and number")
        else:
            self.signal.emit_signal('install:single:start', self.inputs)

    def cancel(self, button):
        self.signal.emit_signal(self.model.get_previous_signal)
