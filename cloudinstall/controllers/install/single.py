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
from functools import partial
from subprocess import check_output, STDOUT
from concurrent.futures import wait
from cloudinstall.async import Async
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

    def wait_for_task(self, future, msg=None):
        try:
            result = future.result()
            if msg:
                log.debug("Task: {}, Result: {}".format(msg, result))
                self.sp_view.set_current_task(msg)
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    def _set_ssh_key(self, future):
        set_ssh_key_f = utils.ssh_genkey_async()
        set_ssh_key_f.add_done_callback(
            partial(self.wait_for_task,
                    msg="Generating SSH keys"))

        future_complete_f = Async.pool.submit(
            lambda: wait(set_ssh_key_f, 10))
        future_complete_f.add_done_callback(self._set_apt_proxy)

    def _set_apt_proxy(self, future):
        set_apt_proxy_f = self.api.set_apt_proxy_async()
        set_apt_proxy_f.add_done_callback(
            partial(self.wait_for_task, msg="Checking APT proxy"))

        set_apts_proxy_f = self.api.set_apts_proxy_async()
        set_apts_proxy_f.add_done_callback(
            partial(self.wait_for_task, msg="Checking APTS proxy"))

        futures = (set_apt_proxy_f, set_apts_proxy_f)
        future_complete_f = Async.pool.submit(lambda: wait(futures, 10))
        future_complete_f.add_done_callback(self._set_userdata)

    def _set_userdata(self, future):
        set_userdata_f = self.api.set_userdata_async()
        set_userdata_f.add_done_callback(
            partial(self.wait_for_task, msg="Defining cloud-init userdata"))

        future_complete_f = Async.pool.submit(lambda: wait(set_userdata_f, 10))
        future_complete_f.add_done_callback(self._set_charmconfig)

    def _set_charmconfig(self, future):
        render_charmconf_f = utils.render_charm_config_async(self.config)
        render_charmconf_f.add_done_callback(
            partial(self.wait_for_task, msg="Defining charm config"))

        future_complete_f = Async.pool.submit(
            lambda: wait(render_charmconf_f, 10))
        future_complete_f.add_done_callback(self._set_juju)

    def _set_juju(self, future):
        set_juju_f = self.api.set_juju_async()
        set_juju_f.add_done_callback(
            partial(self.wait_for_task, msg="Configuring Juju"))

        future_complete_f = Async.pool.submit(lambda: wait(set_juju_f, 10))
        future_complete_f.add_done_callback(self._set_perms)

    def _set_perms(self, future):
        set_perms_f = self.api.set_perms_async()
        set_perms_f.add_done_callback(
            partial(self.wait_for_task, msg='Setting permissions'))

        future_complete_f = Async.pool.submit(lambda: wait(set_perms_f, 10))
        future_complete_f.add_done_callback(self._set_create_container)

    def _set_create_container(self, future):
        create_container_f = self.api.create_container_async()
        create_container_f.add_done_callback(
            partial(self.wait_for_task, msg="Creating host container"))

        future_complete_f = Async.pool.submit(
            lambda: wait(create_container_f, 1200))
        future_complete_f.add_done_callback(self._start_container)

    def _start_container(self, future):
        lxc_logfile = os.path.join(
            self.config['settings']['cfg_path'], 'lxc.log')
        start_container_f = self.api.start_container_async(lxc_logfile)
        start_container_f.add_done_callback(
            partial(self.wait_for_task, msg="Starting Container"))

        future_complete_f = Async.pool.submit(
            lambda: wait(start_container_f, 1200))
        future_complete_f.add_done_callback(self._wait_for_container)

    def _wait_for_container(self, future):
        lxc_logfile = os.path.join(
            self.config['settings']['cfg_path'], 'lxc.log')
        Container.wait_checked(self.container_name, lxc_logfile)
        tries = 0
        while not self.cloud_init_finished(tries):
            log.debug("Waiting for container")
            time.sleep(1)
            tries += 1
        return self._set_lxc_network()

    def _set_lxc_network(self, future):
        lxc_network = self.api.set_lxc_net_config()
        static_route_f = self.api.set_static_route_async(lxc_network)
        static_route_f.add_done_callback(
            partial(self.wait_for_task, msg="Configure LXC network"))

        future_complete_f = Async.pool.submit(lambda: wait(static_route_f, 10))
        future_complete_f.add_done_callback(self._set_install_deps)

    def _set_install_deps(self, future):
        install_deps_f = self.api.install_dependencies_async()
        install_deps_f.add_done_callback(
            partial(self.wait_for_task, msg="Installing dependencies"))

        future_complete_f = Async.pool.submit(
            lambda: wait(install_deps_f, 1200))
        future_complete_f.add_done_callback(self._set_copy_host_ssh)

    def _set_copy_host_ssh(self, future):
        copy_host_ssh_f = self.api.copy_host_ssh_to_container_async()
        copy_host_ssh_f.add_done_callback(
            partial(self.wait_for_task, msg="Copying ssh keys to container"))

        future_complete_f = Async.pool.submit(
            lambda: wait(copy_host_ssh_f, 20))
        future_complete_f.add_done_callback(self._set_upstream_deb)

    def _set_upstream_deb(self, future):
        upstream_deb = self.config['settings.single']['upstream_deb_path']
        if upstream_deb:
            copy_upstream_deb_f = self.api.copy_upstream_deb_async()
            copy_upstream_deb_f.add_done_callback(
                partial(self.wait_for_task,
                        msg="Setting local debian package"))

            install_upstream_deb_f = self.api.install_upstream_deb_async()
            install_upstream_deb_f.add_done_callback(
                partial(self.wait_for_task,
                        msg="Installing upstream debian package"))

            futures = (copy_upstream_deb_f, install_upstream_deb_f)
            future_complete_f = Async.pool.submit(lambda: wait(futures, 100))
            future_complete_f.add_done_callback(self._set_install_only)
        return self._set_install_only()

    def _set_install_only(self):
        # Close out loop if install only
        log.debug("Checking if we should stop for --install-only")
        if self.config['settings']['install_only']:
            log.info("Done installing, stopping here per --install-only.")
            self.config['settings']['install_only'] = "yes"
            utils.write_ini(self.config)
            self.signal.emit_signal('quit')
        return self._set_juju_proxy()

    def _set_juju_proxy(self):
        #  Update jujus no-proxy setting if applicable
        log.debug("Writing juju proxy settings if applicable")
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
        log.debug("Starting status screen.")
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
        ensure_nested_kvm_f = self.api.ensure_nested_kvm_async()
        ensure_nested_kvm_f.add_done_callback(
            partial(self.wait_for_task,
                    msg='Ensuring KVM is loaded'))

        future_complete_f = Async.pool.submit(
            lambda: wait(ensure_nested_kvm_f, 300))
        future_complete_f.add_done_callback(self._set_ssh_key)
