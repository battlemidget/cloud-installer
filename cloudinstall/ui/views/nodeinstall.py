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

from urwid import (WidgetWrap, Text, Columns, Filler, Pile)
import random
from cloudinstall.ui.utils import (Color, Padding)


class NodeInstallWaitView(WidgetWrap):

    def __init__(self,
                 message="Installer is initializing nodes. Please wait."):
        self.message = message
        super().__init__(self._build_node_waiting())

    def _build_node_waiting(self):
        """ creates a loading screen if nodes do not exist yet """
        text = [Padding.line_break(""),
                Text(self.message, align="center"),
                Padding.line_break("")]

        load_box = [Color.pending_icon_on(Text("\u2581",
                                               align="center")),
                    Color.pending_icon_on(Text("\u2582",
                                               align="center")),
                    Color.pending_icon_on(Text("\u2583",
                                               align="center")),
                    Color.pending_icon_on(Text("\u2584",
                                               align="center")),
                    Color.pending_icon_on(Text("\u2585",
                                               align="center")),
                    Color.pending_icon_on(Text("\u2586",
                                               align="center")),
                    Color.pending_icon_on(Text("\u2587",
                                               align="center")),
                    Color.pending_icon_on(Text("\u2588",
                                               align="center"))]

        # Add loading boxes
        random.shuffle(load_box)
        loading_boxes = []
        loading_boxes.append(('weight', 1, Text('')))
        for i in load_box:
            loading_boxes.append(('pack',
                                  load_box[random.randrange(len(load_box))]))
        loading_boxes.append(('weight', 1, Text('')))
        loading_boxes = Columns(loading_boxes)

        return Filler(Pile(text + [loading_boxes]),
                      valign="middle")


