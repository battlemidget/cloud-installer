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

import logging
import time

from os import path, getenv

from operator import attrgetter

from uoilib.async import nb
from uoilib import utils
from uoilib.log import pretty_log

from .alarms import AlarmMonitor
from .state import get_state
from .maas import (
    connect_to_maas,
    FakeMaasState
)
from .charms import CharmQueue
from .placement.controller import (PlacementController,
                                   AssignmentType)
from .juju import (connect_to_juju, FakeJujuState)

log = logging.getLogger('core')


def authenticate_backends(env):
    """ Authenticates against Juju and MAAS backends

    Arguments:
    env: Dict of (config, maas, maas_state, juju, juju_state)

    Returns:
    In place update of env, returns nothing
    """
    if getenv("FAKE_API_DATA"):
        env['juju_state'] = FakeJujuState()
        env['maas_state'] = FakeMaasState()
    else:
        env['juju'], env['juju_state'] = connect_to_juju(env['config'])
        if env['config'].is_multi():
            creds = env['config'].getopt('maascreds')
            env['maas'], env['maas_state'] = connect_to_maas(creds)


def all_juju_machines_started(env, placement_controller):
    """ Returns if all juju machines have an agent_state of started

    Arguments:
    env: Dict of config, juju, juju_state, maas, maas_state
    placement_controller: Placement UI Controller

    Returns:
    Boolean
    """
    juju_state = env['juju_state']
    juju_state.invalidate_status_cache()
    n_needed = len(placement_controller.machines_pending())
    n_allocated = len([jm for jm in juju_state.machines()
                       if jm.agent_state == 'started'])
    return n_allocated >= n_needed


def commit_placement(env, ui, loop, nodes):
    juju_state = env['juju_state']
    maas_state = env['maas_state']
    config = env['config']
    config.setopt('current_state', get_state('controller', 'SERVICES'))
    ui.render_services_view(nodes, juju_state,
                            maas_state, config)
    loop.redraw_screen()
    deploy()


def deploy_using_placement(env, placement_controller, deployed_charm_classes):
    """Deploy charms using machine placement from placement controller,
    waiting for any deferred charms.  Then enqueue all charms for
    further processing and return.
    """
    juju_state = env['juju_state']

    log.info("Verifying service deployments")
    assigned_ccs = placement_controller.assigned_charm_classes()
    charm_classes = sorted(assigned_ccs,
                           key=attrgetter('deploy_priority'))

    def undeployed_charm_classes():
        return [c for c in charm_classes
                if c not in deployed_charm_classes]

    def update_pending_display():
        pending_names = [c.display_name for c in
                         undeployed_charm_classes()]
        log.info("Pending: {}".format(pending_names))

    while len(undeployed_charm_classes()) > 0:
        update_pending_display()

        for charm_class in undeployed_charm_classes():
            log.info(
                "Checking if {c} is deployed".format(
                    c=charm_class.display_name))

            service_names = [s.service_name for s in
                             juju_state.services]

            if charm_class.charm_name in service_names:
                log.info(
                    "{c} is already deployed, skipping".format(
                        c=charm_class.display_name))
                deployed_charm_classes.append(charm_class)
                continue

            err = try_deploy(charm_class)
            name = charm_class.display_name
            if err:
                log.debug(
                    "{} is waiting for another service, will"
                    " re-try in a few seconds".format(name))
                break
            else:
                log.debug("Issued deploy for {}".format(name))
                deployed_charm_classes.append(charm_class)

            juju_state.invalidate_status_cache()
            update_pending_display()

        num_remaining = len(undeployed_charm_classes())
        if num_remaining > 0:
            log.debug("{} charms pending deploy.".format(num_remaining))
            log.debug("deployed_charm_classes={}".format(
                pretty_log(deployed_charm_classes)))

            time.sleep(5)
        update_pending_display()


def try_deploy(env, charm_class, placement_controller):
    """ Try deployment

    Returns:
    True if deploy is deferred and should be tried again.
    """
    juju = env['juju']
    juju_state = env['juju_state']
    config = env['config']

    charm = charm_class(juju=juju,
                        juju_state=juju_state,
                        config=config)

    asts = placement_controller.get_assignments(charm_class)
    errs = []
    first_deploy = True
    for atype, ml in asts.items():
        for machine in ml:
            mspec = get_machine_spec(machine, atype)
            if mspec is None:
                errs.append(machine)
                continue

            if first_deploy:
                msg = "Deploying {c}".format(c=charm_class.display_name)
                if mspec != '':
                    msg += " to machine {mspec}".format(mspec=mspec)
                log.info(msg)
                deploy_err = charm.deploy(mspec)
                if deploy_err:
                    errs.append(machine)
                else:
                    first_deploy = False
            else:
                # service already deployed, need to add-unit
                msg = ("Adding one unit of "
                       "{c}".format(c=charm_class.display_name))
                if mspec != '':
                    msg += " to machine {mspec}".format(mspec=mspec)
                log.info(msg)
                deploy_err = charm.add_unit(machine_spec=mspec)
                if deploy_err:
                    errs.append(machine)
            if not deploy_err:
                placement_controller.mark_deployed(machine,
                                                   charm_class,
                                                   atype)

    had_err = len(errs) > 0
    if had_err and not config.getopt('headless'):
        log.warning("deferred deploying to these machines: {}".format(
            errs))
    return had_err


