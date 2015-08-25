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

from subprocess import (check_output,
                        CalledProcessError,
                        STDOUT)
import logging
import os
import lxc
import sys
from cloudinstall import utils

log = logging.getLogger("cloudinstall.api.container")


class NoContainerIPException(Exception):

    "Container has no IP"


class ContainerRunException(Exception):

    "Running cmd in container failed"


class Container:

    @classmethod
    def ip(cls, name):
        try:
            c = lxc.Container(name)
            ips = c.get_ips()
            log.debug("lxc-info found: '{}'".format(ips))
            if len(ips) == 0:
                raise NoContainerIPException()
            log.debug("using {} as the container ip".format(ips[0]))
            return ips[0]
        except CalledProcessError:
            log.exception("error calling lxc-info to get container IP")
            raise NoContainerIPException()

    # @classmethod
    # def cp(cls, filepath, dst):
    #     """ copy file to container

    #     :param str name: name of container
    #     :param str filepath: file to copy to container
    #     :param str dst: destination of remote path
    #     """
    #     params = {
    #         'file': filepath,
    #         'dst': dst
    #     }

    @classmethod
    def create(cls, name, userdata):
        """ creates a container from ubuntu-cloud template
        """
        # NOTE: the -F template arg is a workaround. it flushes the lxc
        # ubuntu template's image cache and forces a re-download. It
        # should be removed after https://github.com/lxc/lxc/issues/381 is
        # resolved.
        flushflag = "-F"
        if os.getenv("USE_LXC_IMAGE_CACHE"):
            log.debug("USE_LXC_IMAGE_CACHE set, so not flushing in lxc-create")
            flushflag = ""
        c = lxc.Container(name)
        if not c.create(template="ubuntu-cloud",
                        args=(flushflag, '-u', userdata)):
            raise Exception(
                "Unable to create container.")

    @classmethod
    def set_config_item(cls, name, key, value):
        c = lxc.Container(name)
        c.set_config_item(key, value)

    @classmethod
    def start(cls, name):
        """ starts lxc container

        :param str name: name of container
        """
        c = lxc.Container(name)
        if not c.start():
            raise Exception("Unable to start container: {}".format(sys.stderr))

    @classmethod
    def stop(cls, name):
        """ stops lxc container

        :param str name: name of container
        """
        c = lxc.Container(name)
        if not c.stop():
            raise Exception("Unable to stop container: {}".format(sys.stderr))

    @classmethod
    def destroy(cls, name):
        """ destroys lxc container

        :param str name: name of container
        """
        out = utils.get_command_output(
            'sudo lxc-destroy -n {0}'.format(name))

        if out['status'] > 0:
            raise Exception("Unable to destroy container: "
                            "{0}".format(out['output']))

        return out['status']

    @classmethod
    def wait_checked(cls, name, check_logfile, interval=20):
        """waits for container to be in RUNNING state, checking
        'check_logfile' every 'interval' seconds for error messages.

        Intended to be used with container_start, which uses 'lxc-start
        -d', which returns 0 immediately and does not detect errors.

        returns when the container 'name' is in RUNNING state.
        raises an exception if errors are detected.
        """
        while True:
            out = utils.get_command_output('sudo lxc-wait -n {} -s RUNNING '
                                           '-t {}'.format(name, interval))
            if out['status'] == 0:
                return
            log.debug("{} not RUNNING after {} seconds, "
                      "checking '{}' for errors".format(name, interval,
                                                        check_logfile))
            grepout = utils.get_command_output(
                'grep -q ERROR {}'.format(check_logfile))
            if grepout['status'] == 0:
                raise Exception("Error detected starting container. See {} "
                                "for details.".format(check_logfile))
        return

    @classmethod
    def wait(cls, name):
        """ waits for the container to be in a RUNNING state

        :param str name: name of container
        """
        c = lxc.Container(name)
        return c

    @classmethod
    def status(cls, name):
        return check_output("lxc-info -n {} -s "
                            "|| true".format(name),
                            shell=True, stderr=STDOUT).decode('utf-8')
