// mini_regular_mega_print_set.scad
// version: 0.1.0
// Selector-based source for the casing-fit-trial-01 mini/regular/mega print set.

use <../casing.scad>;
use <../knob.scad>;
use <../tub.scad>;
use <hex_peg_set.scad>;

$fn = 64;

PRINT_PART = "casing-regular";

MINI_TUB_EXTERIOR_X = 130.4;
REGULAR_TUB_EXTERIOR_X = 256.4;
MEGA_TUB_EXTERIOR_X = 382.4;
STANDARD_TUB_EXTERIOR_Y = 340.4;
TUB_SOURCE_HEIGHT_U = 23;
PITCH_Z = 3.5;
MINIMUM_LIP_Z = 3.74;
TUB_EXTERIOR_Z = TUB_SOURCE_HEIGHT_U * PITCH_Z + MINIMUM_LIP_Z;

SIDE_CLEARANCE = 1.0;
BACK_CLEARANCE = 0.5;
TOP_CLEARANCE = 1.0;

SIDE_THICKNESS = 25;
BACK_THICKNESS = 25;
TOP_THICKNESS = 10;
PEG_SPACING = 190;

function valid_print_part(part) =
    part == "casing-mini" ||
    part == "casing-regular" ||
    part == "casing-mega" ||
    part == "tub-mini" ||
    part == "tub-regular" ||
    part == "tub-mega" ||
    part == "knob" ||
    part == "hex-peg-set";

module hutchfinity_sized_casing(tub_width, tub_depth = STANDARD_TUB_EXTERIOR_Y) {
    hutchfinity_casing(
        slot_width = tub_width + 2 * SIDE_CLEARANCE,
        slot_depth = tub_depth + BACK_CLEARANCE,
        slot_height = TUB_EXTERIOR_Z + TOP_CLEARANCE,
        side_thickness = SIDE_THICKNESS,
        back_thickness = BACK_THICKNESS,
        top_thickness = TOP_THICKNESS,
        peg_spacing = PEG_SPACING,
        casing_magnet_drawer_depth = tub_depth
    );
}

assert(valid_print_part(PRINT_PART), str("Unknown PRINT_PART: ", PRINT_PART));

if (PRINT_PART == "casing-mini") {
    hutchfinity_sized_casing(MINI_TUB_EXTERIOR_X);
} else if (PRINT_PART == "casing-regular") {
    hutchfinity_sized_casing(REGULAR_TUB_EXTERIOR_X);
} else if (PRINT_PART == "casing-mega") {
    hutchfinity_sized_casing(MEGA_TUB_EXTERIOR_X);
} else if (PRINT_PART == "tub-mini") {
    hutchfinity_mini_tub();
} else if (PRINT_PART == "tub-regular") {
    hutchfinity_regular_tub();
} else if (PRINT_PART == "tub-mega") {
    hutchfinity_mega_tub();
} else if (PRINT_PART == "knob") {
    hutchfinity_knob();
} else if (PRINT_PART == "hex-peg-set") {
    hex_peg_set();
}
