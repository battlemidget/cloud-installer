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

import unittest

from cloudinstall.ui.notify import set_stream
from cloudinstall.ui.stream import (ConsoleStream,
                                    UrwidStream)


class TestConsoleNotifyStream(unittest.TestCase):
    def setUp(self):
        self.stream = set_stream('headless')

    def test_console_stream(self):
        self.assertIsInstance(self.stream, ConsoleStream)


class TestUrwidNotifyStream(unittest.TestCase):
    def setUp(self):
        self.stream = set_stream('urwid')

    def test_urwid_stream(self):
        self.assertIsInstance(self.stream, UrwidStream)


class TestInvalidNotifyStream(unittest.TestCase):
    def test_invalid_stream(self):
        with self.assertRaises(Exception):
            set_stream('bongodrums')
