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

import logging

log = logging.getLogger('state')

states = {
    'install': {
        'RUNNING': 0,
        'NODE_WAIT': 1
    },

    'controller': {
        'INSTALL_WAIT': 0,
        'PLACEMENT': 1,
        'SERVICES': 2,
        'ADD_SERVICES': 3,
        'HELP': 4
    },

    'charm': {
        'REQUIRED': 0,
        'OPTIONAL': 1,
        'CONFLICTED': 2
    }
}


def get_state(key, state):
    try:
        states[key][state]
    except:
        log.error("Unknown state: {}".format(state))
