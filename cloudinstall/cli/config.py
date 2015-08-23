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

""" Small utility to print current installer configuration settings """

import sys
from cloudinstall.config import Config


class ConfigCmd:
    def __init__(self, opts):
        self.opts = opts

    def main(self):
        if not Config.exists():
            print("No existing config file found.")
            sys.exit(1)
        if not self.opts.section:
            print("No --section found")
            sys.exit(1)
        if not self.opts.option:
            print("No --option found")
            sys.exit(1)
        val = Config.get(self.opts.section, self.opts.option)
        print(val)
        sys.exit(0)
