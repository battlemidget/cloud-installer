#
# Copyright 2014 Canonical, Ltd.
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


# from cloudinstall.state import ControllerState
# import cloudinstall.utils as utils
# import sys
# import threading
from cloudinstall.ui.palette import STYLES
import logging
import urwid

log = logging.getLogger('cloudinstall.ev')


class EventLoop:

    """ Abstracts out event loops in different scenarios
    """

    def __init__(self, ui, config, log):
        self.ui = ui
        self.config = config
        self.log = log
        self.error_code = 0
        # self._callback_map = {}
        self.loop = self._build_loop()

        # if not self.config.getopt('headless'):
        #     self.loop = self._build_loop()
        #     self.loop.set_alarm_in(2, self.check_thread_exit_event)
        #     self._loop_thread = threading.current_thread()
        #     self._thread_exit_event = threading.Event()

    # def register_callback(self, key, val):
    #     """ Registers some additional callbacks that didn't make sense
    #     to be added as part of its initial creation

    #     TODO: Doubt this is the best way as its more of a band-aid
    #     to core.py/add_charm and hotkeys in the gui.
    #     """
    #     self._callback_map[key] = val

    def header_hotkeys(self, key):
        if key in ['q', 'Q']:
            self.exit(0)

    # def exit(self, err=0):
    #     self.error_code = err
    #     self.log.info("Stopping eventloop")
    #     if self.config.getopt('headless'):
    #         sys.exit(err)

    #     if threading.current_thread() == self._loop_thread:
    #         raise urwid.ExitMainLoop()
    #     else:
    #         self._thread_exit_event.set()
    #         log.debug("{} exiting, deferred UI exit "
    #                   "to main thread.".format(
    #                       threading.current_thread().name))

    def exit(self):
        raise urwid.ExitMainLoop()

    # def check_thread_exit_event(self, *args, **kwargs):
    #     if self._thread_exit_event.is_set():
    #         raise urwid.ExitMainLoop()
    #     self.loop.set_alarm_in(2, self.check_thread_exit_event)

    def redraw_screen(self):
        try:
            self.loop.draw_screen()
        except AssertionError as e:
            self.log.exception("exception failure in redraw_screen")
            raise e

    def set_alarm_in(self, interval, cb):
        self.loop.set_alarm_in(interval, cb)
        return

    def _build_loop(self):
        additional_opts = {
            'screen': urwid.raw_display.Screen(),
            'unhandled_input': self.header_hotkeys,
            'handle_mouse': False
        }
        additional_opts['screen'].set_terminal_properties(colors=256)
        additional_opts['screen'].reset_default_terminal_palette()
        return urwid.MainLoop(self.ui, STYLES, **additional_opts)

    def run(self):
        """ Run eventloop
        """
        try:
            self.loop.run()
        except:
            log.exception("Exception in ev.run():")
            raise
        return

    def __repr__(self):
        return "<eventloop urwid based on select()>"
