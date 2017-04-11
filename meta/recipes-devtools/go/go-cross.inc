inherit cross

DEPENDS += "gcc-cross-${TARGET_ARCH}"

PN = "go-cross-${TARGET_ARCH}"

# Ignore how TARGET_ARCH is computed.
TARGET_ARCH[vardepvalue] = "${TARGET_ARCH}"

# go-cross is built once per target architecture, and thus must not
# depend on the tune-specific libgcc.
DEPENDS_remove = "libgcc"

FILESEXTRAPATHS =. "${FILE_DIRNAME}/go-cross:"

GOROOT_FINAL = "${libdir}/go"
export GOROOT_FINAL

# x32 ABI is not supported on go compiler so far
COMPATIBLE_HOST_linux-gnux32 = "null"
# ppc32 is not supported in go compilers
COMPATIBLE_HOST_powerpc = "null"
