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
from subprocess import check_output, STDOUT
from tornado.gen import coroutine
from cloudinstall import utils, netutils
from cloudinstall.api.container import Container
from cloudinstall.controller import ControllerPolicy
from cloudinstall.models import SingleInstallModel
from cloudinstall.api.install import SingleInstallAPI
from cloudinstall.ui.views.install import (SingleInstallView,
                                           SingleInstallProgressView)
from cloudinstall.ui.views import ErrorView


log = logging.getLogger('cloudinstall.c.i.single')


class SingleInstallControllerException(Exception):
    pass


class SingleInstallController(ControllerPolicy):

    def __init__(self, ui, signal, config):
        self.ui = ui
        self.signal = signal
        self.config = config
        self.model = SingleInstallModel()
        self.api = SingleInstallAPI(self.config)
        self.container_name = self.config['settings.single']['container_name']

    def single(self):
        """ Start prompting for Single Install information
        """
        # TODO: Add exception view
        # if os.path.exists(self.container_abspath):
        #     raise Exception("Container exists, please uninstall or kill "
        #                     "existing cloud before proceeding.")

        title = "Single installation"
        excerpt = ("Please fill out the input fields to continue with "
                   "the single installation.")
        self.ui.set_header(title, excerpt)
        self.ui.set_body(SingleInstallView(self.model,
                                           self.signal))

    def _read_container_status(self):
        return check_output("lxc-info -n {} -s "
                            "|| true".format(self.container_name),
                            shell=True, stderr=STDOUT).decode('utf-8')

    def _read_cloud_init_output(self):
        try:
            s = Container.run(self.container_name, 'tail -n 10 '
                              '/var/log/cloud-init-output.log')
            return s.replace('\r', '')
        except Exception:
            return "Waiting..."

    def _read_juju_log(self):
        try:
            return Container.run(self.container_name, 'tail -n 10 '
                                 '/var/log/juju-ubuntu-local'
                                 '/all-machines.log')
        except Exception:
            return "Waiting..."

    def print_task(self, msg=None):
        if msg:
            log.debug("Task: {}".format(msg))
            self.sp_view.set_current_task(msg)
        # self.ui.set_body(ErrorView(self.model,
        #                            self.signal,
        #                            e))

    @coroutine
    def ensure_kvm(self):
        self.print_task("1 ensuring kvm loaded")
        try:
            yield self.api.ensure_nested_kvm_async()
        except:
            log.error("problem with ensure kvm")
        self.ssh_genkey()

    @coroutine
    def ssh_genkey(self):
        self.print_task("2 genkey")
        try:
            yield utils.ssh_genkey_async()
        except:
            log.error("problem with genkey")
        self.set_apt_proxy()

    @coroutine
    def set_apt_proxy(self):
        self.print_task("3 apt proxy")
        yield self.api.set_apt_proxy_async()
        yield self.api.set_apts_proxy_async()
        self.set_userdata()

    @coroutine
    def set_userdata(self):
        self.print_task("4 userdata")
        yield self.api.set_userdata_async()
        self.set_charmconfig()

    @coroutine
    def set_charmconfig(self):
        self.print_task("5 charmconfig")
        yield utils.render_charm_config_async(self.config)
        self.set_juju()

    @coroutine
    def set_juju(self):
        self.print_task("6 juju")
        yield self.api.set_juju_async()
        self.set_perms()

    @coroutine
    def set_perms(self):
        self.print_task("7 perms")
        yield self.api.set_perms_async()
        self.set_create_container()

    @coroutine
    def set_create_container(self):
        self.print_task("8 create container")
        try:
            yield self.api.create_container_async()
            self.set_copy_host_ssh()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_copy_host_ssh(self):
        self.print_task("13 copy host ssh")
        yield self.api.copy_host_ssh_to_container_async()
        self.set_upstream_deb()

    @coroutine
    def set_upstream_deb(self):
        self.print_task("14 upstream deb")
        upstream_deb = self.config['settings.single']['upstream_deb_path']
        if upstream_deb:
            yield self.api.copy_upstream_deb_async()
            yield self.api.install_upstream_deb_async()
        self.set_install_only()

    def set_install_only(self):
        self.print_task("15 install only")
        # Close out loop if install only
        self.print_task("Checking if we should stop for --install-only")
        if self.config['settings']['install_only']:
            log.info("Done installing, stopping here per --install-only.")
            self.config['settings']['install_only'] = "yes"
            utils.write_ini(self.config)
            self.signal.emit_signal('quit')
        return self.set_juju_proxy()

    def set_juju_proxy(self):
        self.print_task("16 juju proxy")
        #  Update jujus no-proxy setting if applicable
        self.print_task("Writing juju proxy settings if applicable")
        proxy = self.config['settings.proxy']
        if proxy['http_proxy'] or proxy['https_proxy']:
            log.info("Updating juju environments for proxy support")
            lxc_net = self.config['settings.single']['lxc_network']
            utils.update_environments_yaml(
                key='no-proxy',
                val='{},localhost,{}'.format(
                    Container.ip(self.container_name),
                    netutils.get_ip_set(lxc_net)))
        return self.start_status()

    def start_status(self):
        self.print_task("17 Starting status screen.")
        # Save our config before moving on to dashboard
        utils.write_ini(self.config)
        cloud_status_bin = ['openstack-status']
        juju_home = self.config['settings.juju']['home_expanded']
        Container.run(self.container_name,
                      "{0} juju --debug bootstrap".format(juju_home),
                      use_ssh=True)
        Container.run(
            self.container_name,
            "{0} juju status".format(juju_home),
            use_ssh=True)
        Container.run_status(
            self.container_name, " ".join(cloud_status_bin), self.config)

    def single_start(self, opts):
        """ Start single install, processing opts
        """
        self.config['settings']['password'] = opts['password']

        log.info("Password entered, saving {}".format(
            self.config['settings']['password']))
        log.info("Starting a single installation.")

        title = "Single installation progress"
        excerpt = ("Currently installing OpenStack via Single Installation "
                   "method. Press (Q) or CTRL-C to quit "
                   "installation.")
        self.ui.set_header(title, excerpt)
        self.sp_view = SingleInstallProgressView(self.model,
                                                 self.signal)
        self.ui.set_body(self.sp_view)

        # Process first step
        return self.ensure_kvm()
