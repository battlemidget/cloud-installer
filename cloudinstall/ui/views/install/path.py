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

""" Install Path View

Diagram:

Ubuntu OpenStack Installer - Choose Install Type

                [Single              ]  Single Install desc

                [Multi               ]  Multi Install desc

                [Landscape Autopilot ]  Autopilot install desc

                               [ Quit  ]
"""

from cloudinstall.view import ViewPolicy
from cloudinstall.ui.buttons import cancel_btn, confirm_btn
from cloudinstall.ui.utils import Color, Padding
from cloudinstall.ui.lists import SimpleList
from urwid import BoxAdapter, ListBox, Pile, Columns, Text, Divider
import logging


log = logging.getLogger("cloudinstall.u.v.i.path")


class InstallPathViewException(Exception):
    "Problem in install path selection view"


class InstallPathView(ViewPolicy):
    def __init__(self, model, signal):
        self.model = model
        self.signal = signal
        body = [
            Padding.center_79(self._build_model_inputs()),
            Padding.line_break(""),
            Padding.center_20(self._build_buttons())
        ]
        super().__init__(ListBox(body))

    def _build_buttons(self):
        self.buttons = [
            Color.button_secondary(
                cancel_btn(label="Quit",
                           on_press=self.cancel),
                focus_map="button_secondary focus")
        ]
        return Pile(self.buttons)

    def _build_model_inputs(self):
        selection = []
        rows = 0
        for label, sig, _ in self.model.get_menu():
            desc_rows, desc = self.model.get_description(label)
            rows = rows + desc_rows
            col = Columns(
                [
                    ("weight", 0.4, Color.button_primary(
                        confirm_btn(label=label,
                                    on_press=self.confirm),
                        focus_map="button_primary focus")),
                    Text(desc)
                ], dividechars=1)
            selection.append(col)
            selection.append(Divider('-', 1, 1))
        selection = selection[:-1]
        return BoxAdapter(SimpleList(selection),
                          height=len(selection) + 2 + rows)

    def confirm(self, result):
        self.signal.emit_signal(self.model.get_signal_by_name(result.label))

    def cancel(self, button):
        raise SystemExit("Exiting Installer.")
