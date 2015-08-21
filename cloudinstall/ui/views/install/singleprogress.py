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
from urwid import (Pile, Text, ListBox, Columns)
from cloudinstall.view import ViewPolicy
from cloudinstall.ui.buttons import cancel_btn
from cloudinstall.ui.utils import Color, Padding


log = logging.getLogger("cloudinstall.u.v.i.singleprogress")


class SingleInstallProgressViewException(Exception):
    "Problem in Single Install Progress View"


class SingleInstallProgressView(ViewPolicy):
    def __init__(self, model, signal):
        self.model = model
        self.signal = signal
        self.current_task = Text("")
        body = [
            Padding.center_79(Columns([
                ("weight", 0.2, Text("Progress:")),
                self.current_task
            ], dividechars=5)),
        ]
        super().__init__(ListBox(body))

    def set_current_task(self, task):
        self.current_task.set_text(task)
        self.signal.emit_signal('refresh')

    def highlight_task_item(self, task):
        return Color.info_major(Text(task))
