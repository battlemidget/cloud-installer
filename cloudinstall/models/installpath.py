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
from cloudinstall.model import ModelPolicy


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

    install_descriptions = {
        'Single': [
            "Fully containerized OpenStack installation "
            "on a single machine.",
            "",
            "Use this option if you want a non-intrusive way to test out an ",
            "an OpenStack install where cleanup is as simple as removing the ",
            "parent LXC container."
        ],
        'Multi': [
            "OpenStack installation utilizing MAAS.",
            "",
            "Use this option if you have an existing MAAS setup and at least",
            "3 registered machines."
        ],
        'Landscape OpenStack Autopilot': [
            "The Canonical Distribution - "
            "Enterprise OpenStack Install and Management.",
            "",
            "Use this option if you want an enterprise-ready cloud with all ",
            "the tools needed to monitor and manage your cloud.",
            "",
            "This option requires you at least have 7 available machines ",
            "registered in MAAS containing at least 2 disks and 2 network ",
            "adapters each."
        ]
    }

    install_types = [
        ("Single",
         "install:single",
         "single"),
        ("Start Single Install",
         "install:single:start",
         "single_start"),
        ("Multi",
         "install:multi",
         "multi"),
        ("Landscape OpenStack Autopilot",
         "install:landscape",
         "landscape")
    ]

    def get_signals(self):
        return self.signals + self.install_types

    def get_menu(self):
        return self.install_types

    def get_signal_by_name(self, selection):
        for x, y, z in self.get_menu():
            if x == selection:
                return y

    def get_description(self, name):
        rows = len(self.install_descriptions[name])
        return (rows, "\n".join(self.install_descriptions[name]))
