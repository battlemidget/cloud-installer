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
import sys
import time
from functools import partial
from cloudinstall.job import job, JobQueue
from cloudinstall import utils
from cloudinstall.api.container import Container


log = logging.getLogger('cloudinstall.c.i.single')


class SingleInstallException(Exception):
    pass


class SingleInstall:

    def __init__(self, config):
        self.config = config
        username = utils.install_user()
        self.container_name = 'openstack-single-{}'.format(username)
        self.container_path = '/var/lib/lxc'
        self.container_abspath = os.path.join(self.container_path,
                                              self.container_name)
        self.userdata = os.path.join(
            self.config.cfg_path, 'userdata.yaml')

        # Sets install type
        self.config.setopt('install_type', 'Single')

    @job('Configuring Proxy')
    def setup_apt_proxy(self):
        "Use http_proxy unless apt_proxy is explicitly set"
        apt_proxy = self.config.getopt('apt_proxy')
        http_proxy = self.config.getopt('http_proxy')
        if not apt_proxy and http_proxy:
            self.config.setopt('apt_proxy', http_proxy)

        apt_https_proxy = self.config.getopt('apt_https_proxy')
        https_proxy = self.config.getopt('https_proxy')
        if not apt_https_proxy and https_proxy:
            self.config.setopt('apt_https_proxy', https_proxy)

    @job('Pollinate')
    def _proxy_pollinate(self):
        """ Proxy pollinate if http/s proxy is set """
        # pass proxy through to pollinate
        http_proxy = self.config.getopt('http_proxy')
        https_proxy = self.config.getopt('https_proxy')
        log.debug('Found proxy info: {}/{}'.format(http_proxy, https_proxy))
        pollinate = ['env']
        if http_proxy:
            pollinate.append('http_proxy={}'.format(http_proxy))
        if https_proxy:
            pollinate.append('https_proxy={}'.format(https_proxy))
        pollinate.extend(['pollinate', '-q', '--curl-opts', '-k'])
        return pollinate

    @job('Writing userdata')
    def prep_userdata(self):
        """ preps userdata file for container install
        """
        render_parts = {'extra_sshkeys': [utils.ssh_readkey()]}

        if self.config.getopt('upstream_ppa'):
            render_parts['upstream_ppa'] = self.config.getopt('upstream_ppa')

        render_parts['seed_command'] = self._proxy_pollinate()

        for opt in ['apt_proxy', 'apt_https_proxy', 'http_proxy',
                    'https_proxy', 'no_proxy',
                    'image_metadata_url', 'tools_metadata_url',
                    'apt_mirror', 'next_charms']:
            val = self.config.getopt(opt)
            if val:
                render_parts[opt] = val

        dst_file = os.path.join(self.config.cfg_path,
                                'userdata.yaml')
        original_data = utils.load_template('userdata.yaml')
        log.debug("Prepared userdata: {}".format(render_parts))
        modified_data = original_data.render(render_parts)
        utils.spew(dst_file, modified_data)

    @job('Preparing Juju')
    def prep_juju(self):
        """ preps juju environments for bootstrap
        """
        ip = False
        while not ip:
            try:
                ip = Container.ip(self.container_name)
            except:
                time.sleep(1)
        log.info("Using {} as bootstrap host".format(ip))
        render_parts = {'openstack_password':
                        self.config.getopt('openstack_password'),
                        'ubuntu_series':
                        self.config.getopt('ubuntu_series'),
                        'bootstrap_host': ip}

        for opt in ['apt_proxy', 'apt_https_proxy', 'http_proxy',
                    'https_proxy']:
            val = self.config.getopt(opt)
            if val:
                render_parts[opt] = val

        # configure juju environment for bootstrap
        single_env = utils.load_template('juju-env/manual.yaml')
        single_env_modified = single_env.render(render_parts)
        utils.spew(os.path.join(self.config.juju_path(),
                                'environments.yaml'),
                   single_env_modified,
                   owner=utils.install_user())

    @job('Setting permissions')
    def set_perms(self):
        """ sets permissions
        """
        try:
            log.info("Setting permissions for user {}".format(
                utils.install_user()))
            utils.chown(self.config.cfg_path,
                        utils.install_user(),
                        utils.install_user(),
                        recursive=True)
            utils.get_command_output("sudo chmod 777 {}".format(
                self.config.cfg_path))
            utils.get_command_output("sudo chmod 777 -R {}/*".format(
                self.config.cfg_path))
        except:
            msg = ("Error setting ownership for "
                   "{}".format(self.config.cfg_path))
            log.exception(msg)
            raise Exception(msg)

    def create_stack_nodes(self):
        services = ['mysql', 'keystone', 'compute', 'dashboard']
        for svc in services:
            log.info("Starting node: {}".format(svc))
            container = 'openstack-{}'.format(svc)
            Container.create(container, self.userdata)
            Container.start(container)
            ip = False
            while not ip:
                try:
                    ip = Container.ip(container)
                except:
                    time.sleep(1)
            time.sleep(5)
            cmd = ('{} juju add-machine '
                   'ssh:ubuntu@{}'.format(self.config.juju_home(use_expansion=True),
                                          ip))
            log.debug(cmd)
            out = utils.get_command_output(cmd)
            log.debug(out)

    def bootstrap(self):
        time.sleep(5)
        out = utils.get_command_output(
            '{} juju --debug bootstrap'.format(
                self.config.juju_home(use_expansion=True)))
        log.debug(out)

    def do_install(self):
        q = JobQueue()
        jobs = [
            utils.ssh_genkey,
            self.setup_apt_proxy,
            self.prep_userdata,
            partial(utils.render_charm_config, self.config),
            partial(Container.create, self.container_name, self.userdata),
            partial(Container.start, self.container_name),
            self.set_perms,
            self.prep_juju,
            self.bootstrap,
            self.create_stack_nodes,
        ]
        for j in jobs:
            q.add(j)

        log.info('Begin job processing')
        q.process()

        # Copy over host ssh keys
        # Container.cp(self.container_name,
        #              os.path.join(utils.install_home(), '.ssh/id_rsa*'),
        #              '.ssh/.')

        # Update jujus no-proxy setting if applicable
        # if self.config.getopt('http_proxy') or \
        #    self.config.getopt('https_proxy'):
        #     log.info("Updating juju environments for proxy support")
        #     lxc_net = self.config.getopt('lxc_network')
        #     self.config.update_environments_yaml(
        #         key='no-proxy',
        #         val='{},localhost,{}'.format(
        #             Container.ip(self.container_name),
        #             netutils.get_ip_set(lxc_net)))

        # start the party
        # cloud_status_bin = ['openstack-status']
        # Container.run(self.container_name,
        #               "{0} juju --debug bootstrap".format(
        #                   self.config.juju_home(use_expansion=True)),
        #               use_ssh=True, output_cb=self.set_progress_output)
        # Container.run(
        #     self.container_name,
        #     "{0} juju status".format(
        #         self.config.juju_home(use_expansion=True)),
        #     use_ssh=True)
        # Container.run_status(
        #     self.container_name, " ".join(cloud_status_bin), self.config)
