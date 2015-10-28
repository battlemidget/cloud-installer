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

import logging
import os

from cloudinstall.state import InstallState
from cloudinstall.controllers.install import SingleInstall
import cloudinstall.utils as utils


log = logging.getLogger('cloudinstall.install')


class InstallController:

    """ Install controller """

    def __init__(self, config):
        self.config = config
        self.install_type = None
        self.config.setopt('current_state', InstallState.RUNNING.value)

    def start(self):
        """ Start installer eventloop
        """
        self.install_type = self.config.getopt('install_type')
        # Set installed placeholder
        utils.spew(os.path.join(
            self.config.cfg_path, 'installed'), 'auto-generated')
        single = SingleInstall(self.config)
        single.do_install()
        os.remove(os.path.join(self.config.cfg_path, 'installed'))
