// hutchfinity-assembly.scad
// version: 0.2.0
// Assembly caller for fit previews. Casing stays tub-agnostic; tub geometry
// belongs here once an authored tub module exists.

use <casing.scad>;
use <peg.scad>;
use <knob.scad>;

REGULAR_TUB_EXTERIOR_X = 255.2;
REGULAR_TUB_EXTERIOR_Y = 339.2;
REGULAR_TUB_BODY_HEIGHT_U = 20;
PITCH_Z = 3.5;
MINIMUM_LIP_Z = 3.74;
REGULAR_TUB_20U_EXTERIOR_Z = REGULAR_TUB_BODY_HEIGHT_U * PITCH_Z + MINIMUM_LIP_Z;
SHOW_OPTIONAL_PARTS = true;

hutchfinity_casing(
    slot_width=REGULAR_TUB_EXTERIOR_Y,
    slot_depth=REGULAR_TUB_EXTERIOR_X,
    slot_height=REGULAR_TUB_20U_EXTERIOR_Z,
    side_thickness=25,
    back_thickness=25,
    top_thickness=10,
    peg_spacing=190
);

if (SHOW_OPTIONAL_PARTS) {
    translate([REGULAR_TUB_EXTERIOR_Y + 110, 0, 0]) hutchfinity_peg();
    translate([REGULAR_TUB_EXTERIOR_Y + 110, 65, 0]) hutchfinity_knob();
}
