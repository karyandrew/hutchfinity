// casing-fit-test.scad
// version: 0.1.0
// Representative casing/tub fit target. This file maps current tub-source
// dimensions to casing slot dimensions while keeping casing.scad tub-agnostic.

use <casing.scad>;

PITCH_Z = 3.5;
MINIMUM_LIP_Z = 3.74;

REGULAR_TUB_EXTERIOR_X = 255.2;
REGULAR_TUB_EXTERIOR_Y = 339.2;
REGULAR_TUB_SOURCE_HEIGHT_U = 23;
PR19_REPRESENTATIVE_HEIGHT_U = 20;

// Slot clearances are casing geometry, not slicer contour compensation.
// SIDE_CLEARANCE is per side across X. BACK_CLEARANCE is extra depth at the
// closed back; the open front has no front wall. TOP_CLEARANCE is ceiling play.
SIDE_CLEARANCE = 0.0;
BACK_CLEARANCE = 0.0;
TOP_CLEARANCE = 0.0;

// Use 23 for the current source tub. Use 20 only to recreate the PR #19
// representative target while comparing against legacy renders.
FIT_TUB_HEIGHT_U = REGULAR_TUB_SOURCE_HEIGHT_U;

SIDE_THICKNESS = 25;
BACK_THICKNESS = 25;
TOP_THICKNESS = 10;
PEG_SPACING = 190;

function tub_total_height(height_u) = height_u * PITCH_Z + MINIMUM_LIP_Z;
function fit_slot_width(tub_width, side_clearance) = tub_width + 2 * side_clearance;
function fit_slot_depth(tub_depth, back_clearance) = tub_depth + back_clearance;
function fit_slot_height(tub_height, top_clearance) = tub_height + top_clearance;

module hutchfinity_regular_tub_fit_target(
    tub_height_u = FIT_TUB_HEIGHT_U,
    side_clearance = SIDE_CLEARANCE,
    back_clearance = BACK_CLEARANCE,
    top_clearance = TOP_CLEARANCE,
    side_thickness = SIDE_THICKNESS,
    back_thickness = BACK_THICKNESS,
    top_thickness = TOP_THICKNESS,
    peg_spacing = PEG_SPACING
) {
    assert(tub_height_u == REGULAR_TUB_SOURCE_HEIGHT_U || tub_height_u == PR19_REPRESENTATIVE_HEIGHT_U,
        "FIT_TUB_HEIGHT_U should be 23 for current source or 20 for PR19 comparison");
    assert(side_clearance >= 0 && back_clearance >= 0 && top_clearance >= 0,
        "fit clearances must be non-negative");

    tub_height = tub_total_height(tub_height_u);

    hutchfinity_casing(
        slot_width = fit_slot_width(REGULAR_TUB_EXTERIOR_Y, side_clearance),
        slot_depth = fit_slot_depth(REGULAR_TUB_EXTERIOR_X, back_clearance),
        slot_height = fit_slot_height(tub_height, top_clearance),
        side_thickness = side_thickness,
        back_thickness = back_thickness,
        top_thickness = top_thickness,
        peg_spacing = peg_spacing
    );
}

hutchfinity_regular_tub_fit_target();
