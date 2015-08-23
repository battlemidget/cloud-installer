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

import logging
import os
import sys

from cloudinstall import utils
from cloudinstall.api.container import Container
from cloudinstall.core import Controller
from cloudinstall.ev import EventLoop
from cloudinstall.config import Config
from cloudinstall.ui.frame import OpenstackStatusUI

log = logging.getLogger('cloudinstall.cli.status')


class StatusCmd:
    def __init__(self, opts):
        self.opts = opts

    def main(self):
        log.info("Running: Ubuntu OpenStack Dashboard")
        if not Config.exists():
            print("No configuration found in ~/.cloud-install/config.conf\n"
                  "and no --config option passed. Please verify your\n"
                  "installation and make sure ~/.cloud-install/config.conf\n"
                  "is there and correct.")
            sys.exit(1)

        if os.path.isfile(Config.get('settings', 'pidfile')):
            print("Another instance of openstack-status is running. If you're "
                  "sure there are no other instances, please remove "
                  "~/.cloud-install/openstack.pid")
            sys.exit(1)

        # Run openstack-status within container on single installs
        out = utils.get_command_output('hostname', user_sudo=True)
        hostname = out['output'].rstrip()
        # TODO: should reach out to agent
        if Config.get('settings', 'install_type') == 'Single' and \
           Config.get('settings.single', 'container_name') not in hostname:
            log.info("Running status within container")
            Container.run_status(Config.get('settings.single',
                                            'container_name'),
                                 'openstack-status')

        ui = OpenstackStatusUI()
        ev = EventLoop(ui)

        # Create pidfile
        utils.spew(Config.get('settings', 'pidfile'),
                   str(os.getppid()),
                   utils.install_user())

        core = Controller(ui=ui, loop=ev)
        return core.start()
