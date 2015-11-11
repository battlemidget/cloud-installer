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

""" Async Handler
Provides async operations for various api calls and other non-blocking
work.
The way this works is you create your non-blocking thread:
.. code::
    def my_async_method(self):
        pool.submit(func, *args)

    # In your controller you would then call using coroutines
    @coroutine
    def do_async_action(self):
        try:
            yield my_async_method()
            # Move to next coroutine or return if finish
            self.do_second_async_action()
        except Exeception as e:
            log.exception("Failed in our non-blocking code.")
"""

import logging
from functools import partial
from concurrent.futures import ThreadPoolExecutor
log = logging.getLogger("cloudinstall.async")
pool = ThreadPoolExecutor(1)


def nb(func, *args, **kwargs):
    log.debug(
        'calling non-blocking func: {} '
        '(args: {}, kwds: {})'.format(func, args, kwargs))
    return pool.submit(partial(func, *args, **kwargs))
