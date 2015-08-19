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

""" Install Path View

Diagram:

Ubuntu OpenStack Installer - Choose Install Type

                ( ) Single              |  Single Install
                ( ) Multi               |  Multi Install
                ( ) Landscape Autopilot |  Autopilot install

                               [ Confirm ]
                               [ Cancel  ]
"""

import logging


log = logging.getLogger("cloudinstall.u.v.i.path")


class InstallPathViewException(Exception):
    "Problem in install path selection view"


class InstallPathView(WidgetWrap):
    def __init__(self):
        pass
