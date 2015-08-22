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
from subprocess import check_output, STDOUT
from tornado.gen import coroutine
from cloudinstall import utils, netutils
from cloudinstall.config import Config
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

    def __init__(self, ui, signal):
        self.ui = ui
        self.signal = signal
        self.model = SingleInstallModel()
        self.api = SingleInstallAPI()
        self.container_name = Config.get('settings.single', 'container_name')

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

    @coroutine
    def ensure_kvm(self):
        try:
            yield self.api.ensure_nested_kvm_async()
            self.ssh_genkey()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def ssh_genkey(self):
        try:
            yield utils.ssh_genkey_async()
            self.set_apt_proxy()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_apt_proxy(self):
        try:
            yield self.api.set_apt_proxy_async()
            self.set_userdata()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_userdata(self):
        try:
            yield self.api.set_userdata_async()
            self.set_charmconfig()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_charmconfig(self):
        try:
            yield utils.render_charm_config_async(Config)
            self.set_juju()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_juju(self):
        try:
            yield self.api.set_juju_async()
            self.set_perms()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_perms(self):
        try:
            yield self.api.set_perms_async()
            self.set_create_container()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_create_container(self):
        self.print_task("Creating Host Container")
        try:
            yield self.api.create_container_async()
            self.set_copy_host_ssh()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_copy_host_ssh(self):
        self.print_task("Copying ssh keys")
        try:
            yield self.api.copy_host_ssh_to_container_async()
            self.set_upstream_deb()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    @coroutine
    def set_upstream_deb(self):
        try:
            upstream_deb = Config.get('settings.single', 'upstream_deb_path')
            if upstream_deb:
                self.print_task("Setting local debian package")
                yield self.api.copy_upstream_deb_async()
                yield self.api.install_upstream_deb_async()
            self.set_install_only()
        except Exception as e:
            self.ui.set_body(ErrorView(self.model,
                                       self.signal,
                                       e))

    def set_install_only(self):
        # Close out loop if install only
        self.print_task("Checking if we should stop for --install-only")
        if Config.getboolean('settings', 'install_only'):
            log.info("Done installing, stopping here per --install-only.")
            Config.set('settings', 'install_only', "yes")
            self.signal.emit_signal('quit')
        return self.set_juju_proxy()

    def set_juju_proxy(self):
        #  Update jujus no-proxy setting if applicable
        proxy = Config.get('settings.proxy')
        if proxy['http_proxy'] or proxy['https_proxy']:
            log.info("Updating juju environments for proxy support")
            lxc_net = Config.get('settings.single', 'lxc_network')
            utils.update_environments_yaml(
                key='no-proxy',
                val='{},localhost,{}'.format(
                    Container.ip(self.container_name),
                    netutils.get_ip_set(lxc_net)))
        return self.start_status()

    def start_status(self):
        # Save our config before moving on to dashboard
        cloud_status_bin = ['openstack-status']
        juju_home = Config.get('settings.juju', 'home_expanded')
        Container.run(self.container_name,
                      "{0} juju --debug bootstrap".format(juju_home),
                      use_ssh=True)
        Container.run(
            self.container_name,
            "{0} juju status".format(juju_home),
            use_ssh=True)
        Container.run_status(
            self.container_name, " ".join(cloud_status_bin), Config)

    def single(self):
        """ Start prompting for Single Install information
        """
        title = "Single installation"
        excerpt = ("Please fill out the input fields to continue with "
                   "the single installation. See `man openstack-config`")
        self.ui.set_header(title, excerpt)
        use_advanced = Config.getboolean('runtime', 'advanced_config')
        self.ui.set_body(SingleInstallView(self.model,
                                           self.signal,
                                           use_advanced))

    def single_start(self, opts):
        """ Start single install, processing opts
        """
        password = opts['settings']['password'].value
        Config.set('settings', 'password', password)
        log.info("Password entered, saving {}".format(
            Config.get('settings', 'password')))

        if Config.getboolean('runtime', 'advanced_config'):
            log.info("Saving rest of advanced configuration settings.")
            for k in opts.keys():
                for a, b in opts[k].items():
                    log.debug("Saving ['{}']['{}'] = {}".format(k, a, b.value))
                    Config.set(k, a, b.value)
        log.info("Starting a single installation.")

        title = "Single installation progress"
        excerpt = ("Currently installing OpenStack via Single Installation "
                   "method. Press CTRL-W to quit "
                   "installation.")
        self.ui.set_header(title, excerpt)
        self.sp_view = SingleInstallProgressView(self.model,
                                                 self.signal)
        self.ui.set_body(self.sp_view)

        # Process first step
        return self.ensure_kvm()
