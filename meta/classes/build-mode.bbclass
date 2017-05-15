# Enable additional logging and debugging features that are unsuitable
# for production images when building in "debug" mode. "kmod" is
# an example of a recipe which has both "debug" and "logging"
# PACKAGECONFIGs.
#
# This distro feature is not very flexible. More useful in practice
# is the IMAGE_MODE in image.bbclass, which allows building production
# and development images in the same build configuration.
PACKAGECONFIG_append_class-target = "${@ \
    (' ' + ' '.join(set(d.getVarFlags('PACKAGECONFIG').keys()).intersection(('debug', 'logging')))) if \
    bb.utils.contains('DISTRO_FEATURES', 'debug-build', True, False, d) \
    else ''}"

# The following DISTRO_FEATURES have to be considered too dangerous
# and/or unsuitable for use in production.
DISTRO_FEATURES_NON_PRODUCTION ??= "debug-build"
