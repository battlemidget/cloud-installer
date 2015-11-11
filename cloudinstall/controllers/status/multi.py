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

""" Multi status deployment
"""

from macumba import Jobs as JujuJobs
from .maas import (connect_to_maas, FakeMaasState,
                   MaasMachineStatus)
from uoilib.log import pretty_log
import logging

log = logging.getLogger('status.multi')


def add_machines_to_juju(env, placement_controller):
    """
    Adds each of the machines used for the placement to juju, if it
    isn't already there.

    Arguments:
    env: Dict of config, juju, juju_state, maas, maas_state
    placement_controller: Placement UI Controller
    """
    juju_state = env['juju_state']
    juju = env['juju']
    juju_state.invalidate_status_cache()
    juju_ids = [jm.instance_id for jm in juju_state.machines()]

    machine_params = []
    for maas_machine in placement_controller.machines_pending():
        if maas_machine.instance_id in juju_ids:
            # ignore machines that are already added to juju
            continue
        cd = dict(tags=[maas_machine.system_id])
        mp = dict(Series="", ContainerType="", ParentId="",
                  Constraints=cd, Jobs=[JujuJobs.HostUnits])
        machine_params.append(mp)

    if len(machine_params) > 0:
        log.debug("calling add_machines with params:"
                  " {}".format(pretty_log(machine_params)))
        rv = juju.add_machines(machine_params)
        log.debug("add_machines returned '{}'".format(rv))


def all_machines_ready(env, placement_controller):
    """ Waits for MAAS machines to be in a READY state

    Arguments:
    env: Dict of config, juju, juju_state, maas, maas_state
    placement_controller: Placement UI controller

    Returns:
    True/False based on result of maas machine states
    """
    maas_state = env['maas_state']
    maas_state.invalidate_nodes_cache()

    cons = env['config'].getopt('constraints')
    needed = set([m.instance_id for m in
                  placement_controller.machines_pending()])
    ready = set([m.instance_id for m in
                 maas_state.machines(MaasMachineStatus.READY,
                                     constraints=cons)])
    allocated = set([m.instance_id for m in
                     maas_state.machines(MaasMachineStatus.ALLOCATED,
                                         constraints=cons)
                     ])

    summary = ", ".join(["{} {}".format(v, k) for k, v in
                         maas_state.machines_summary().items()])
    log.info("Waiting for {} maas machines to be ready."
             " Machines Summary: {}".format(len(needed),
                                            summary))
    if not needed.issubset(ready.union(allocated)):
        return False
    return True
