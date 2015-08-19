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

    # def _set_install_type(self, install_type):
    #     self.install_type = install_type
    #     self.ui.show_password_input(
    #         'Create a New OpenStack Password', self._save_password)

    # def _save_password(self, creds):
    #     """ Checks passwords match and proceeds
    #     """
    #     password = creds['password'].value
    #     if password.isdigit():
    #         self.ui.flash("Password must not be a number")
    #         self.loop.redraw_screen()
    #         return self.ui.show_password_input(
    #             'Create a New OpenStack Password', self._save_password)
    #     if 'confirm_password' in creds:
    #         confirm_password = creds['confirm_password'].value
    #     if password and password == confirm_password:
    #         self.ui.flash_reset()
    #         self.loop.redraw_screen()
    #         self.config.setopt('openstack_password', password)
    #         self.ui.hide_show_password_input()
    #         self.do_install()
    #     else:
    #         self.ui.flash('Passwords did not match')
    #         self.loop.redraw_screen()
    #         return self.ui.show_password_input(
    #             'Create a New OpenStack Password', self._save_password)

    # def _save_maas_creds(self, creds):
    #     self.ui.hide_widget_on_top()
    #     maas_server = creds['maas_server'].value
    #     maas_apikey = creds['maas_apikey'].value

    #     if maas_server and maas_apikey:
    #         if maas_server.startswith("http"):
    #             self.ui.flash('Please enter the MAAS server\'s '
    #                           'IP address only, not a full URL')
    #             return self.ui.select_maas_type(self._save_maas_creds)
    #         self.config.setopt('maascreds', dict(api_host=maas_server,
    #                                              api_key=maas_apikey))
    #         log.info("Performing a Multi Install with existing MAAS")
    #         return self.MultiInstallExistingMaas(
    #             self.loop, self.ui, self.config).run()
    #     else:
    #         self.ui.flash('Please enter the MAAS server\'s '
    #                       'IP address and API key to proceed.')
    #         return self.ui.select_maas_type(self._save_maas_creds)

    def install(self):
        """ load install path view """
        title = "Install Path Selection"
        excerpt = ("Highlight the type of installation you wish to make and "
                   "press ENTER to proceed.")
        self.ui.set_header(title, excerpt)
        self.ui.set_body(InstallPathView(self.model,
                                         self.signal))
