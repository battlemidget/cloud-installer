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

""" Factory for deployments
"""

from .controllers.deploy import (multi, single)


class IDeploy:
    """ Provides a factory for status deployments
    """
    def __init__(self, env):
        """ init

        Arguments:
        env: mapping of loop, config, juju, juju_env, maas_env, maas_state
        """
        self.config = env['config']
        if self.config.is_single():
            self.driver = single
        elif self.config.is_multi():
            self.driver = multi
        else:
            raise Exception('Unable to determine factory driver')
