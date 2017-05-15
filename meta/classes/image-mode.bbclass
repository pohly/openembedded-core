# Images can be built for "production", "debugging" or "development".
# Additional modes might get defined by a distro or developer. This is
# intentionally a separate variable. That way, IMAGE_FEATURES can be
# set dynamically depending on IMAGE_MODE.
#
# They can be set independently from the "debug-build" DISTRO_FEATURE.
# However, images that are explicitly marked as "production" get
# disabled when "debug-build" is active.
#
# The intended usage is:
# - production - enable and allow only features suitable for production
# - development - enable also features useful while developing the distro and/or image content,
#                 like easier root access
# - debugging - same as development plus additional debug output
#
# The default is not to have a fixed mode. Which features an image
# recipe enables in that case depends on whether the image and/or project is more
# geared towards development or production. For example, the OE-core
# local.conf.sample enables "debug-tweaks" by default unless "production"
# is set.
IMAGE_MODE ??= ""
IMAGE_MODE_VALID ??= "production development debugging"

python () {
    # Sanity checks for IMAGE_MODE.
    image_mode = d.getVar('IMAGE_MODE', d)
    mode = set(image_mode.split())
    if len(mode) == 0:
        return
    if len(mode) > 1:
        bb.fatal('An image can only be built in exactly one mode: IMAGE_MODE=%s' % image_mode)
    mode = mode.pop()
    valid = d.getVar('IMAGE_MODE_VALID')
    if mode not in valid.split():
        bb.fatal('Invalid image mode: IMAGE_MODE=%s (not in %s)' % (image_mode, valid))

    # Disable development images when we can't be sure that they'll only contain
    # production content. This errs on the side of caution.
    if mode == 'production' and 'debug-build' in d.getVar('DISTRO_FEATURES').split():
        raise bb.parse.SkipRecipe("Production images are disabled when the 'debug-build' DISTRO_FEATURE is active.")
}

# Optional additional text appended to an image's /etc/motd
# when some mode other than "production" is chosen explicitly.
#
# Set to empty to disable this.
IMAGE_DEV_MOTD_DEFAULT () {
*********************************************
*** This is a ${IMAGE_MODE} image! ${@ ' ' * (19 - len(d.getVar('IMAGE_MODE')))} ***
*** Do not use in production.             ***
*********************************************
}
IMAGE_DEV_MOTD ??= "${IMAGE_DEV_MOTD_DEFAULT}"

python dev_motd () {
    motd = d.getVar('IMAGE_DEV_MOTD')
    if motd:
        with open(d.expand('${IMAGE_ROOTFS}${sysconfdir}/motd'), 'a') as f:
            f.write(motd)
}

ROOTFS_POSTPROCESS_COMMAND += "${@'' if (d.getVar('IMAGE_MODE') or 'production') == 'production' else ' dev_motd;'}"
