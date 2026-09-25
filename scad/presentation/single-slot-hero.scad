// Deterministic single-slot product hero for issue #32.
// Presentation-only caller: all product geometry comes from the pinned modules.

use <../casing.scad>;
use <../tub.scad>;
use <../knob.scad>;

$fn = 64;

PITCH_Z = 3.5;
MINIMUM_LIP_Z = 3.74;
TUB_EXTERIOR_X = 256.4;
TUB_EXTERIOR_Y = 340.4;
TUB_SOURCE_HEIGHT_U = 23;
TUB_EXTERIOR_Z = TUB_SOURCE_HEIGHT_U * PITCH_Z + MINIMUM_LIP_Z;
SIDE_CLEARANCE = 1.0;
BACK_CLEARANCE = 0.5;
TOP_CLEARANCE = 1.0;
SIDE_THICKNESS = 25;
BACK_THICKNESS = 25;
TOP_THICKNESS = 10;
PEG_SPACING = 190;

SLOT_WIDTH = TUB_EXTERIOR_X + 2 * SIDE_CLEARANCE;
SLOT_DEPTH = TUB_EXTERIOR_Y + BACK_CLEARANCE;
SLOT_HEIGHT = TUB_EXTERIOR_Z + TOP_CLEARANCE;
OUTER_X = SLOT_WIDTH + 2 * SIDE_THICKNESS;
OUTER_Y = SLOT_DEPTH + BACK_THICKNESS;
PRINT_Z = TOP_THICKNESS + SLOT_HEIGHT;
TUB_CENTER_X = SIDE_THICKNESS + SIDE_CLEARANCE + TUB_EXTERIOR_X / 2;
TUB_CLOSED_CENTER_Y = TUB_EXTERIOR_Y / 2;
TUB_SLOT_BOTTOM_Z = -TOP_THICKNESS - TOP_CLEARANCE - TUB_EXTERIOR_Z;
HANDLE_CENTER_Z = 36;

DRAWER_EXTENSION = 150;
PRODUCT_SCALE = 1;
INCLUDE_CASING = true;
INCLUDE_TUB = true;
INCLUDE_KNOB = true;

CASING_COLOR = [0.74, 0.77, 0.80, 1.0];
TUB_COLOR = [0.32, 0.52, 0.63, 1.0];
KNOB_COLOR = [0.18, 0.20, 0.22, 1.0];

assert(PRODUCT_SCALE == 1, "HF_HARD_REJECT:SCALE_CHANGED");
assert(DRAWER_EXTENSION > 0 && DRAWER_EXTENSION < TUB_EXTERIOR_Y,
    "drawer extension must keep the tub partially engaged");

module installed_casing() {
    echo("HF_PART|casing|1");
    color(CASING_COLOR)
        translate([OUTER_X, 0, 0])
            rotate([0, 180, 0])
                hutchfinity_casing(
                    slot_width = SLOT_WIDTH,
                    slot_depth = SLOT_DEPTH,
                    slot_height = SLOT_HEIGHT,
                    side_thickness = SIDE_THICKNESS,
                    back_thickness = BACK_THICKNESS,
                    top_thickness = TOP_THICKNESS,
                    peg_spacing = PEG_SPACING,
                    casing_magnet_drawer_depth = TUB_EXTERIOR_Y
                );
}

module extended_tub() {
    echo("HF_PART|tub|1");
    color(TUB_COLOR)
        translate([
            TUB_CENTER_X,
            TUB_CLOSED_CENTER_Y - DRAWER_EXTENSION,
            TUB_SLOT_BOTTOM_Z
        ])
            hutchfinity_regular_tub();
}

module assembled_knob() {
    echo("HF_PART|knob|1");
    color(KNOB_COLOR)
        translate([
            TUB_CENTER_X,
            -DRAWER_EXTENSION,
            TUB_SLOT_BOTTOM_Z + HANDLE_CENTER_Z
        ])
            rotate([90, 0, 0])
                hutchfinity_knob();
}

echo("HF_SCENE|single-slot-hero");
echo(str("HF_META|product_scale|", PRODUCT_SCALE));

scale([PRODUCT_SCALE, PRODUCT_SCALE, PRODUCT_SCALE]) {
    if (INCLUDE_CASING) installed_casing();
    if (INCLUDE_TUB) extended_tub();
    if (INCLUDE_KNOB) assembled_knob();
}
