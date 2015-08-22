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
from cloudinstall.signals import Signal
from cloudinstall.controllers.install import (InstallPathController,
                                              SingleInstallController)

log = logging.getLogger('cloudinstall.c.installbase')


class InstallController:

    """ Install controller """

    def __init__(self, ui, loop):
        self.ui = ui
        self.loop = loop
        self.signal = Signal()
        self.controllers = {
            "installpath": InstallPathController(self.ui,
                                                 self.signal),
            "singleinstall": SingleInstallController(self.ui,
                                                     self.signal)
        }
        self._connect_base_signals()

    def _connect_base_signals(self):
        """ Connect signals used in the core controller
        """
        signals = []

        # Add quit signal
        signals.append(('quit', self.loop.exit))
        signals.append(('stop-loop', self.loop.stop))
        signals.append(('refresh', self.loop.redraw_screen))
        self.signal.connect_signals(signals)

        # Registers signals from each controller
        for controller, controller_class in self.controllers.items():
            controller_class.register_signals()
        log.debug(self.signal)

    def update(self, *args, **kwargs):
        pass

    def start(self):
        """ Start installer eventloop
        """
        self.loop.set_alarm_in(0.05, self.install)
        self.loop.run()

    # Display Install view mode -----------------------------------------------
    #  Start the initial UI view.
    def install(self, *args, **kwargs):
        self.controllers['installpath'].install()
