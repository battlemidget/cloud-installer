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

""" Machine widget, easily display hardware attributes
and updates
"""
from urwid import WidgetWrap, Text


class MachineWidget(WidgetWrap):
    def __init__(self, unit, charm_class, hwinfo):
        self.hwinfo = hwinfo
        self.container = Text(self.hwinfo['container'])
        self.machine = Text(self.hwinfo['machine'])
        self.arch = Text(self.hwinfo['arch'])
        self.cpu_cores = Text(self.hwinfo['cpu_cores'])
        self.mem = Text(self.hwinfo['mem'])
        self.storage = Text(self.hwinfo['storage'])
        self.display_name = Text(charm_class.diplay_name)
        self.agent_state = Text(unit.agent_state)
        self.public_address = Text(unit.public_address)
        self.icon = None
