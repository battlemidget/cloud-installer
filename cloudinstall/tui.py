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

""" UI interface to the OpenStack Installer """

from __future__ import unicode_literals
import sys
import logging

import urwid
from urwid import (Text,
                   Filler, Frame, WidgetWrap, Button,
                   Pile, Divider)

from cloudinstall.task import Tasker
from cloudinstall.ui import (SelectorWithDescription,
                             PasswordInput,
                             MaasServerInput,
                             LandscapeInput)
from cloudinstall.ui.widgets import (StatusBarWidget,
                                     BannerWidget,
                                     HeaderWidget)
from cloudinstall.alarms import AlarmMonitor
from cloudinstall.ui.views import (ErrorView,
                                   ServicesView,
                                   HelpView,
                                   NodeInstallWaitView)
from cloudinstall.ui.utils import Color, Padding
from cloudinstall.machinewait import MachineWaitView
from cloudinstall.placement.ui import PlacementView
from cloudinstall.placement.ui.add_services_dialog import AddServicesDialog

log = logging.getLogger('cloudinstall.gui')


class StepInfo(WidgetWrap):

    def __init__(self, msg=None):
        if not msg:
            msg = "Processing."
        items = [
            Padding.center_60(Text("Information", align="center")),
            Padding.center_60(
                Divider("\N{BOX DRAWINGS LIGHT HORIZONTAL}", 1, 1)),
            Padding.center_60(Text(msg))
        ]
        super().__init__(Filler(Pile(items), valign='middle'))

    def _build_buttons(self):
        buttons = [
            Padding.line_break(""),
            Color.button_secondary(
                Button("Quit", self.cancel),
                focus_map='button_secondary focus'),
        ]
        return Pile(buttons)

    def cancel(self, button):
        raise SystemExit("Installation cancelled.")


def _check_encoding():
    """Set the Urwid global byte encoding to utf-8.

    Exit the application if, for some reasons, the change does not have effect.
    """
    urwid.set_encoding('utf-8')
    if not urwid.supports_unicode():
        # Note: the following message must only include ASCII characters.
        msg = (
            'Error: your terminal does not seem to support UTF-8 encoding.\n'
            'Please check your locale settings.\n'
            'On Ubuntu, running the following might fix the problem:\n'
            '  sudo locale-gen en_US.UTF-8\n'
            '  sudo dpkg-reconfigure locales'
        )
        sys.exit(msg.encode('ascii'))


