// casing_mouth_fit_gauge.scad
// version: 0.1.0
// Low-filament mouth gauge for the representative regular-tub casing slot.

use <../casing.scad>;

PITCH_Z = 3.5;
MINIMUM_LIP_Z = 3.74;

REGULAR_TUB_EXTERIOR_Y = 339.2;
REGULAR_TUB_SOURCE_HEIGHT_U = 23;

SIDE_CLEARANCE = 0.0;
TOP_CLEARANCE = 0.0;
GAUGE_SLOT_DEPTH = 40.0;
GAUGE_BACK_THICKNESS = 8.0;

SIDE_THICKNESS = 25;
TOP_THICKNESS = 10;
PEG_SPACING = 190;

function tub_total_height(height_u) = height_u * PITCH_Z + MINIMUM_LIP_Z;
function gauge_slot_width(tub_width, side_clearance) = tub_width + 2 * side_clearance;
function gauge_slot_height(tub_height, top_clearance) = tub_height + top_clearance;

module hutchfinity_casing_mouth_fit_gauge(
    tub_height_u = REGULAR_TUB_SOURCE_HEIGHT_U,
    side_clearance = SIDE_CLEARANCE,
    top_clearance = TOP_CLEARANCE,
    gauge_slot_depth = GAUGE_SLOT_DEPTH,
    gauge_back_thickness = GAUGE_BACK_THICKNESS,
    side_thickness = SIDE_THICKNESS,
    top_thickness = TOP_THICKNESS,
    peg_spacing = PEG_SPACING
) {
    assert(side_clearance >= 0 && top_clearance >= 0,
        "mouth-gauge clearances must be non-negative");
    assert(gauge_slot_depth > 0 && gauge_back_thickness > 0,
        "mouth-gauge depth and back stop must be positive");

    tub_height = tub_total_height(tub_height_u);

    hutchfinity_casing(
        slot_width = gauge_slot_width(REGULAR_TUB_EXTERIOR_Y, side_clearance),
        slot_depth = gauge_slot_depth,
        slot_height = gauge_slot_height(tub_height, top_clearance),
        side_thickness = side_thickness,
        back_thickness = gauge_back_thickness,
        top_thickness = top_thickness,
        peg_spacing = peg_spacing,
        enable_peg_holes = false
    );
}

hutchfinity_casing_mouth_fit_gauge();
