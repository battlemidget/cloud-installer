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

""" An exception View equipped with traceback,
log output, and where to file a bug.
"""

import logging
from urwid import (Pile, Text, ListBox)
from cloudinstall.view import ViewPolicy
from cloudinstall.ui.buttons import cancel_btn
from cloudinstall.ui.utils import Color, Padding


log = logging.getLogger("cloudinstall.u.v.error")


class ErrorViewException(Exception):
    "Problem in Error  View"


class ErrorView(ViewPolicy):
    def __init__(self, model, signal, error):
        self.model = model
        self.signal = signal
        self.error = error
        body = [
            Padding.center_95(
                Text("Oops, there was a problem with your install:")),
            Padding.line_break(""),
            Padding.center_79(
                Color.error_major(Text("Reason: {}".format(self.error)))),
            Padding.line_break(""),
            Padding.center_95(
                Text("You'll need to press CTRL-C to exit the installation.")),
            Padding.line_break(""),
            Padding.center_20(self._build_buttons())
        ]
        super().__init__(ListBox(body))

    def _build_buttons(self):
        buttons = [
            Color.button_secondary(
                cancel_btn(label="Quit", on_press=self.cancel),
                focus_map="button_secondary focus")
        ]
        return Pile(buttons)

    def cancel(self, button):
        self.signal.emit_signal('quit')
