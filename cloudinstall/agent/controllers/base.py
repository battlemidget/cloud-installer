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

import json
from tornado.web import RequestHandler


class BaseHandler(RequestHandler):
    def render_json(self, content):
        content_json = json.dumps(content)
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.write(content_json)
        self.finish()

    def client_settings(self, items=None):
        if isinstance(items, dict):
            self.application.settings['client'] = items
        return self.application.settings['client']

    @property
    def run_as(self):
        user = self.application.settings['run_as']
        if user is None:
            return "ubuntu"
        return user

    def params_to_dict(self, content):
        if self.request.headers["Content-Type"].startswith("application/json"):
            json_args = json.loads(self.request.body)
        else:
            json_args = None
        return json_args
