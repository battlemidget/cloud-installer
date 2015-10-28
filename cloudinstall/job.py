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

""" Job encapsulates each install/deploy step to be run
through a queue
"""
import time
from queue import Queue
from contextlib import ContextDecorator
import logging

log = logging.getLogger('cloudinstall.job')


class job(ContextDecorator):
    """ Tracks jobs execution time
    """

    def __init__(self, name):
        self.name = name
        self.runtime = time.time()

    def __enter__(self):
        """ Pre hook for setting up requirements in a job
        """
        log.debug('Started job: {}'.format(self.name))

    def __exit__(self, exc_type, exc, exc_tb):
        """ Performs tasks
        """
        elapsed_time = time.time() - self.runtime
        log.debug('Completed job: {} '
                  '(elapsed {:2.2f} sec(s))'.format(self.name,
                                                    elapsed_time))


class JobQueue:
    def __init__(self):
        self.q = Queue()

    def add(self, job):
        """ add job to queue
        """
        self.q.put(job)

    def process(self):
        """ Processes jobs
        """
        while not self.q.empty():
            try:
                job = self.q.get()
                job()
                self.q.task_done()
            except:
                raise Exception('Problem running a job')
