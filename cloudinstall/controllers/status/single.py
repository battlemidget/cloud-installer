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

""" Single status deployment
"""

import logging

log = logging.getLogger('status.single')


def add_machines_to_juju(env, placement_controller):
    """ Adds machines to Juju in Single mode

    Arguments:
    env: Dict of config, juju, juju_state, maas, maas_state
    placement_controller: Placement UI Controller

    Returns:
    Dict of juju placements
    """
    juju_state = env['juju_state']
    juju = env['juju']
    juju_state.invalidate_status_cache()
    juju_m_idmap = {}
    for jm in juju_state.machines():
        response = juju.get_annotations(jm.machine_id,
                                        'machine')
        ann = response['Annotations']
        if 'instance_id' in ann:
            juju_m_idmap[ann['instance_id']] = jm.machine_id

    log.debug("existing juju machines: {}".format(juju_m_idmap))

    def get_created_machine_id(iid, response):
        d = response['Machines'][0]
        if d['Error']:
            raise Exception("Error adding machine '{}':"
                            "{}".format(iid, response))
        else:
            return d['Machine']

    for machine in placement_controller.machines_pending():
        if machine.instance_id in juju_m_idmap:
            machine.machine_id = juju_m_idmap[machine.instance_id]
            log.debug("machine instance_id {} already exists as #{}, "
                      "skipping".format(machine.instance_id,
                                        machine.machine_id))
            continue
        log.debug("adding machine with "
                  "constraints={}".format(machine.constraints))
        rv = juju.add_machine(constraints=machine.constraints)
        m_id = get_created_machine_id(machine.instance_id, rv)
        machine.machine_id = m_id
        rv = juju.set_annotations(m_id, 'machine',
                                  {'instance_id':
                                   machine.instance_id})
        juju_m_idmap[machine.instance_id] = m_id
    return juju_m_idmap
