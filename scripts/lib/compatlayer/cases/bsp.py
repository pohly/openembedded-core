# Copyright (C) 2017 Intel Corporation
# Released under the MIT license (see COPYING.MIT)

import unittest

from compatlayer import LayerType, get_signatures
from compatlayer.case import OECompatLayerTestCase

class BSPCompatLayer(OECompatLayerTestCase):
    @classmethod
    def setUpClass(self):
        if self.tc.layer['type'] != LayerType.BSP:
            raise unittest.SkipTest("BSPCompatLayer: Layer %s isn't BSP one." %\
                self.tc.layer['name'])

    def test_bsp_defines_machines(self):
        self.assertTrue(self.tc.layer['conf']['machines'], 
                "Layer is BSP but doesn't defines machines.")

    def test_bsp_no_set_machine(self):
        from oeqa.utils.commands import get_bb_var

        machine = get_bb_var('MACHINE')
        self.assertEqual(self.td['bbvars']['MACHINE'], machine,
                msg="Layer %s modified machine %s -> %s" % \
                    (self.tc.layer['name'], self.td['bbvars']['MACHINE'], machine))


    def test_machine_world(self):
        '''
        "bitbake world" is expected to work regardless which machine is selected.
        BSP layers sometimes break that by enabling a recipe for a certain machine
        without checking whether that recipe actually can be built in the current
        distro configuration (for example, OpenGL might not enabled).

        This test iterates over all machines. It would be nicer to instantiate
        it once per machine. It merely checks for errors during parse
        time. It does not actually attempt to build anything.
        '''

        if not self.td['machines']:
            self.skipTest('No machines set with --machines.')
        msg = []
        for machine in self.td['machines']:
            # In contrast to test_machine_signatures() below, errors are fatal here.
            try:
                get_signatures(self.td['builddir'], failsafe=False, machine=machine)
            except RuntimeError as ex:
                msg.append(str(ex))
        if msg:
            msg.insert(0, 'The following machines broke a world build:')
            self.fail('\n'.join(msg))

    def test_machine_signatures(self):
        '''
        Selecting a machine may only affect the signature of tasks that are specific
        to that machine. In other words, when MACHINE=A and MACHINE=B share a recipe
        foo and the output of foo, then both machine configurations must build foo
        in exactly the same way. Otherwise it is not possible to use both machines
        in the same distribution.

        This criteria can only be tested by testing different machines in combination,
        i.e. one main layer, potentially several additional BSP layers and an explicit
        choice of machines:
        yocto-compat-layer --additional-layers .../meta-intel --machines intel-corei7-64 imx6slevk -- .../meta-freescale
        '''

        if not self.td['machines']:
            self.skipTest('No machines set with --machines.')

        # Collect signatures for all machines that we are testing
        # and merge that into a hash:
        # tune -> task -> signature -> list of machines with that combination
        #
        # It is an error if any tune/task pair has more than one signature,
        # because that implies that the machines that caused those different
        # signatures do not agree on how to execute the task.
        tunes = {}
        # Preserve ordering of machines as chosen by the user.
        for machine in self.td['machines']:
            curr_sigs, tune2tasks = get_signatures(self.td['builddir'], failsafe=True, machine=machine)
            # Invert the tune -> [tasks] mapping.
            tasks2tune = {}
            for tune, tasks in tune2tasks.items():
                for task in tasks:
                    tasks2tune[task] = tune
            for task, sighash in curr_sigs.items():
                tunes.setdefault(tasks2tune[task], {}).setdefault(task, {}).setdefault(sighash, []).append(machine)

        msg = []
        for tune in sorted(tunes.keys()):
            tasks = tunes[tune]
            for task in sorted(tasks.keys()):
                signatures = tasks[task]
                # do_build can be ignored: it is know to have
                # different signatures in some cases, for example in
                # the allarch ca-certificates due to RDEPENDS=openssl.
                # That particular dependency is whitelisted via
                # SIGGEN_EXCLUDE_SAFE_RECIPE_DEPS, but still shows up
                # in the sstate signature hash because filtering it
                # out would be hard and running do_build multiple
                # times doesn't really matter.
                if len(signatures.keys()) > 1 and \
                   not task.endswith(':do_build'):
                    # Error!
                    #
                    # Sort signatures by machines, because the hex values don't mean anything.
                    # => all-arch adwaita-icon-theme:do_build: 1234... (beaglebone, qemux86) != abcdf... (qemux86-64)
                    line = '   %s %s: ' % (tune, task)
                    line += ' != '.join(['%s (%s)' % (signature, ', '.join([m for m in signatures[signature]])) for
                                         signature in sorted(signatures.keys(), key=lambda s: signatures[s])])
                    msg.append(line)
        if msg:
            msg.insert(0, 'The machines have conflicting signatures for some shared tasks:')
            self.fail('\n'.join(msg))
