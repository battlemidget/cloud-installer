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
import logging

from urwid import (Filler, Frame, WidgetWrap)

from cloudinstall.task import Tasker
from cloudinstall.ui.utils import check_encoding
from cloudinstall.ui.widgets import (StatusBarWidget,
                                     BannerWidget,
                                     HeaderWidget)
from cloudinstall.alarms import AlarmMonitor
from cloudinstall.ui.views import (ErrorView,
                                   ServicesView,
                                   NodeInstallWaitView)
from cloudinstall.machinewait import MachineWaitView
from cloudinstall.placement.ui import PlacementView
from cloudinstall.placement.ui.add_services_dialog import AddServicesDialog

log = logging.getLogger('tui')


def status_message(frame, text):
    frame.footer.message(text)
    frame.set_footer(frame.footer)


def status_error_message(frame, message):
    frame.footer.error_message(message)


def status_info_message(frame, message):
    frame.footer.info_message(
        "{}\N{HORIZONTAL ELLIPSIS}".format(message))


def set_openstack_rel(frame, release):
    frame.header.set_openstack_rel(release)


def render_services_view(frame, nodes, juju_state, maas_state, config):
    services_view = ServicesView(nodes, juju_state, maas_state,
                                 config)
    frame.body = services_view
    # header.set_show_add_units_hotkey(True)
    dc = config.getopt('deploy_complete')
    dcstr = "complete" if dc else "pending"
    rc = config.getopt('relations_complete')
    rcstr = "complete" if rc else "pending"
    ppc = config.getopt('postproc_complete')
    ppcstr = "complete" if ppc else "pending"
    status_info_message("Status: Deployments {}, "
                        "Relations {}, "
                        "Post-processing {} ".format(dcstr,
                                                     rcstr,
                                                     ppcstr))


def render_node_install_wait(frame, message=None, **kwargs):
    frame.body = NodeInstallWaitView(message, **kwargs)


def render_placement_view(frame, loop, config, cb):
    """ render placement view

    :param cb: deploy callback trigger
    """
    pc = None
    placement_view = PlacementView(pc, loop,
                                   config, cb)
    placement_view.update()
    frame.body = placement_view


def render_machine_wait_view(frame, config):
    current_installer = None
    machine_wait_view = MachineWaitView(
        current_installer, config)
    machine_wait_view.update()
    frame.body = machine_wait_view


def render_add_services_dialog(frame, deploy_cb, cancel_cb):
    def reset():
        add_services_dialog = None

    def cancel():
        reset()
        cancel_cb()

    def deploy():
        reset()
        deploy_cb()

    if add_services_dialog is None:
        add_services_dialog = AddServicesDialog(controller,
                                                deploy_cb=deploy,
                                                cancel_cb=cancel)
    add_services_dialog.update()
    frame.body = Filler(add_services_dialog)


def show_exception_message(frame, ex):
    msg = ("A fatal error has occurred: {}\n".format(ex.args[0]))
    log.error(msg)
    frame.body = ErrorView(ex.args[0])
    AlarmMonitor.remove_all()


def select_install_type(frame, install_types, cb):
    """ Dialog for selecting installation type
    """
    show_selector_with_desc(
        'Select the type of installation to perform',
        install_types,
        cb)


def tasker(loop, config):
    """ Interface with Tasker class

    :param loop: urwid.Mainloop
    :param dict config: config object
    """
    return Tasker(loop, config)


class TUI(WidgetWrap):
    key_conversion_map = {'tab': 'down', 'shift tab': 'up'}

    def __init__(self, header=None, body=None, footer=None):
        check_encoding()  # Make sure terminal supports utf8
        self.header = header if header else HeaderWidget()
        self.body = body if body else BannerWidget()
        self.footer = footer if footer else StatusBarWidget('')

        self.frame = Frame(self.body,
                           header=self.header,
                           footer=self.footer)
        super().__init__(self.frame)
