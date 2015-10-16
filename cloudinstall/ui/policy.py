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


""" UI Policy """

from abc import ABC, abstractmethod


class UIPolicyException(Exception):
    "Problem in UI Policy"


class UIPolicy(ABC):
    """ policy contract
    """
    def __init__(self, common):
        self.loop = common['loop']
        self.config = common['config']

    # Logging Policy
    @abstractmethod
    def log_info(self, msg):
        """ Logger INFO
        """
        pass

    @abstractmethod
    def log_error(self, msg):
        """ Logger ERROR
        """
        pass

    @abstractmethod
    def log_debug(self, msg):
        """ Logger DEBUG
        """
        pass

    @abstractmethod
    def status_info(self, msg):
        """ Status info message
        """
        pass

    @abstractmethod
    def status_error(self, msg):
        """ Status error message
        """
        pass

    @abstractmethod
    def step_info(self, msg):
        """ Step info
        """
        pass
