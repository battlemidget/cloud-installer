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

""" Base api
"""

import requests
import json
from .config import Config
from .container import Container
from .install.single import SingleInstallAPI


class Result:
    def __init__(self, response):
        self.response = response

    def ok(self):
        return self.response.ok

    @property
    def content(self):
        return json.loads(self.response.text)


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.api_url = "http://{}:{}/api".format(self.host, self.port)

    def get(self, url, params=None):
        return Result(requests.get(url=self.api_url + url,
                                   params=params))

    def post(self, url, params=None):
        return Result(requests.post(url=self.api_url + url,
                                    data=params))

    def delete(self, url, params=None):
        return Result(requests.delete(url=self.api_url + url))

    # Config API -------------------------------------------------------------
    def config(self):
        return Config(self)

    # Container API ----------------------------------------------------------
    def container(self):
        return Container(self)

    # Single Install API -----------------------------------------------------
    def single_install(self):
        return SingleInstallAPI(self)
