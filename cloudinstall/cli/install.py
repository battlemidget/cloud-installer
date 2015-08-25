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

""" CLI for installing Ubuntu OpenStack """

import sys
import os
import logging
import cloudinstall.utils as utils
from cloudinstall.ui.frame import OpenstackInstallUI
from cloudinstall.controllers.installbase import InstallController
from cloudinstall.ev import EventLoop

CFG_DIR = os.path.join(utils.install_home(), '.cloud-install')
CFG_FILE = os.path.join(CFG_DIR, 'config.conf')

log = logging.getLogger('cloudinstall.cli.install')


class InstallCmd:
    def __init__(self, opts):
        self.opts = opts

    def set_config_defaults(self, config):
        config['settings'] = {
            'pidfile': os.path.join(CFG_DIR, 'openstack.pid'),
            'cfg_path': CFG_DIR,
            'cfg_file': CFG_FILE,
            'placements_file': os.path.join(CFG_DIR, 'placements.yaml'),
            'install_only': "no",
            'headless': "no"
        }
        config['settings.juju'] = {
            'path': os.path.join(CFG_DIR, 'juju'),
            'home': os.path.join(CFG_DIR, 'juju'),
            'home_expanded': "~/.cloud-install/juju",
            'environments_path': os.path.join(CFG_DIR, 'juju',
                                              'environments'),
            'environments_yaml': os.path.join(CFG_DIR, 'juju',
                                              'environments.yaml'),
            'series': "trusty",
        }
        config['settings.single'] = {
            'container_name': 'openstack-single-{}'.format(
                utils.install_user())
        }
        return config

    def main(self):
        if os.geteuid() != 0:
            sys.exit(
                "Installing a cloud requires root privileges. Rerun with sudo")

        log.info("Running: Ubuntu OpenStack Install")

        # New install, write default config
        if not os.path.isfile(CFG_FILE):
            try:
                config = utils.read_ini('/usr/share/openstack/config.conf')
            except Exception as e:
                print(e)
                sys.exit(1)
            config = self.set_config_defaults(config)
            utils.write_ini(config)
        elif os.path.isfile(CFG_FILE) and not self.opts.advanced:
            msg = ("An existing configuration was found at "
                   "~/.cloud-install/config.conf. This could indicate an "
                   "existing install. If you are wanting to do further "
                   "customizations before install please re-try with \n\n"
                   "$ sudo openstack-install --advanced\n\n"
                   "This will bring up the installer in advanced "
                   "configuration mode and allow you to fine-tune "
                   "the install further.")
            print(msg)
            sys.exit(1)
        else:
            config = utils.read_ini_existing()
        log.debug("Current Config: {}".format(dict(config)))
        if self.opts.uninstall:
            msg = (
                "Warning:\n\nThis will uninstall OpenStack and "
                "make a best effort to return the system back "
                "to its original state.\n\n"
                "If you haven't backed up your ~/.cloud-install/config.conf "
                "nows a good time to do so before proceeding.")
            print(msg)
            yn = input("Proceed? [y/N] ")

            if "y" in yn or "Y" in yn:
                print("Restoring system to last known state.")
                os.execl('/usr/bin/openstack-uninstall', '')
            else:
                print("Uninstall cancelled.")
                sys.exit(1)

        if sys.getdefaultencoding() != 'utf-8':
            print(
                "Ubuntu OpenStack Installer requires unicode support. "
                "Please enable this on the system running the installer.\n\n")
            print("Example:\n")
            print("  export LC_ALL=en_US.UTF-8")
            print("  export LANG=en_US.UTF-8")
            print("  export LANGUAGE=en_US.UTF-8")
            sys.exit(1)

        if self.opts.advanced:
            config['runtime'] = {}
            config['runtime']['advanced_config'] = "yes"
            utils.write_ini(config)

        # # TODO: move this into agent
        # juju_path = config['settings.juju']['path']
        # if not os.path.exists(juju_path):
        #     log.info("Creating juju directories: {}".format(juju_path))
        #     os.makedirs(juju_path)
        #     utils.chown(juju_path, utils.install_user(), utils.install_user())

        # if os.path.isfile(os.path.join(CFG_DIR, 'installed')):
        #     msg = ("\n\nError:\n\n"
        #            "Previous installation detected. Did you mean to run "
        #            "openstack-status instead? \n"
        #            "If attempting to re-install please run "
        #            "    $ sudo openstack-install -u\n\n")
        #     print(msg)
        #     sys.exit(1)
        # out = utils.get_command_output(
        #     '{} juju api-endpoints'.format(
        #         config['settings.juju']['home_expanded']), user_sudo=True)
        # if out['status'] == 0:
        #     msg = ("Existing OpenStack environment detected. Please destroy "
        #            "that environment before proceeding with a new install.")
        #     print(msg)
        #     sys.exit(1)

        ui = OpenstackInstallUI()

        # Setup event loop
        ev = EventLoop(ui)

        return InstallController(ui=ui, loop=ev).start()