def get_machine_spec(env, maas_machine, atype, placement_controller):
    """Given a machine and assignment type, return a juju machine spec.

    Returns None on errors, and '' for the subordinate char placeholder.
    """
    juju_state = env['juju_state']
    if placement_controller.is_placeholder(maas_machine.instance_id):
        # placeholder machines do not use a machine spec
        return ""

    jm = next((m for m in juju_state.machines()
               if (m.instance_id == maas_machine.instance_id or
                   m.machine_id == maas_machine.machine_id)), None)
    if jm is None:
        log.error("could not find juju machine matching {}"
                  " (instance id {})".format(maas_machine,
                                             maas_machine.instance_id))

        return None

    if atype == AssignmentType.BareMetal \
       or atype == AssignmentType.DEFAULT:
        return jm.machine_id
    elif atype == AssignmentType.LXC:
        return "lxc:{}".format(jm.machine_id)
    elif atype == AssignmentType.KVM:
        return "kvm:{}".format(jm.machine_id)
    else:
        log.error("unexpected atype: {}".format(atype))
        return None


def wait_for_deployed_services_ready(env):
    """ Blocks until all deployed services attached units
    are in a 'started' state
    """
    juju_state = env['juju_state']
    config = env['config']
    if not juju_state:
        return

    log.info("Waiting for deployed services to be in a ready state.")

    not_ready_len = 0
    while not juju_state.all_agents_started():
        not_ready = [(a, b) for a, b in juju_state.get_agent_states()
                     if b != 'started']
        if len(not_ready) == not_ready_len:
            time.sleep(3)
            continue

        not_ready_len = len(not_ready)
        log.info("Checking availability of {} ".format(
            ", ".join(["{}:{}".format(a, b) for a, b in not_ready])))
        time.sleep(3)

    config.setopt('deploy_complete', True)
    log.info("Processing relations and finalizing services")


def enqueue_deployed_charms(env, ui, loop, nodes, deployed_charm_classes):
    """Send all deployed charms to CharmQueue for relation setting and
    post-proc.
    """
    config = env['config']
    juju = env['juju']
    juju_state = env['juju_state']
    maas_state = env['maas_state']
    charm_q = CharmQueue(config=config,
                         juju=juju, juju_state=juju_state,
                         deployed_charms=deployed_charm_classes)

    charm_q.watch_relations()
    charm_q.watch_post_proc()
    charm_q.is_running = True

    # Exit cleanly if we've finished all deploys, relations,
    # post processing, and running in headless mode.
    if config.getopt('headless'):
        while not config.getopt('postproc_complete'):
            log.info("Waiting for services to be started.")
            time.sleep(10)
        log.info("All services deployed, relations set, and started")
        loop.exit(0)

    log.info(
        "Services deployed, relationships still pending."
        " Please wait for all relations to be set before"
        " deploying additional services.")
    ui.render_services_view(nodes, juju_state,
                            maas_state, config)
    loop.redraw_screen()


def deploy_new_services(env, loop, ui, nodes):
    """Deploys newly added services in background thread.
    Does not attempt to create new machines.
    """
    config = env['config']
    juju_state = env['juju_state']
    maas_state = env['maas_state']
    config.setopt('current_state', get_state('controller', 'SERVICES'))
    ui.render_services_view(nodes, juju_state,
                            maas_state, config)
    loop.redraw_screen()

    deploy_using_placement()
    wait_for_deployed_services_ready()
    enqueue_deployed_charms()


