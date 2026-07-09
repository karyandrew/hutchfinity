// hutchfinity-assembly.scad
// version: 0.6.2
// Assembly caller for fit previews. Casing stays tub-agnostic; tub geometry
// belongs here once an authored tub module exists.

use <casing.scad>;
use <tub.scad>;
use <peg.scad>;
use <knob.scad>;

REGULAR_TUB_EXTERIOR_X = 256.4;
REGULAR_TUB_EXTERIOR_Y = 340.4;
REGULAR_TUB_SOURCE_HEIGHT_U = 23;
REGULAR_TUB_MAX_BIN_HEIGHT_U = 20;
PITCH_Z = 3.5;
MINIMUM_LIP_Z = 3.74;
REGULAR_TUB_EXTERIOR_Z = REGULAR_TUB_SOURCE_HEIGHT_U * PITCH_Z + MINIMUM_LIP_Z;
SIDE_CLEARANCE = 1.0;
BACK_CLEARANCE = 0.5;
TOP_CLEARANCE = 1.0;
SHOW_OPTIONAL_PARTS = true;

hutchfinity_casing(
    slot_width=REGULAR_TUB_EXTERIOR_X + 2 * SIDE_CLEARANCE,
    slot_depth=REGULAR_TUB_EXTERIOR_Y + BACK_CLEARANCE,
    slot_height=REGULAR_TUB_EXTERIOR_Z + TOP_CLEARANCE,
    side_thickness=25,
    back_thickness=25,
    top_thickness=10,
    peg_spacing=190,
    casing_magnet_drawer_depth=REGULAR_TUB_EXTERIOR_Y
);

if (SHOW_OPTIONAL_PARTS) {
    translate([0, REGULAR_TUB_EXTERIOR_Y + 70, 0])
        hutchfinity_regular_tub();
    translate([REGULAR_TUB_EXTERIOR_X + 110, 0, 0]) hutchfinity_peg();
    translate([REGULAR_TUB_EXTERIOR_X + 110, 65, 0]) hutchfinity_knob();
}
