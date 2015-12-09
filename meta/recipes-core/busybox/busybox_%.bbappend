inherit capabilities

# This .bbappend  lowers privileges of certain commands from "runs as
# root via suid" to "runs with a limited set of privileges via file
# capabilities".
#
# The original list of symlinks to busybox.suid is, with (*) marking
# commands which now can get executed with less privileges:
#    /bin/ping (*)
#    /bin/ping6 (*)
#    /bin/login
#    /usr/bin/passwd
#    /bin/su
#    /usr/bin/traceroute (*)
#    /usr/bin/vock
#
# As it stands now, this change still leaves the "ping" and "traceroute"
# code in the busybox.suid binary, where it can be executed as root by
# a normal user by symlinking to it ("ln -s /bin/busybox.suid /tmp/ping;
# /tmp/ping ...").
#
# To fix this, one would have to split up busybox even further, which
# (somewhat) negates the space saving coming from implementing several
# commands in the same binary.

CAPABILITIES_${PN} = " \
    ${base_bindir}/busybox.net_raw=net_raw \
"

do_install_append () {
    ln ${D}/${base_bindir}/busybox.suid ${D}/${base_bindir}/busybox.net_raw
    grep \
       -e ping \
       -e traceroute \
       ${D}/${sysconfdir}/busybox.links.suid >${D}/${sysconfdir}/busybox.links.net_raw
    grep -v \
       -e ping \
       -e traceroute \
       ${D}/${sysconfdir}/busybox.links.suid >${D}/${sysconfdir}/busybox.links.suid.tmp
    mv ${D}/${sysconfdir}/busybox.links.suid.tmp ${D}/${sysconfdir}/busybox.links.suid
}
