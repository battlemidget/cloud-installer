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

import logging
from subiquity.model import ModelPolicy


log = logging.getLogger('subiquity.models.installpath')


class InstallPathModel(ModelPolicy):
    """ Model representing install path selection
    """
    prev_signal = None

    signals = [
        ("Install path view",
         'installpath:show',
         'install')
    ]

    install_types = [
        ("Single - "
         "Fully containerized OpenStack installation "
         "on a single machine.",
         "installpath:single",
         "install_single"),
        ("Multi - OpenStack installation utilizing MAAS.",
         "installpath:multi",
         "install_multi"),
        ("Landscape OpenStack Autopilot - "
         "The Canonical Distribution "
         "- Enterprise Openstack Install and Management.",
         "installpath:landscape",
         "install_landscape")
    ]

    def get_signals(self):
        return self.signals + self.install_types

    def get_menu(self):
        return self.install_types

    def get_signal_by_name(self, selection):
        for x, y, z in self.get_menu():
            if x == selection:
                return y
