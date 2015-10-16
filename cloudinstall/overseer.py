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

""" Overseer - responsible for setting up executions based on
output interface
"""

from cloudinstall.ui.notify import set_stream
from cloudinstall.ev import EventLoop


class Overseer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.notify = None
        self.loop = None

        if cfg.getopt('headless'):
            self.setup_headless()
        else:
            self.setup_urwid()

    def setup_headless(self):
        self.notify = set_stream('headless')

    def setup_urwid(self):
        self.notify = set_stream('urwid')
        self.loop = EventLoop(self.cfg)