class TUI(WidgetWrap):
    key_conversion_map = {'tab': 'down', 'shift tab': 'up'}

    def __init__(self, header=None, body=None, footer=None):
        _check_encoding()  # Make sure terminal supports utf8
        self.header = header if header else HeaderWidget()
        self.body = body if body else BannerWidget()
        self.footer = footer if footer else StatusBarWidget('')

        self.frame = Frame(self.body,
                           header=self.header,
                           footer=self.footer)

        self.services_view = None
        self.placement_view = None
        self.controller = None
        self.machine_wait_view = None
        self.add_services_dialog = None
        super().__init__(self.frame)

    def keypress(self, size, key):
        key = self.key_conversion_map.get(key, key)
        return super().keypress(size, key)

    def focus_next(self):
        if hasattr(self.frame.body, 'scroll_down'):
            self.frame.body.scroll_down()

    def focus_previous(self):
        if hasattr(self.frame.body, 'scroll_up'):
            self.frame.body.scroll_up()

    def focus_first(self):
        if hasattr(self.frame.body, 'scroll_top'):
            self.frame.body.scroll_top()

    def focus_last(self):
        if hasattr(self.frame.body, 'scroll_bottom'):
            self.frame.body.scroll_bottom()

    def show_help_info(self):
        self.controller = self.frame.body
        AlarmMonitor.remove_all()
        self.frame.body = HelpView()

    def show_step_info(self, msg):
        self.frame.body = StepInfo(msg)

    def show_selector_with_desc(self, title, opts, cb):
        self.frame.body = SelectorWithDescription(title, opts, cb)

    def show_password_input(self, title, cb):
        self.frame.body = PasswordInput(title, cb)

    def show_maas_input(self, title, cb):
        self.frame.body = MaasServerInput(title, cb)

    def show_landscape_input(self, title, cb):
        self.frame.body = LandscapeInput(title, cb)

    def set_pending_deploys(self, pending_charms):
        self.frame.footer.set_pending_deploys(pending_charms)

    def flash(self, msg):
        self.frame.body.flash("{}\N{HORIZONTAL ELLIPSIS}".format(msg))

    def flash_reset(self):
        self.frame.body.flash_reset()

    def status_message(self, text):
        self.frame.footer.message(text)
        self.frame.set_footer(self.frame.footer)

    def status_error_message(self, message):
        self.frame.footer.error_message(message)

    def status_info_message(self, message):
        self.frame.footer.info_message(
            "{}\N{HORIZONTAL ELLIPSIS}".format(message))

    def set_openstack_rel(self, release):
        self.frame.header.set_openstack_rel(release)

    def clear_status(self):
        self.frame.footer = None
        self.frame.set_footer(self.frame.footer)

    def render_services_view(self, nodes, juju_state, maas_state, config):
        self.services_view = ServicesView(nodes, juju_state, maas_state,
                                          config)
        self.frame.body = self.services_view
        self.header.set_show_add_units_hotkey(True)
        dc = config.getopt('deploy_complete')
        dcstr = "complete" if dc else "pending"
        rc = config.getopt('relations_complete')
        rcstr = "complete" if rc else "pending"
        ppc = config.getopt('postproc_complete')
        ppcstr = "complete" if ppc else "pending"
        self.status_info_message("Status: Deployments {}, "
                                 "Relations {}, "
                                 "Post-processing {} ".format(dcstr,
                                                              rcstr,
                                                              ppcstr))

    def render_node_install_wait(self, message=None, **kwargs):
        self.frame.body = NodeInstallWaitView(message, **kwargs)

    def render_placement_view(self, loop, config, cb):
        """ render placement view

        :param cb: deploy callback trigger
        """
        if self.placement_view is None:
            assert self.controller is not None
            pc = self.controller.placement_controller
            self.placement_view = PlacementView(self, pc, loop,
                                                config, cb)
        self.placement_view.update()
        self.frame.body = self.placement_view

    def render_machine_wait_view(self, config):
        if self.machine_wait_view is None:
            self.machine_wait_view = MachineWaitView(
                self, self.current_installer, config)
        self.machine_wait_view.update()
        self.frame.body = self.machine_wait_view

    def render_add_services_dialog(self, deploy_cb, cancel_cb):
        def reset():
            self.add_services_dialog = None

        def cancel():
            reset()
            cancel_cb()

        def deploy():
            reset()
            deploy_cb()

        if self.add_services_dialog is None:
            self.add_services_dialog = AddServicesDialog(self.controller,
                                                         deploy_cb=deploy,
                                                         cancel_cb=cancel)
        self.add_services_dialog.update()
        self.frame.body = Filler(self.add_services_dialog)

    def show_exception_message(self, ex):
        msg = ("A fatal error has occurred: {}\n".format(ex.args[0]))
        log.error(msg)
        self.frame.body = ErrorView(ex.args[0])
        AlarmMonitor.remove_all()

    def select_install_type(self, install_types, cb):
        """ Dialog for selecting installation type
        """
        self.show_selector_with_desc(
            'Select the type of installation to perform',
            install_types,
            cb)

    def __repr__(self):
        return "<Ubuntu OpenStack Installer GUI Interface>"

    def tasker(self, loop, config):
        """ Interface with Tasker class

        :param loop: urwid.Mainloop
        :param dict config: config object
        """
        return Tasker(self, loop, config)

    def exit(self, loop=None):
        """ Provide exit loop helper

        :param loop: Just a placeholder, exit with urwid.
        """
        urwid.ExitMainLoop()
