# Simplifies setting file capabilities. Those have to go into
# a postinst script because it is not guaranteed that the package
# format preserves the security.capabilities xattr that holds
# the file capabilities.
#
# Using this class also ensures that the necessary tools are
# available.
#
# Example usage (for a hypothetical ping_%.bb[append]):
#   inherit capabilities
#   CAPABILITIES_PACKAGES = "${PN}-bin"
#   CAPABILITIES_${PN}-bin = "${bindir}/ping=net_raw,net_admin ${bindir}/pong=net_broadcast"
#
# Copyright (C) 2015 Intel Corporation
# Licensed under the MIT license

# Dependency when install in cross-compile mode on build host.
# Runtime DEPENDS_<pkg> needs to be created dynamically.
DEPENDS += "libcap-ng-native"

# Space-separated list of packages containing files with capabilities.
CAPABILITIES_PACKAGES ??= "${PN}"

# Space-separated list of files and their capabilities.
# Capability list may be empty.
# CAPABILITIES_${PN} = "/foo/bar=capability1,capability2 /abc/def="

# Ensure that add_capabilities_postinsts gets re-run when the content
# of CAPABILITIES_PACKAGES changes. CAPABILITIES_PACKAGES_<pkg> is added below.
add_capabilities_postinsts[vardeps] = "CAPABILITIES_PACKAGES"
python add_capabilities_postinsts() {
    for pkg in d.getVar('CAPABILITIES_PACKAGES', True).split():
        bb.note("adding capabilities postinst script to %s" % pkg)
        postinst = d.getVar('pkg_postinst_%s' % pkg, True) or d.getVar('pkg_postinst', True) or ''
        files = d.getVar('CAPABILITIES_' + pkg, True)
        if files is None:
            bb.fatal('%s listed in CAPABILITIES_PACKAGES but CAPABILITIES_%s is not set' % (pkg, pkg))
        for entry in files.split():
            filename, capabilities = entry.split('=', 1)
            capabilities = capabilities.split(',')
            if capabilities:
                cmd = 'filecap $D%s %s' % (filename, ' '.join(capabilities))
                # TODO: errors during do_rootfs do not show up in log.do_rootfs.
                # This makes it easy to miss problems.
                postinst += 'echo "{0}"; {0} || exit 1\n'.format(cmd)
            d.setVar('pkg_postinst_%s' % pkg, postinst)
}

PACKAGEFUNCS =+ "add_capabilities_postinsts"

python () {
    capabilities_pkgs = d.getVar('CAPABILITIES_PACKAGES', True).split()
    for pkg in capabilities_pkgs:
        d.appendVar('RDEPENDS_' + pkg, ' libcap-ng-bin')

    d.appendVarFlag('add_capabilities_postinsts', 'vardeps',
                    ' ' + ' '.join(['CAPABILITIES_' + pkg for pkg in capabilities_pkgs]))
}
