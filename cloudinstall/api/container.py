#
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

import subprocess
from subprocess import (check_output,
                        CalledProcessError)
import logging
import shlex
import pty
import os
import codecs
import errno
import time
import tempfile
import yaml
from collections import deque
from cloudinstall import utils

log = logging.getLogger("cloudinstall.api.container")


class NoContainerIPException(Exception):

    "Container has no IP"


class ContainerRunException(Exception):

    "Running cmd in container failed"


class Container:

    @classmethod
    def import_images(cls):
        out = subprocess.call("lxd-images import ubuntu --alias ubuntu")
        return out == 0

    @classmethod
    def exists(cls, name):
        out = subprocess.call("lxc info " + name, shell=True)
        return out == 0

    @classmethod
    def get_status(cls, name):
        s = subprocess.check_output("lxc info {} | grep Status".format(name),
                                    shell=True,
                                    stderr=subprocess.STDOUT).decode('utf-8')
        return s

    @classmethod
    def ip(cls, name):
        try:
            ips = subprocess.check_output("lxc list {}".format(name),
                                          shell=True).decode()
            ips = ips.splitlines()
            if len(ips) < 5:    # four lines of table drawing
                log.debug("Container not shown in lxc list: {} ".format(ips))
                raise NoContainerIPException()

            ip = ips[3].split('|')[3].strip()
            # that gives us a comma-sep list, take the first one:
            ip = ip.split(',')[0]
            log.debug("lxc ip found: '{}'".format(ip))
            if len(ip) == 0:
                raise NoContainerIPException()
            log.debug("using {} as the container ip".format(ip))
            return ip

        except subprocess.CalledProcessError:
            log.exception("error calling lxc list to get container IP")
            raise NoContainerIPException()

    @classmethod
    def run(cls, name, cmd, use_ssh=False, output_cb=None):
        """ run command in container
        :param str name: name of container
        :param str cmd: command to run
        """

        if use_ssh:
            ip = cls.ip(name)
            quoted_cmd = shlex.quote(cmd)
            wrapped_cmd = ("sudo -H -u {3} TERM=xterm256-color ssh -t -q "
                           "-l ubuntu -o \"StrictHostKeyChecking=no\" "
                           "-o \"UserKnownHostsFile=/dev/null\" "
                           "-o \"ControlMaster=auto\" "
                           "-o \"ControlPersist=600\" "
                           "-i {2} "
                           "{0} {1}".format(ip, quoted_cmd,
                                            utils.ssh_privkey(),
                                            utils.install_user()))
        else:
            quoted_cmd = cmd
            wrapped_cmd = ("lxc exec {container_name} -- "
                           "{cmd}".format(container_name=name,
                                          cmd=cmd))

        log.debug("Final command to run:\n'{}'".format(wrapped_cmd))
        stdoutmaster, stdoutslave = pty.openpty()
        subproc = subprocess.Popen(wrapped_cmd, shell=True,
                                   stdout=stdoutslave,
                                   stderr=subprocess.PIPE)
        os.close(stdoutslave)
        decoder = codecs.getincrementaldecoder('utf-8')()

        def last_ten_lines(s):
            chunk = s[-1500:]
            lines = chunk.splitlines(True)
            return ''.join(lines[-10:]).replace('\r', '')

        decoded_output = ""
        try:
            while subproc.poll() is None:
                try:
                    b = os.read(stdoutmaster, 512)
                except OSError as e:
                    if e.errno != errno.EIO:
                        raise
                    break
                else:
                    final = False
                    if not b:
                        final = True
                    decoded_chars = decoder.decode(b, final)
                    if decoded_chars is None:
                        continue

                    decoded_output += decoded_chars
                    if output_cb:
                        ls = last_ten_lines(decoded_output)

                        output_cb(ls)
                    if final:
                        break
        finally:
            os.close(stdoutmaster)
            if subproc.poll() is None:
                subproc.kill()
            subproc.wait()

        errors = [l.decode('utf-8') for l in subproc.stderr.readlines()]
        if output_cb:
            output_cb(last_ten_lines(decoded_output))

        errors = ''.join(errors)

        if subproc.returncode == 0:
            return decoded_output.strip()
        else:
            raise ContainerRunException("Problem running {0} in container "
                                        "{1}".format(quoted_cmd, name),
                                        subproc.returncode)

    @classmethod
    def run_status(cls, name, cmd, config):
        """ Runs cloud-status in container
        """
        ip = cls.ip(name)
        cmd = ("sudo -H -u {2} TERM=xterm256-color ssh -t -q "
               "-l ubuntu -o \"StrictHostKeyChecking=no\" "
               "-o \"UserKnownHostsFile=/dev/null\" "
               "-o \"ControlMaster=auto\" "
               "-o \"ControlPersist=600\" "
               "-i {1} "
               "{0} {3}".format(ip, utils.ssh_privkey(),
                                utils.install_user(), cmd))
        log.debug("Running command without waiting "
                  "for response.: {}".format(cmd))
        args = deque(shlex.split(cmd))
        os.execlp(args.popleft(), *args)

    @classmethod
    def cp(cls, name, src, dst):
        """ copy file to container
        :param str name: name of container
        :param str src: file to copy to container
        :param str dst: destination full path
        """

        cmd = ("lxc file push {src} {name}/{dst} ".format(dst=dst,
                                                          name=name,
                                                          src=src))
        ret = utils.get_command_output(cmd)
        if ret['status'] > 0:
            raise Exception("There was a problem copying ({0}) to the "
                            "container ({1}): out:'{2}'\nerr:{3}"
                            "\ncmd:{4}".format(src, name,
                                               ret['output'],
                                               ret['err'],
                                               cmd))

    @classmethod
    def create(cls, name, userdata):
        """ creates a container from an image with the alias 'ubuntu'
        """
        out = utils.get_command_output('lxc image list | grep ubuntu')
        if len(out['output']) == 0:
            utils.get_command_output(
                'lxd-images import ubuntu -- alias ubuntu')
            raise Exception("No 'ubuntu' image found")

        imgname = os.getenv("LXD_IMAGE_NAME", "ubuntu")
        out = utils.get_command_output('lxc init {} {}'.format(imgname,
                                                               name))
        if out['status'] > 0:
            raise Exception("Unable to create container: "
                            + out['output'])

        out = utils.get_command_output('lxc config show ' + name)
        if out['status'] > 0:
            raise Exception("Unable to get container config: "
                            + out['output'])

        cfgyaml = yaml.load(out['output'])
        with open(userdata, 'r') as uf:
            if 'user.user_data' in cfgyaml['config']:
                raise Exception("Container config already has userdata")

            cfgyaml['config']['user.user-data'] = "".join(uf.readlines())
            # cfgyaml['config']['security.privileged'] = True

        with tempfile.NamedTemporaryFile(delete=False) as cfgtmp:
            cfgtmp.write(yaml.dump(cfgyaml).encode())
            cfgtmp.flush()
            cmd = 'cat {} | lxc config edit {}'.format(cfgtmp.name, name)
            log.debug("cmd is '{}'".format(cmd))
            out = utils.get_command_output(cmd)
            if out['status'] > 0:
                raise Exception("Unable to set userdata config: "
                                + out['output'] + "ERR" + out['err'])

        return 0

    @classmethod
    def add_bind_mounts(cls, name, mounts):
        return ["lxc.mount.entry = {} {} "
                "none bind,create={}".format(src, dest, ty)
                for src, dest, ty in mounts]

    @classmethod
    def add_config_entries(cls, name, configlines):
        raw_lxc_config = "\n".join(configlines)
        out = utils.get_command_output('lxc config set {} raw.lxc '
                                       '"{}"'.format(name, raw_lxc_config))
        if out['status'] > 0:
            raise Exception("couldn't set container config")

    @classmethod
    def start(cls, name):
        """ starts lxc container
        :param str name: name of container
        """
        out = utils.get_command_output('lxc start ' + name)

        if out['status'] > 0:
            raise Exception("Unable to start container: "
                            "out:{}\nerr{}".format(out['output'],
                                                   out['err']))
        return out['status']

    @classmethod
    def stop(cls, name):
        """ stops lxc container
        :param str name: name of container
        """
        out = utils.get_command_output('lxc stop ' + name)

        if out['status'] > 0:
            raise Exception("Unable to stop container: "
                            "{}".format(out['output']))

        return out['status']

    @classmethod
    def destroy(cls, name):
        """ destroys lxc container
        :param str name: name of container
        """
        out = utils.get_command_output('lxc delete ' + name)

        if out['status'] > 0:
            raise Exception("Unable to delete container: "
                            "{0}".format(out['output']))

        return out['status']

    @classmethod
    def wait_checked(cls, name, check_logfile, interval=20):
        """waits for container to be in RUNNING state.
        Ignores check_logfile.
        returns when the container 'name' is in RUNNING state.
        raises an exception if errors are detected.
        """
        while True:
            cmd = 'lxc info {} | grep Status'.format(name)
            out = utils.get_command_output(cmd)
            if out['status'] != 0:
                raise Exception("Error getting container info {}".format(out))
            outstr = out['output'].strip()
            if outstr == "Status: Running":
                return
            time.sleep(4)
