# Copyright (C) 2017 Intel Corporation
# Released under the MIT license (see COPYING.MIT)

import unittest

from compatlayer import LayerType, get_signatures, check_command
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
        pruned = 0
        last_line_key = None
        # task order as determined by completion scheduler ("merged task list"),
        # edited a bit to add tasks not active in the build config that was used
        taskname_list = ( 'do_fetch',
                          'do_unpack',
                          'do_kernel_checkout',
                          'do_validate_branches',
                          'do_kernel_metadata',
                          'do_patch',
                          'do_preconfigure',
                          'do_kernel_configme',
                          'do_generate_toolchain_file',
                          'do_pam_sanity',
                          'do_prepare_recipe_sysroot',
                          'do_configure',
                          'do_kernel_configcheck',
                          'do_kernel_version_sanity_check',
                          'do_configure_ptest_base',
                          'do_compile',
                          'do_shared_workdir',
                          'do_kernel_link_images',
                          'do_compile_kernelmodules',
                          'do_strip',
                          'do_sizecheck',
                          'do_uboot_mkimage',
                          'do_gcc_stash_builddir',
                          'do_compile_ptest_base',
                          'do_install',
                          'do_multilib_install',
                          'do_extra_symlinks',
                          'do_stash_locale',
                          'do_poststash_install_cleanup',
                          'do_install_ptest_base',
                          'do_package',
                          'do_packagedata',
                          'do_populate_sysroot',
                          'do_bundle_initramfs',
                          'do_populate_lic',
                          'do_generate_rmc_db',
                          'do_deploy',
                          'do_package_write_ipk',
                          'do_package_write_rpm',
                          'do_package_write_deb',
                          'do_rootfs',
                          'do_write_qemuboot_conf',
                          'do_image',
                          'do_image_cpio',
                          'do_write_wks_template',
                          'do_rootfs_wicenv',
                          'do_image_wic',
                          'do_image_complete',
                          'do_image_qa',
                          'do_deploy_files',
                          'do_package_qa',
                          'do_rm_work',
                          'do_rm_work_all',
                          'do_build_sysroot',
                          'do_build')
        taskname_order = dict([(task, index) for index, task in enumerate(taskname_list) ])
        def task_key(task):
            pn, taskname = task.rsplit(':', 1)
            return (pn, taskname_order.get(taskname, 0), taskname)

        for tune in sorted(tunes.keys()):
            tasks = tunes[tune]
            # As for test_signatures it would be nicer to sort tasks
            # by dependencies here, but that is harder because we have
            # to report on tasks from different machines, which might
            # have different dependencies. We resort to pruning the
            # output by reporting only one task per recipe if the set
            # of machines matches.
            #
            # "bitbake-diffsigs -t -s" is intelligent enough to print
            # diffs recursively, so often it does not matter that much
            # if we don't pick the underlying difference
            # here. However, sometimes recursion fails
            # (https://bugzilla.yoctoproject.org/show_bug.cgi?id=6428).
            #
            # To mitigate that a bit, we use a hard-coded ordering of
            # tasks that represents how they normally run and prefer
            # to print the ones that run first.
            for task in sorted(tasks.keys(), key=task_key):
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
                    #
                    # Skip the line if it is covered already by the predecessor (same pn, same sets of machines).
                    pn, taskname = task.rsplit(':', 1)
                    next_line_key = (pn, sorted(signatures.values()))
                    if next_line_key != last_line_key:
                        line = '   %s %s: ' % (tune, task)
                        line += ' != '.join(['%s (%s)' % (signature, ', '.join([m for m in signatures[signature]])) for
                                             signature in sorted(signatures.keys(), key=lambda s: signatures[s])])
                        last_line_key = next_line_key
                        msg.append(line)
                        # Randomly pick two mismatched signatures and remember how to invoke
                        # bitbake-diffsigs for them.
                        iterator = iter(signatures.items())
                        a = next(iterator)
                        b = next(iterator)
                        diffsig_machines = '(%s) != (%s)' % (', '.join(a[1]), ', '.join(b[1]))
                        diffsig_params = '-t %s %s -s %s %s' % (pn, taskname, a[0], b[0])
                    else:
                        pruned += 1

        if msg:
            msg.insert(0, 'The machines have conflicting signatures for some shared tasks:')
            if pruned > 0:
                msg.append('')
                msg.append('%d tasks where not listed because some other task of the recipe already differed.' % pruned)
                msg.append('It is likely that differences from different recipes also have the same root cause.')
            msg.append('')
            # Explain how to investigate...
            msg.append('To investigate, run bitbake-diffsigs -t recipename taskname -s fromsig tosig.')
            cmd = 'bitbake-diffsigs %s' % diffsig_params
            msg.append('Example: %s in the last line' % diffsig_machines)
            msg.append('Command: %s' % cmd)
            # ... and actually do it automatically for that example, but without aborting
            # when that fails.
            try:
                output = check_command('Comparing signatures failed.', cmd).decode('utf-8')
            except RuntimeError as ex:
                output = str(ex)
            msg.extend(['   ' + line for line in output.splitlines()])
            self.fail('\n'.join(msg))
