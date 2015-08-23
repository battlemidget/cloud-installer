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

""" API for single install routines

Exposes both synchronous and asynchronous routines via futures
"""

from ipaddress import IPv4Network
import shutil
from subprocess import call, check_call, check_output, STDOUT
import os
import json
import logging
import time
from cloudinstall.config import Config
from cloudinstall import utils, netutils
from cloudinstall.async import Async
from cloudinstall.api.container import (Container,
                                        ContainerRunException,
                                        NoContainerIPException)

log = logging.getLogger("cloudinstall.a.i.single")


class SingleInstallAPIException(Exception):
    pass


class SingleInstallAPI:
    def __init__(self):
        username = utils.install_user()
        self.container_name = 'openstack-single-{}'.format(username)
        self.container_path = '/var/lib/lxc'
        self.container_abspath = os.path.join(self.container_path,
                                              self.container_name)
        self.cfg_path = Config.get('settings', 'cfg_path')
        self.userdata = os.path.join(self.cfg_path, 'userdata.yaml')

    def set_apt_proxy_async(self):
        return Async.pool.submit(self.set_apt_proxy)

    def set_apt_proxy(self):
        "Use http_proxy unless apt_http_proxy is explicitly set"
        proxy = Config.get('settings.proxy')
        apt_proxy = proxy['apt_proxy']
        http_proxy = proxy['http_proxy']
        if not apt_proxy and http_proxy:
            proxy['apt_proxy'] = http_proxy

        apt_https_proxy = proxy['apt_https_proxy']
        https_proxy = proxy['https_proxy']
        if not apt_https_proxy and https_proxy:
            proxy['apt_https_proxy'] = https_proxy
        return

    def set_proxy_pollinate_async(self):
        return Async.pool.submit(self.set_proxy_polliante)

    def set_proxy_pollinate(self):
        """ Proxy pollinate if http/s proxy is set """
        # pass proxy through to pollinate
        proxy = Config.get('settings.proxy')
        http_proxy = proxy['http_proxy']
        https_proxy = proxy['https_proxy']
        log.debug('Found proxy info: {}/{}'.format(http_proxy, https_proxy))
        pollinate = ['env']
        if http_proxy:
            pollinate.append('http_proxy={}'.format(http_proxy))
        if https_proxy:
            pollinate.append('https_proxy={}'.format(https_proxy))
        pollinate.extend(['pollinate', '-q'])
        return pollinate

    def set_userdata_async(self):
        return Async.pool.submit(self.set_userdata)

    def set_userdata(self):
        """ set userdata file for container install
        """
        render_parts = {'extra_sshkeys': [utils.ssh_readkey()]}

        use_upstream_ppa = Config.getboolean('settings', 'use_upstream_ppa')
        if use_upstream_ppa:
            ppa = Config.get('settings', 'upstream_ppa')
            render_parts['upstream_ppa'] = ppa

        render_parts['seed_command'] = self.set_proxy_pollinate()

        render_parts['apt_mirror'] = Config.get('settings', 'apt_mirror')
        for opt in Config.get('settings.juju').keys():
            if opt in ['image_metadata_url',
                       'tools_metadata_url']:
                val = Config.get('settings', opt)
                if val:
                    render_parts[opt] = val
        for opt in Config.get('settings.proxy').keys():
            if opt in ['apt_proxy', 'apt_https_proxy', 'http_proxy',
                       'https_proxy', 'no_proxy']:
                val = Config.get('settings.proxy', opt)
                if val:
                    render_parts[opt] = val

        dst_file = os.path.join(self.cfg_path,
                                'userdata.yaml')
        original_data = utils.load_template('userdata.yaml')
        log.info("Prepared userdata: {}".format(render_parts))
        modified_data = original_data.render(render_parts)
        utils.spew(dst_file, modified_data)

    def set_juju_async(self):
        return Async.pool.submit(self.set_juju)

    def set_juju(self):
        """ set juju environments for bootstrap
        """
        render_parts = {'openstack_password':
                        Config.get('settings', 'password'),
                        'ubuntu_series':
                        Config.get('settings.juju', 'series')}

        for opt in ['apt_proxy', 'apt_https_proxy', 'http_proxy',
                    'https_proxy']:
            val = Config.get('settings.proxy', opt)
            if val:
                render_parts[opt] = val

        # configure juju environment for bootstrap
        single_env = utils.load_template('juju-env/single.yaml')
        single_env_modified = single_env.render(render_parts)
        utils.spew(Config.get('settings.juju', 'environments_yaml'),
                   single_env_modified,
                   owner=utils.install_user())

    def copy_host_ssh_to_container_async(self):
        return Async.pool.submit(self.copy_host_ssh_to_container)

    def copy_host_ssh_to_container(self):
        Container.cp(self.container_name,
                     os.path.join(utils.install_home(), '.ssh/id_rsa*'),
                     '.ssh/.')

    def set_lxc_net_config_async(self):
        return Async.pool.submit(self.set_lxc_net_config)

    def set_lxc_net_config(self):
        """Finds and configures a new subnet for the host container,
        to avoid overlapping with IPs used for Neutron.
        """
        lxc_net_template = utils.load_template('lxc-net')
        lxc_net_container_filename = os.path.join(self.container_abspath,
                                                  'rootfs/etc/default/lxc-net')

        network = netutils.get_unique_lxc_network()
        Config.set('settings.single', 'lxc_network', network)
        nw = IPv4Network(network)
        addr = nw[1]
        netmask = nw.with_netmask.split('/')[-1]
        net_low, net_high = netutils.ip_range_max(nw, [addr])
        dhcp_range = "{},{}".format(net_low, net_high)
        render_parts = dict(addr=addr,
                            netmask=netmask,
                            network=network,
                            dhcp_range=dhcp_range)
        lxc_net = lxc_net_template.render(render_parts)
        name = self.container_name
        log.info("Writing lxc-net config for {}".format(name))
        utils.spew(lxc_net_container_filename, lxc_net)

        return network

    def set_static_route_async(self, lxc_net):
        return Async.pool.submit(self.set_static_route, lxc_net)

    def set_static_route(self, lxc_net):
        """ Adds static route to host system
        """
        # Store container IP in config
        ip = Container.ip(self.container_name)
        Config.set('settings.single', 'container_ip', ip)

        log.info("Adding static route for {} via {}".format(lxc_net,
                                                            ip))

        out = utils.get_command_output(
            'ip route add {} via {} dev lxcbr0'.format(lxc_net, ip))
        if out['status'] != 0:
            raise Exception("Could not add static route for {}"
                            " network: {}".format(lxc_net, out['output']))

    def create_container_async(self):
        return Async.pool.submit(self.create_container)

    def create_container(self):
        """ Creates container
        """
        Container.create(self.container_name, self.userdata)

        log.debug("Writing containers fstab file")
        with open(os.path.join(self.container_abspath, 'fstab'), 'w') as f:
            f.write("{0} {1} none bind,create=dir\n".format(
                self.cfg_path,
                'home/ubuntu/.cloud-install'))
            f.write("/var/cache/lxc var/cache/lxc none bind,create=dir\n")
            # Detect additional charm plugins and make available to the
            # container.
            charm_plugin_dir = Config.get('settings.charms', 'plugin_path')
            if charm_plugin_dir \
               and self.cfg_path in charm_plugin_dir:
                plug_dir = os.path.abspath(charm_plugin_dir)
                plug_base = os.path.basename(plug_dir)
                f.write("{d} home/ubuntu/{m} "
                        "none bind,create=dir\n".format(d=plug_dir,
                                                        m=plug_base))

            extra_mounts = os.getenv("EXTRA_BIND_DIRS", None)
            if extra_mounts:
                for d in extra_mounts.split(','):
                    mountpoint = os.path.basename(d)
                    f.write("{d} home/ubuntu/{m} "
                            "none bind,create=dir\n".format(d=d,
                                                            m=mountpoint))

        # update container config
        with open(os.path.join(self.container_abspath, 'config'), 'a') as f:
            f.write("lxc.mount.auto = cgroup:mixed\n"
                    "lxc.start.auto = 1\n"
                    "lxc.start.delay = 5\n"
                    "lxc.mount = {}/fstab\n".format(self.container_abspath))
        lxc_logfile = os.path.join(
            self.cfg_path, 'lxc.log')

        Container.start(self.container_name, lxc_logfile)

        Container.wait_checked(self.container_name,
                               lxc_logfile)

        tries = 0
        while not self.cloud_init_finished(tries):
            time.sleep(1)
            tries += 1

        # we do this here instead of using cloud-init, for greater
        # control over ordering
        log.debug("Container started, cloud-init done.")

        lxc_network = self.set_lxc_net_config()
        self.set_static_route(lxc_network)

        log.debug("Installing openstack & openstack-single directly, "
                  "and juju-local, libvirt-bin and lxc via deps")
        Container.run(self.container_name,
                      "env DEBIAN_FRONTEND=noninteractive apt-get -qy "
                      "-o Dpkg::Options::=--force-confdef "
                      "-o Dpkg::Options::=--force-confold "
                      "install openstack openstack-single ", use_ssh=True)
        log.debug("done installing deps")

    def copy_upstream_deb_async(self):
        return Async.pool.submit(self.copy_upstream_deb)

    def copy_upstream_deb(self):
        """ Copies local upstream debian package into container """
        shutil.copy(Config.get('settings', 'upstream_deb'),
                    self.cfg_path)

    def install_upstream_deb_async(self):
        return Async.pool.submit(self.install_upstream_deb)

    def install_upstream_deb(self):
        log.info('Found upstream deb, installing that instead')
        filename = os.path.basename(
            Config.get('settings.single', 'upstream_deb_path'))
        try:
            Container.run(
                self.container_name,
                'dpkg -i /home/ubuntu/.cloud-install/{}'.format(
                    filename),
                output_cb=self.set_progress_output)
        except:
            # Make sure deps are installed if any new ones introduced by
            # the upstream packaging.
            Container.run(
                self.container_name, 'apt-get install -qyf',
                output_cb=self.set_progress_output)

    def set_perms_async(self):
        return Async.pool.submit(self.set_perms)

    def set_perms(self):
        """ sets permissions
        """
        try:
            log.info("Setting permissions for user {}".format(
                utils.install_user()))
            utils.chown(self.cfg_path,
                        utils.install_user(),
                        utils.install_user(),
                        recursive=True)
            utils.get_command_output("sudo chmod 777 {}".format(
                self.cfg_path))
            utils.get_command_output("sudo chmod 777 -R {}/*".format(
                self.cfg_path))
        except:
            msg = ("Error setting ownership for "
                   "{}".format(self.cfg_path))
            log.exception(msg)
            raise Exception(msg)

    def ensure_nested_kvm_async(self):
        return Async.pool.submit(self.ensure_nested_kvm)

    def ensure_nested_kvm(self):
        """kvm_intel module defaults to nested OFF. If qemu_system_x86 is not
        installed, this may stay off. Our package installs a
        modprobe.d/openstack.conf file to fix this after reboots, but
        we also try to reload the module to work now.
        """

        if 0 == call("lsmod | grep kvm_amd", shell=True):
            return              # we're fine, kvm_amd has nested on by default
        if 0 != call("lsmod | grep kvm_intel", shell=True):
            raise Exception("kvm_intel kernel module not loaded, "
                            "nested VMs will fail to launch")

        try:
            nested_on = check_output("cat "
                                     "/sys/module/kvm_intel/parameters/nested"
                                     "".format(self.container_name),
                                     shell=True, stderr=STDOUT).decode('utf-8')
            if nested_on.strip() == 'Y':
                return
        except:
            log.exception("can't cat /sys/module/kvm_intel/parameters/nested")
            raise Exception("error inspecting kvm_intel module params, nested"
                            "VMs likely will not work")

        # need to unload and reload module
        try:
            check_call("modprobe -r kvm_intel", shell=True)
        except Exception as e:
            log.exception("couldn't unload kvm_intel: {}".format(e.output))
            raise Exception("Could not automatically unload kvm_intel module "
                            "to enable nested VMs. A manual reboot or reload"
                            "will be required.")

        if 0 != call("modprobe kvm_intel", shell=True):
            raise Exception("Could not automatically reload kvm_intel kernel"
                            "module to enable nested VMs. A manual reboot or "
                            "reload will be required.")
        return True

    def cloud_init_finished(self, tries, maxlenient=20):
        """checks cloud-init result.json in container to find out status

        For the first `maxlenient` tries, it treats a container with
        no IP and SSH errors as non-fatal, assuming initialization is
        still ongoing. Afterwards, will raise exceptions for those
        errors, so as not to loop forever.

        returns True if cloud-init finished with no errors, False if
        it's not done yet, and raises an exception if it had errors.

        """
        cmd = 'sudo cat /run/cloud-init/result.json'
        try:
            result_json = Container.run(self.container_name, cmd)

        except NoContainerIPException as e:
            log.debug("Container has no IPs according to lxc-info. "
                      "Will retry.")
            return False

        except ContainerRunException as e:
            _, returncode = e.args
            if returncode == 255:
                if tries < maxlenient:
                    log.debug("Ignoring initial SSH error.")
                    return False
                raise e
            if returncode == 1:
                # the 'cat' did not find the file.
                if tries < 1:
                    log.debug("Waiting for cloud-init status result")
                return False
            else:
                log.debug("Unexpected return code from reading "
                          "cloud-init status in container.")
                raise e

        if result_json == '':
            return False

        try:
            ret = json.loads(result_json)
        except Exception as e:
            if tries < maxlenient + 10:
                log.debug("exception trying to parse '{}'"
                          " - retrying".format(result_json))
                return False

            log.error(str(e))
            log.debug("exception trying to parse '{}'".format(result_json))
            raise e

        errors = ret['v1']['errors']
        if len(errors):
            log.error("Container cloud-init finished with "
                      "errors: {}".format(errors))
            raise Exception("Top-level container OS did not initialize "
                            "correctly.")
        return True
