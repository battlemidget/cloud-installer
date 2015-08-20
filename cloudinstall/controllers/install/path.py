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

import cloudinstall.utils as utils
from cloudinstall.controller import ControllerPolicy
from cloudinstall.models import InstallPathModel
from cloudinstall.ui.views.install import InstallPathView

log = logging.getLogger("cloudinstall.c.i.installpath")


class InstallPathControllerException(Exception):
    pass


class InstallPathController(ControllerPolicy):
    """ Presents user with install selection type
    """
    def __init__(self, ui, signal):
        self.ui = ui
        self.signal = signal
        self.model = InstallPathModel()

    def install(self):
        """ load install path view """
        title = "Install Path Selection"
        excerpt = ("Highlight the type of installation you wish to make and "
                   "press ENTER to proceed.")
        self.ui.set_header(title, excerpt)
        self.ui.set_body(InstallPathView(self.model,
                                         self.signal))

    def set_install_type(self, result):
        """ Stores install selection type and writes config """
        config = utils.read_ini_existing()
        config['settings']['install_type'] = result
        log.debug("Set install type {} in config".format(result))
        utils.write_ini(config)
