PV = "0.0+cvs${SRCDATE}"
LICENSE = "MIT"
DESCRIPTION = "utility for modifying keymaps and pointer button mappings in X"
SECTION = "x11/base"
PR = "r1"

DEPENDS = "virtual/libx11"

SRC_URI = "${FREEDESKTOP_CVS}/xorg;module=xc/programs/xmodmap \
           file://autofoo.patch;patch=1"
S = "${WORKDIR}/xmodmap"

inherit autotools pkgconfig 
