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

""" UrwidStream - urwid notification to Installer """

from __future__ import unicode_literals
import logging

log = logging.getLogger('cloudinstall.ui.urwidstream')

from cloudinstall.policies import NotifyPolicy
from cloudinstall.ui.widgets import Status


class UrwidStream(NotifyPolicy):
    INFO = "[INFO]"
    ERROR = "[ERROR]"
    ARROW = " \u21e8 "

    def __init__(self):
        self.w = Status()

    def info(self, msg):
        super().info(msg)
        self.w = [('status_info', self.INFO),
                  self.ARROW + msg]

    def error(self, msg):
        super().error(msg)
        self.w = [('status_error', self.ERROR),
                  self.ARROW + msg]

    def __repr__(self):
        return "<Ubuntu OpenStack Installer Urwid Stream>"
