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

from urwid import WidgetWrap, Text, Pile
from cloudinstall.ui.utils import Color


class Status(WidgetWrap):
    def __init__(self, msg="", align="center"):
        self.message = Text(msg, align)
        super().__init__(self.message)

    def __get__(self, obj, objtyp):
        return self.message.get_text()

    def __set__(self, obj, msg):
        self.message.set_text(msg)


class StatusBar(WidgetWrap):

    """Displays text."""

    def __init__(self, stream):
        """
        :params stream: Notification stream to connect to
        """
        self.status_line = stream

        self.pending_deploys = Status()
        self.horizon_url = Status(align="left")
        self.jujugui_url = Status(align="left")
        super().__init__(Pile([self.pending_deploys,
                               self._build_status_extra()]))

    def _build_status_extra(self):
        return Color.frame_footer(
            Pile([
                self.horizon_url,
                self.jujugui_url,
                self.status_line
            ]))

    def set_dashboard_url(self, ip=None, user=None, password=None):
        """ sets horizon dashboard url """
        text = "Horizon: "
        if not ip:
            text += "(pending)"
        else:
            text += "https://{}/horizon l:{} p:{}".format(
                ip, user, password)
        self.horizon_url = text

    def set_jujugui_url(self, ip=None):
        """ sets juju gui url """
        if not ip:
            return
        text = "JujuGUI: "
        text += "https://{}/".format(ip)
        self.jujugui_url = text

    def set_pending_deploys(self, pending_deploys):
        if len(pending_deploys) > 0:
            msg = "Pending deploys: " + ", ".join(pending_deploys)
            self.pending_deploys = msg
        else:
            self.pending_deploys = ''