def header_hotkeys(self, key, env, ui):
    config = env['config']
    kbd = config.kbd
    if not config.getopt('headless'):
        if key in kbd['views']['status']:
            self.ui.render_services_view(
                self.nodes, self.juju_state,
                self.maas_state, self.config)

        if key in kbd['views']['help']:
            self.config.setopt('current_state',
                               get_state('controller', 'HELP'),
                               keep_previous=True)
            self.ui.show_help_info()

        if key in kbd['views']['add_service']:
            self.config.setopt('current_state',
                               get_state('controller', 'ADD_SERVICES'),
                               keep_previous=True)

            self.ui.render_placement_view(self.loop,
                                          self.config,
                                          self.commit_placement)

            self.ui.render_add_services_dialog(
                nb(self.deploy_new_services),
                self.cancel_add_services)

        if key in kbd['global']['quit']:
            self.loop.exit(0)

        if key in kbd['global']['refresh']:
            self.ui.status_info_message("View was refreshed")

        if key in kbd['global']['esc']:
            self.config.setopt('current_state',
                               self.config.getopt('previous_state'))


def update(env, ui, *args, **kwargs):
    """Render UI according to current state and reset timer
    """
    interval = 1
    config = env['config']
    loop = env['loop']
    current_state = config.getopt('current_state')
    if current_state == get_state('controller', 'PLACEMENT'):
        ui.render_placement_view(loop,
                                 config,
                                 commit_placement)
    elif current_state == get_state('controlelr', 'INSTALL_WAIT'):
        ui.render_node_install_wait(message="Waiting...")
        interval = config.node_install_wait_interval
    else:
        update_node_states()
        AlarmMonitor.add_alarm(loop.set_alarm_in(interval,
                                                 update),
                               "core-controller-update")


def update_node_states(self):
    """ Updating node states

    PegasusGUI only
    """
    if not self.juju_state:
        return
    deployed_services = sorted(self.juju_state.services,
                               key=attrgetter('service_name'))
    deployed_service_names = [s.service_name for s in deployed_services]

    charm_classes = sorted(
        [m.__charm_class__ for m in
         utils.load_charms(self.config.getopt('charm_plugin_dir'))
         if m.__charm_class__.charm_name in
         deployed_service_names],
        key=attrgetter('charm_name'))

    self.nodes = list(zip(charm_classes, deployed_services))

    if len(self.nodes) == 0:
        return
    else:
        if not self.ui.services_view:
            self.ui.render_services_view(
                self.nodes, self.juju_state,
                self.maas_state, self.config)
        else:
            self.ui.services_view.refresh_nodes(self.nodes)


def cancel_add_services(env, ui, nodes):
    """User cancelled add-services screen.
    Just redisplay services view.
    """
    config = env['config']
    loop = env['loop']
    juju_state = env['juju_state']
    maas_state = env['maas_state']
    config.setopt('current_state', get_state('controller', 'SERVICES'))
    ui.render_services_view(nodes, juju_state,
                            maas_state, config)
    loop.redraw_screen()


def start(env):
    """ Starts UI loop
    """
    config = env['config']
    loop = env['loop']

    if config.getopt('headless'):
        authenticate_backends(env)
    else:
        # rel = config.getopt('openstack_release')
        # label = OPENSTACK_RELEASE_LABELS[rel]
        # self.ui.set_openstack_rel(label)
        authenticate_backends(env)

        loop.build_loop(unhandled_input=header_hotkeys)

        AlarmMonitor.add_alarm(loop.set_alarm_in(0, update),
                               "controller-start")
        config.setopt("gui_started", True)
        loop.run()
        loop.close()


def deploy(env):
    """ Deploy services

    Arguments:
    env: Dict of (config, maas, maas_state, juju, juju_state)
    """
    pc = placement_controller()
    config = env['config']
    maas = env['maas']
    juju_state = env['juju_state']

    if config.is_multi():

        # now all machines are added
        maas.tag_fpi(maas.nodes)
        maas.nodes_accept_all()
        maas.tag_name(maas.nodes)

        while not all_maas_machines_ready(env, pc):
            time.sleep(3)

        add_machines_to_juju_multi(env, pc)

    elif config.is_single():
        juju_m_idmap = add_machines_to_juju_single(env, pc)

    # Quiet out some of the logging
    _previous_summary = None
    while not all_juju_machines_started(env, pc):
        sd = juju_state.machines_summary()
        summary = ", ".join(["{} {}".format(v, k) for k, v
                             in sd.items()])
        if summary != _previous_summary:
            log.info("Waiting for machines to "
                     "start: {}".format(summary))
            _previous_summary = summary

        time.sleep(1)

    if len(juju_state.machines()) == 0:
        raise Exception("Expected some juju machines started.")

    config.setopt('current_state', get_state('controller', 'SERVICES'))
    ppc = config.getopt("postproc_complete")
    rc = config.getopt("relations_complete")
    if not ppc or not rc:
        if config.is_single():
            controller_machine = juju_m_idmap['controller']
            configure_lxc_network(env, controller_machine)

        deploy_using_placement(env)
        wait_for_deployed_services_ready(env)
        enqueue_deployed_charms(env)
    else:
        log.info("Deployment complete.")
