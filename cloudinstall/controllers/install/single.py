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
import time
from subprocess import check_output, STDOUT

from cloudinstall import utils, netutils
from cloudinstall.api.container import Container
from cloudinstall.controller import ControllerPolicy
from cloudinstall.models import SingleInstallModel
from cloudinstall.api.install import SingleInstallAPI
from cloudinstall.ui.views.install import (SingleInstallView,
                                           SingleInstallProgressView)


log = logging.getLogger('cloudinstall.c.i.single')


class SingleInstallControllerException(Exception):
    pass


class SingleInstallController(ControllerPolicy):

    def __init__(self, ui, signal):
        self.ui = ui
        self.signal = signal
        self.model = SingleInstallModel()
        self.api = SingleInstallAPI()

        self.tasks = {
            'initialize': 'Initializing Environment',
            'ensure_kvm': 'Ensuring KVM is loaded in Container',
            'config_set': 'Determining configuration and setting variables',
            'perms_set': 'Setting permissions',
            'initialize_container': 'Creating Container',
            'install_deps': 'Installing Dependencies',
            'bootstrap': 'Bootstrapping Juju'
        }

    def single(self):
        """ Start prompting for Single Install information
        """
        # TODO: Add exception view
        if os.path.exists(self.container_abspath):
            raise Exception("Container exists, please uninstall or kill "
                            "existing cloud before proceeding.")

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

    def handle_nested_kvm(self, future):
        try:
            result = future.result()
            log.debug("Future: {}".format(result))

            set_ssh_key_f = utils.ssh_genkey_async()
            set_ssh_key_f.add_done_callback(self.handle_ssh_genkey)
        except Exception as e:
            # TODO: show exception view
            log.exception(e)
            raise Exception(e)

    def handle_ssh_genkey(self, future):
        result = future.result()
        log.debug("Future: {}".format(result))
        self.sp_view.set_current_task(self.tasks['config_set'])
        return self._set_apt_proxy()

    def _set_apt_proxy(self):
        self.api.set_apt_proxy()
        self.api.set_apts_proxy()
        return self._set_userdata()

    def _set_userdata(self):
        self.api.set_userdata()
        return self._set_charmconfig()

    def _set_charmconfig(self):
        utils.render_charm_config(self.config)
        return self._set_juju()

    def _set_juju(self):
        self.api.set_juju()
        return self._set_perms()

    def _set_perms(self):
        self.sp_view.set_current_task(self.tasks['perms_set'])
        self.api.set_perms()

        create_container_f = self.api.create_container_async()
        create_container_f.add_done_callback(self.handle_create_container)
        return

    def handle_create_container(self, future):
        result = future.result()
        log.debug("Future: {}".format(result))

        self.sp_view.set_current_task(self.tasks['initialize_container'])
        start_container_f = self._start_container()
        start_container_f.add_done_callback(self.handle_start_container)

    def _start_container(self):
        lxc_logfile = os.path.join(self.config.cfg_path, 'lxc.log')
        self.api.start_container(lxc_logfile)
        Container.wait_checked(self.container_name, lxc_logfile)
        tries = 0
        while not self.cloud_init_finished(tries):
            time.sleep(1)
            tries += 1
        return

    def handle_start_container(self, future):
        result = future.result()
        log.debug("Future: {}".format(result))
        return self._set_lxc_network()

    def _set_lxc_network(self):
        lxc_network = self.api.set_lxc_net_config()
        self.api.set_static_route(lxc_network)

        install_deps_f = self.api.install_dependencies_async()
        install_deps_f.add_done_callback(self.handle_install_dependencies)

    def handle_install_dependencies(self, future):
        try:
            result = future.result()
            log.debug("Future: {}".format(result))
            self.sp_view.set_current_task(self.tasks['install_deps'])

            copy_host_ssh_f = self.api.copy_host_ssh_to_container_async()
            copy_host_ssh_f.add_done_callback(self.handle_copy_host_ssh)
        except Exception as e:
            raise e

    def handle_copy_host_ssh(self, future):
        try:
            result = future.result()
            log.debug("Future: {}".format(result))

            upstream_deb = self.config['settings.single']['upstream_deb_path']
            if upstream_deb:
                copy_upstream_deb_f = self.api.copy_upstream_deb_async()
                copy_upstream_deb_f.add_done_callback(
                    self.handle_copy_upstream_deb)

            # Close out loop if install only
            if self.config['settings']['install_only']:
                log.info("Done installing, stopping here per --install-only.")
                self.config['settings']['install_only'] = "yes"
                utils.write_ini(self.config)
                self.signal.emit_signal('quit')
        except Exception as e:
            raise e

    def handle_copy_upstream_deb(self, future):
        try:
            result = future.result()
            log.debug("Future: {}".format(result))

            install_upstream_deb_f = self.api.install_upstream_deb_async()
            install_upstream_deb_f.add_done_callback(
                self.handle_install_upstream_deb)
        except Exception as e:
            raise e

    def handle_install_upstream_deb(self, future):
        try:
            result = future.result()
            log.debug("Future: {}".format(result))
            # Close out loop if install only
            # FIXME: repeatative from copy_host_ssh
            if self.config['settings']['install_only']:
                log.info("Done installing, stopping here per --install-only.")
                self.config['settings']['install_only'] = "yes"
                utils.write_ini(self.config)
                self.signal.emit_signal('quit')
            return self._set_juju_proxy()
        except Exception as e:
            raise e

    def _set_juju_proxy(self):
        #  Update jujus no-proxy setting if applicable
        proxy = self.config['settings.proxy']
        if proxy['http_proxy'] or proxy['https_proxy']:
            log.info("Updating juju environments for proxy support")
            lxc_net = self.config['settings.single']['lxc_network']
            utils.update_environments_yaml(
                key='no-proxy',
                val='{},localhost,{}'.format(
                    Container.ip(self.container_name),
                    netutils.get_ip_set(lxc_net)))
        return self._start_status()

    def _start_status(self):
        self.sp_view.set_current_task(self.tasks['bootstrap'])
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
        log.info("Starting a single installation.")

        title = "Single installation progress"
        excerpt = ("Currently installing OpenStack via Single Installation "
                   "method. Press (Q) or CTRL-C to quit "
                   "installation.")
        self.ui.set_header(title, excerpt)
        self.sp_view = SingleInstallProgressView(self.model,
                                                 self.signal,
                                                 self.tasks)
        self.ui.set_body(self.single_progress_view)

        self.sp_view.set_current_task(self.tasks['ensure_kvm'])
        # Process first step
        ensure_nested_kvm_f = self.api.ensure_nested_kvm_async()
        ensure_nested_kvm_f.add_done_callback(self.handle_nested_kvm)
