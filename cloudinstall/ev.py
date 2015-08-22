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

from cloudinstall.ui.palette import STYLES
import logging
from tornado.ioloop import IOLoop
import urwid

log = logging.getLogger('cloudinstall.ev')


class EventLoop:

    """ Abstracts out event loop
    """

    def __init__(self, ui, log):
        self.ui = ui
        self.log = log
        self.error_code = 0
        self.loop = self._build_loop()

    def header_hotkeys(self, key):
        pass

    def exit(self):
        raise urwid.ExitMainLoop()

    def stop(self):
        self.loop.stop()

    def redraw_screen(self):
        try:
            self.loop.draw_screen()
            log.debug("Screen was redrawn.")
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
        evl = urwid.TornadoEventLoop(IOLoop())
        return urwid.MainLoop(
            self.ui, STYLES, event_loop=evl, **additional_opts)

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
