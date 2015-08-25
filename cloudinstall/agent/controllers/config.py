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

""" Agent config controller

Obtains config generated from UI install questions and
stores for future processing
"""

from .base import BaseHandler  # NOQA
from tornado.gen import coroutine


class ConfigHandler(BaseHandler):
    """ POST /api/config

    Store application config and set the appropriate run_as user
    when executing installer tasks.
    :param config: JSON config object
    """
    @coroutine
    def post(self):
        self.client_settings(self.params_to_dict())
        self.render_json({"status": 200,
                          "message": "Client configuration stored."})

    @coroutine
    def get(self):
        self.render_json({"status": 200,
                         "content": self.client_settings()})
