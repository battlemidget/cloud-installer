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

from __future__ import unicode_literals
from operator import attrgetter
import logging
import random
from urwid import (Text, Columns, WidgetWrap,
                   Pile, ListBox, Divider)
from cloudinstall.status import get_sync_status
from cloudinstall import utils
from cloudinstall.ui.widgets import MachineWidget
from cloudinstall.ui.utils import Color


log = logging.getLogger('cloudinstall.ui.views.services')


class ServiceColumn:

    def __init__(self):
        self.columns = {}

    def add(self, key, heading):
        self.columns[key] = Pile([
            Color.column_header(Text(heading))
        ])

    def get(self, key):
        return self.columns[key]

    def add_to(self, key, w):
        """ Append item to specified column pile
        """
        pile = self.get(key)
        pile.contents.append((w, pile.options()))
        pile.contents.append((
            Divider("\N{BOX DRAWINGS LIGHT HORIZONTAL}"),
            pile.options()))

    def contents(self, key):
        return self.get(key).contents

    def render(self):
        """ Renders columns with proper spacing
        """
        items = []
        for col in self.columns.keys():
            # Dont set fixed width for service name
            if col == "services":
                items.append(self.columns[col])
                continue
            items.append(('fixed', len(col)+1, self.columns[col]))
        return items


