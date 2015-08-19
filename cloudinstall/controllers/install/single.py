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

""" Single Install Controller """

import logging
import os
import json

from cloudinstall import utils, netutils
from cloudinstall.api.container import (Container,
                                        NoContainerIPException,
                                        ContainerRunException)
from cloudinstall.controller import ControllerPolicy
from cloudinstall.models import SingleInstallModel
from cloudinstall.api.install import SingleInstallAPI
from cloudinstall.ui.views.install import SingleInstallView


log = logging.getLogger('cloudinstall.c.i.single')


class SingleInstallControllerException(Exception):
    pass


class SingleInstallController(ControllerPolicy):

    def __init__(self, ui, signal):
        self.ui = ui
        self.signal = signal
        self.model = SingleInstallModel()
        self.api = SingleInstallAPI()

    def single(self):
        """ Start prompting for Single Install information
        """
        title = "Single installation"
        excerpt = ("Please fill out the input fields to continue with "
                   "the single installation.")
        self.ui.set_header(title, excerpt)
        self.ui.set_body(SingleInstallView(self.model,
                                           self.signal))

    # def read_container_status(self):
    #     return check_output("lxc-info -n {} -s "
    #                         "|| true".format(self.container_name),
    #                         shell=True, stderr=STDOUT).decode('utf-8')

    # def read_cloud_init_output(self):
    #     try:
    #         s = Container.run(self.container_name, 'tail -n 10 '
    #                           '/var/log/cloud-init-output.log')
    #         return s.replace('\r', '')
    #     except Exception:
    #         return "Waiting..."

    # def set_progress_output(self, output):
    #     self.progress_output = output

    # def read_progress_output(self):
    #     return self.progress_output

    # def read_juju_log(self):
    #     try:
    #         return Container.run(self.container_name, 'tail -n 10 '
    #                              '/var/log/juju-ubuntu-local'
    #                              '/all-machines.log')
    #     except Exception:
    #         return "Waiting..."

    # def _set_apt_proxy(self):
    #     self.api.set_apt_proxy()
    #     self.api.set_apts_proxy()

    # def cloud_init_finished(self, tries, maxlenient=20):
    #     """checks cloud-init result.json in container to find out status

    #     For the first `maxlenient` tries, it treats a container with
    #     no IP and SSH errors as non-fatal, assuming initialization is
    #     still ongoing. Afterwards, will raise exceptions for those
    #     errors, so as not to loop forever.

    #     returns True if cloud-init finished with no errors, False if
    #     it's not done yet, and raises an exception if it had errors.

    #     """
    #     cmd = 'sudo cat /run/cloud-init/result.json'
    #     try:
    #         result_json = Container.run(self.container_name, cmd)

    #     except NoContainerIPException as e:
    #         log.debug("Container has no IPs according to lxc-info. "
    #                   "Will retry.")
    #         return False

    #     except ContainerRunException as e:
    #         _, returncode = e.args
    #         if returncode == 255:
    #             if tries < maxlenient:
    #                 log.debug("Ignoring initial SSH error.")
    #                 return False
    #             raise e
    #         if returncode == 1:
    #             # the 'cat' did not find the file.
    #             if tries < 1:
    #                 log.debug("Waiting for cloud-init status result")
    #             return False
    #         else:
    #             log.debug("Unexpected return code from reading "
    #                       "cloud-init status in container.")
    #             raise e

    #     if result_json == '':
    #         return False

    #     try:
    #         ret = json.loads(result_json)
    #     except Exception as e:
    #         if tries < maxlenient + 10:
    #             log.debug("exception trying to parse '{}'"
    #                       " - retrying".format(result_json))
    #             return False

    #         log.error(str(e))
    #         log.debug("exception trying to parse '{}'".format(result_json))
    #         raise e

    #     errors = ret['v1']['errors']
    #     if len(errors):
    #         log.error("Container cloud-init finished with "
    #                   "errors: {}".format(errors))
    #         raise Exception("Top-level container OS did not initialize "
    #                         "correctly.")
    #     return True

    # def run(self):
    #     self.ensure_nested_kvm()
    #     self.display_controller.status_info_message("Building environment")
    #     if os.path.exists(self.container_abspath):
    #         raise Exception("Container exists, please uninstall or kill "
    #                         "existing cloud before proceeding.")

    #     # Step 1 --------------------------------------------------------------
    #     utils.ssh_genkey()

    #     # Step 2 --------------------------------------------------------------
    #     self._set_apt_proxy()

    #     # Step 3 --------------------------------------------------------------
    #     self.api.set_userdata()

    #     # Step 4 --------------------------------------------------------------
    #     utils.render_charm_config(self.config)

    #     # Step 5 --------------------------------------------------------------
    #     self.api.set_juju()

    #     # Step 6 --------------------------------------------------------------
    #     self.api.set_perms()

    #     # Step 7 --------------------------------------------------------------
    #     #  (Async)
    #     self.api.create_container()

    #     # Step 8 --------------------------------------------------------------
    #     lxc_logfile = os.path.join(self.config.cfg_path, 'lxc.log')
    #     self.api.start_container(lxc_logfile)
    #     Container.wait_checked(self.container_name, lxc_logfile)

    #     # Step 9 --------------------------------------------------------------
    #     lxc_network = self.api.set_lxc_net_config()
    #     self.api.set_static_route(lxc_network)

    #     # Step 10 -------------------------------------------------------------
    #     #  Copy over host ssh keys
    #     Container.cp(self.container_name,
    #                  os.path.join(utils.install_home(), '.ssh/id_rsa*'),
    #                  '.ssh/.')

    #     # Step 11 -------------------------------------------------------------
    #     #  Install local copy of openstack installer if provided
    #     upstream_deb = self.config.getopt("upstream_deb")
    #     if upstream_deb:
    #         self.api.copy_upstream_deb(upstream_deb)
    #         self.api.install_upstream_deb()

    #     # Step 12 -------------------------------------------------------------
    #     #  Stop before we attempt to access container
    #     if self.config.getopt('install_only'):
    #         log.info("Done installing, stopping here per --install-only.")
    #         self.config.setopt('install_only', True)
    #         self.loop.exit(0)

    #     # Step 13 -------------------------------------------------------------
    #     #  Update jujus no-proxy setting if applicable
    #     if self.config.getopt('http_proxy') or \
    #        self.config.getopt('https_proxy'):
    #         log.info("Updating juju environments for proxy support")
    #         lxc_net = self.config.getopt('lxc_network')
    #         self.config.update_environments_yaml(
    #             key='no-proxy',
    #             val='{},localhost,{}'.format(
    #                 Container.ip(self.container_name),
    #                 netutils.get_ip_set(lxc_net)))

    #     # Step 14 -------------------------------------------------------------
    #     #  start the party
    #     cloud_status_bin = ['openstack-status']
    #     Container.run(self.container_name,
    #                   "{0} juju --debug bootstrap".format(
    #                       self.config.juju_home(use_expansion=True)),
    #                   use_ssh=True, output_cb=self.set_progress_output)
    #     Container.run(
    #         self.container_name,
    #         "{0} juju status".format(
    #             self.config.juju_home(use_expansion=True)),
    #         use_ssh=True)

    #     self.display_controller.status_info_message(
    #         "Starting cloud deployment")
    #     Container.run_status(
    #         self.container_name, " ".join(cloud_status_bin), self.config)
