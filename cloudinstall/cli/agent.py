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

""" Installer agent

REST server for managing the install and state of an OpenStack install
"""

import logging
import configparser
from tornado import ioloop
from tornado.web import Application, url

log = logging.getLogger('cloudinstall.cli.agent')


class AgentCmd:
    def __init__(self, opts):
        self.cfg = configparser.ConfigParser()
        self.cfg.read('/etc/openstack/agent.conf')
        self.opts = opts
        self.port = self.cfg['general']['port']
        if self.opts.port:
            self.port = self.opts.port
            self.cfg['general']['port'] = self.opts.port
        with open('/etc/openstack/agent.conf', 'w') as cfg_w:
            self.cfg.write(cfg_w)

    def main(self):
        log.info("Running: Ubuntu OpenStack Agent")

        urls = [
            url(r"/api/config",
                "cloudinstall.agent.controllers.Config"),
            url(r"/api/install/single/ssh_keys",
                "cloudinstall.agent.controllers.SshKeys")
        ]

        settings = dict(
            client={},
            run_as=None
        )
        application = Application(urls, **settings)
        application.listen(self.port)
        ioloop.IOLoop.current().start()