class ServicesView(WidgetWrap):

    view_columns = [
        ('icon', ""),
        ('display_name', "Service"),
        ('agent_state', "Status"),
        ('public_address', "IP"),
        ('container', "Container"),
        ('machine', "Machine"),
        ('arch', "Arch"),
        ('cpu_cores', "Cores"),
        ('mem', "Mem"),
        ('storage', "Storage")
    ]

    def __init__(self, nodes, juju_state, maas_state, config):
        self.columns = ServiceColumn()
        self.nodes = [] if nodes is None else nodes
        self.juju_state = juju_state
        self.maas_state = maas_state
        self.config = config
        self.machine_w = None
        self.log_cache = None

        for key, label in self.view_columns:
            self.columns.add(key, label)
        super().__init__(self._build_widget())

    def _build_widget(self):
        for node in self.nodes:
            charm_class, service = node
            if len(service.units) > 0:
                for u in sorted(service.units, key=attrgetter('unit_name')):
                    self.initialize_column(u, charm_class)
        return ListBox(Columns(self.columns.render()))

    def update(self, nodes):
        """ Updates individual machine information
        """
        for node in nodes:
            charm_class, service = node
            if len(service.units) > 0:
                for u in sorted(service.units, key=attrgetter('unit_name')):
                    # These are really the only dynamic properties
                    self.machine_w.public_address.set_text(u.public_address)
                    self.machine_w.agent_state.set_text(u.agent_state)

    def _generate_status(self, unit, charm_class):
        result = {
            "icon": None,
            "error": None
        }
        # unit.agent_state may be "pending" despite errors elsewhere,
        # so we check for error_info first.
        # if the agent_state is "error", _detect_errors returns that.
        error_info = self._detect_errors(unit, charm_class)

        if error_info:
            result['icon'] = Color.error_icon(
                Text("\N{TETRAGRAM FOR FAILURE}"))
            if unit.agent_state != "error":
                result['error'] = unit.agent_state
            return result
        elif unit.agent_state == "pending":
            pending_status = [Color.pending_icon(Text("\N{CIRCLED BULLET}")),
                              Color.pending_icon(
                                  Text("\N{CIRCLED WHITE BULLET}")),
                              Color.pending_icon_on(Text("\N{FISHEYE}"))]
            result['icon'] = random.choice(pending_status)
        elif unit.agent_state == "installed":
            result['icon'] = Color.pending_icon(
                Text("\N{HOURGLASS}"))
        elif unit.agent_state == "started":
            result['icon'] = Color.success_icon(Text("\u2713"))
        elif unit.agent_state == "stopped":
            result['icon'] = Color.error_icon(Text("\N{BLACK FLAG}"))
        elif unit.agent_state == "down":
            result['icon'] = Color.error_icon(
                Text("\N{DOWNWARDS BLACK ARROW}"))
        else:
            # shouldn't get here
            result['icon'] = "?"

        return result

    def initialize_column(self, unit, charm_class):
        """ Initial rendering of columns with service information
        """
        hwinfo = self._get_hardware_info(unit)
        self.machine_w = MachineWidget(unit, charm_class, hwinfo)

        status = self._generate_status(unit, charm_class)
        self.machine_w.icon = status['icon']
        self.columns.add_to('icon', self.machine_w.icon)

        if 'glance-simplestreams-sync' in unit.unit_name:
            status_oneline = get_sync_status().replace("\n", " - ")
            self.machine_w.display_name.set_text(
                "{} ({})".format(self.machine_w.display_name, status_oneline))

        if status['error']:
            self.machine_w.public_address.set_text(status['error'])
        else:
            self.machine_w.public_address.set_text("IP Pending")

        for k, label in self.view_columns:
            self.columns.add_to(k, getattr(self.machine_w, k))

    def _get_hardware_info(self, unit):
        """Get hardware info from juju or maas

        Returns list of text and formatting tuples
        """
        juju_machine = self.juju_state.machine(unit.machine_id)
        maas_machine = None
        if self.maas_state:
            maas_machine = self.maas_state.machine(juju_machine.instance_id)

        m = juju_machine
        if juju_machine.arch == "N/A":
            if maas_machine:
                m = maas_machine
            else:
                try:
                    return self._get_container_info(unit)
                except:
                    log.exception(
                        "failed to get container info for unit {}.".format(
                            unit))

        hw_info = self._hardware_info_for_machine(m)
        hw_info['machine'] = juju_machine.machine_id
        return hw_info

    def _get_container_info(self, unit):
        """Attempt to get hardware info of host machine for a unit that looks
        like a container.

        """
        base_machine = self.juju_state.base_machine(unit.machine_id)

        if base_machine.arch == "N/A" and self.maas_state is not None:
            m = self.maas_state.machine(base_machine.instance_id)
        else:
            m = base_machine

        # FIXME: Breaks single install status display
        # base_id, container_type, container_id = unit.machine_id.split('/')
        # ctypestr = dict(kvm="VM", lxc="Container")[container_type]

        # rl = ["{} {} (Machine {}".format(ctypestr, container_id,
        #                                  base_id)]
        try:
            container_id = unit.machine_id.split('/')[-1]
        except:
            log.exception("ERROR: base_machine is {} and m is {}, "
                          "and unit.machine_id is {}".format(
                              base_machine, m, unit.machine_id))
            return "?"

        base_id = base_machine.machine_id
        hw_info = self._hardware_info_for_machine(m)
        hw_info['machine'] = base_id
        hw_info['container'] = container_id
        return hw_info

    def _hardware_info_for_machine(self, m):
        return {"arch": m.arch,
                "cpu_cores": m.cpu_cores,
                "mem": m.mem,
                "storage": m.storage,
                "container": 'x',
                "machine": 0}

    def _detect_errors(self, unit, charm_class):
        """Look in multiple places for an error.

        Return error info string if present,
        or None if no error is found
        """
        unit_machine = self.juju_state.machine(unit.machine_id)

        if unit.agent_state == "error":
            return unit.agent_state_info.lstrip()

        err_info = ""

        if unit.agent_state == 'pending' and \
           unit_machine.agent_state is '' and \
           unit_machine.agent_state_info is not None:

            # detect MAAS API errors, returned as 409 conflict:
            if "409" in unit_machine.agent_state_info:
                if charm_class.constraints is not None:
                    err_info = "Found no machines meeting constraints: "
                    err_info += ', '.join(["{}='{}'".format(k, v) for k, v
                                           in charm_class.constraints.items()])
                else:
                    err_info += "No machines available for unit."
            else:
                err_info += unit_machine.agent_state_info
            return err_info
        return None

    def get_log_text(self, unit_name):
        name = '-'.join(unit_name.split('/'))
        cmd = ("sudo grep {unit} /var/log/juju-ubuntu-local/all-machines.log "
               " | tail -n 2")
        cmd = cmd.format(unit=name)
        out = utils.get_command_output(cmd)
        if out['status'] == 0 and len(out['output']) > 0:
            return out['output']
        else:
            return "No log matches for {}".format(name)
