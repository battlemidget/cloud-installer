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

from urwid import (WidgetWrap, Pile, Text, AttrWrap, Columns)
from .lists import SimpleList
from .utils import Color, Padding


class Header(WidgetWrap):
    """ Header Widget
    This widget uses the style key `frame_header`
    :param str title: Title of Header
    :returns: Header()
    """

    def __init__(self, title="Ubuntu OpenStack Installer"):
        widgets = [
            Color.frame_header(Text(title)),
            Padding.line_break("")
        ]
        super().__init__(Pile(widgets))


class Footer(WidgetWrap):

    """Displays text."""

    INFO = "[INFO]"
    ERROR = "[ERROR]"
    ARROW = " \u21e8 "

    def __init__(self, text=''):
        self._pending_deploys = Text('')
        self._status_line = Text(text)
        self._horizon_url = Text('')
        self._jujugui_url = Text('')
        self._openstack_rel = Text('')
        self._status_extra = self._build_status_extra()
        status = Pile([self._pending_deploys,
                       self._status_line, self._status_extra])
        super().__init__(status)

    def _build_status_extra(self):
        status = []
        status.append(Pile([self._horizon_url, self._jujugui_url]))
        status.append(('pack', self._openstack_rel))
        return AttrWrap(Columns(status), 'status_extra')

    def set_openstack_rel(self, text="Icehouse (2014.1.1)"):
        """ Updates openstack release text
        """
        return self._openstack_rel.set_text(text)

    def set_dashboard_url(self, ip=None, user=None, password=None):
        """ sets horizon dashboard url """
        text = "Openstack Dashboard: "
        if not ip:
            text += "(pending)"
        else:
            text += "https://{}/horizon l:{} p:{}".format(
                ip, user, password)
        return self._horizon_url.set_text(text)

    def set_jujugui_url(self, ip=None):
        """ sets juju gui url """
        text = "{0:<21}".format("JujuGUI:")
        if not ip:
            text += "(pending)"
        else:
            text += "https://{}/".format(ip)
        return self._jujugui_url.set_text(text)

    def message(self, text):
        """Write `text` on the footer."""
        self._status_line.set_text(text)

    def error_message(self, text):
        self.message([('error', self.ERROR),
                      ('default', self.ARROW + text)])

    def info_message(self, text):
        self.message([('info', self.INFO),
                      ('default', self.ARROW + text)])

    def set_pending_deploys(self, pending_deploys):
        if len(pending_deploys) > 0:
            msg = "Pending deploys: " + ", ".join(pending_deploys)
            self._pending_deploys.set_text(msg)
        else:
            self._pending_deploys.set_text('')

    def clear(self):
        """Clear the text."""
        self._w.set_text('')


class InstallMenu(WidgetWrap):

    def __init__(self):
        menu = [
            Color.body(Text("(Q)uit"))
        ]
        super().__init__(Columns(menu))


class Body(WidgetWrap):
    """ Body widget
    """

    def __init__(self):
        text = [Text("")]
        w = (SimpleList(text))
        super().__init__(w)
