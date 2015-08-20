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

""" Single Install Progress View
"""

import logging
from urwid import (Pile, Columns, Text, ListBox, Divider)
from cloudinstall.view import ViewPolicy
from cloudinstall.ui.buttons import confirm_btn, cancel_btn
from cloudinstall.ui.widgets import (Password,
                                     ConfirmPassword)
from cloudinstall.ui.utils import Color, Padding


log = logging.getLogger("cloudinstall.u.v.i.singleprogress")


class SingleInstallProgressViewException(Exception):
    "Problem in Single Install Progress View"


class SingleInstallProgressView(ViewPolicy):
    def __init__(self, model, signal, tasks):
        self.model = model
        self.signal = signal
        self.tasks = tasks
        self.current_task = Text("")
        body = [
            Padding.center_79(self.current_task),
            Padding.line_break(""),
            Padding.center_20(self._build_buttons())
        ]
        super().__init__(ListBox(body))

    def _build_buttons(self):
        buttons = [
            Color.button_secondary(
                cancel_btn(on_press=self.cancel),
                focus_map="button_secondary focus")
        ]
        return Pile(buttons)

    def set_current_task(self, task):
        self.current_task.set_text(task)
        self.signal.emit_signal('refresh')

    def highlight_task_item(self, task):
        self.tasks[task] = Color.info_major(Text(self.tasks[task]))

    def _build_task_list(self):
        """ Displays the status columns for each task running """
        rows = []
        for task in self.tasks.keys():
            rows.append(Color.info_minor(Text(task)))
        return Pile(rows)
