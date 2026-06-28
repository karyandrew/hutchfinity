// casing.scad
// version: 0.1.4
// First-pass Hutchfinity casing shell. Emits print orientation: top on bed,
// no front, no bottom. Magnet and peg recipes are reserved but provisional.

$fn = 48;
EPS = 0.01;

// Representative first-pass parameters.
CELLS_X = 10;
CELLS_Y = 10;
CELLS_Z = 24;
PITCH_XY = 21;
PITCH_Z = 3.5;
TUB_WALL_THICKNESS = 1.6;
CLEARANCE_SLIDE = 0.6;
SIDE_WALL_THICKNESS = 2.4;
BACK_WALL_THICKNESS = 2.4;
TOP_THICKNESS = 2.4;
BOTTOM_THICKNESS = 0;
FOOTER_THRESHOLD_XY = 450;
DETENT_POSITION = 0.75;

// Provisional interface toggles stay false until physical recipes land.
SHOW_INTERFACE_MARKERS = false;
ENABLE_PROVISIONAL_TOP_PEG_SOCKETS = false;
PEG_SOCKET_D = 6.0;
PEG_SOCKET_DEPTH = 1.2;
PEG_PREVIEW_COUNT_X = 2;
PEG_PREVIEW_COUNT_Y = 2;
PEG_PREVIEW_SPACING_X = 190.0;
PEG_PREVIEW_SPACING_Y = 190.0;
PEG_PREVIEW_EDGE_MARGIN = 10.0;

function tub_outer(cells, pitch_xy, tub_wall) = cells * pitch_xy + 2 * tub_wall;
function slot_height(cells_z, pitch_z) = max(cells_z * pitch_z, 0);
function casing_inner_x(cells_x, pitch_xy, tub_wall, clearance) =
    tub_outer(cells_x, pitch_xy, tub_wall) + 2 * clearance;
function casing_inner_y(cells_y, pitch_xy, tub_wall, clearance) =
    tub_outer(cells_y, pitch_xy, tub_wall) + clearance;
function casing_outer_x(cells_x, pitch_xy, tub_wall, clearance, side_wall) =
    casing_inner_x(cells_x, pitch_xy, tub_wall, clearance) + 2 * side_wall;
function casing_outer_y(cells_y, pitch_xy, tub_wall, clearance, back_wall) =
    casing_inner_y(cells_y, pitch_xy, tub_wall, clearance) + back_wall;
// Preview-only positions for optional top-slab markers/cuts. These are
// parameterized knobs, not an algorithmic placement rule.
function preview_axis_position(size, count, spacing, index) =
    size / 2 - ((count - 1) * spacing) / 2 + index * spacing;
function preview_peg_positions(outer_x, outer_y, count_x, count_y, spacing_x, spacing_y) = [
    for (ix = [0 : count_x - 1])
        for (iy = [0 : count_y - 1])
            [
                preview_axis_position(outer_x, count_x, spacing_x, ix),
                preview_axis_position(outer_y, count_y, spacing_y, iy)
            ]
];

module casing_shell(outer_x, outer_y, print_z, side_wall, back_wall, top_thickness) {
    union() {
        // Top slab: bed-facing in print, upper riding surface in installed use.
        cube([outer_x, outer_y, top_thickness]);

        // Side and back walls rise from the top slab in print orientation.
        cube([side_wall, outer_y, print_z]);
        translate([outer_x - side_wall, 0, 0]) cube([side_wall, outer_y, print_z]);
        translate([0, outer_y - back_wall, 0]) cube([outer_x, back_wall, print_z]);
    }
}

module provisional_top_peg_socket_cuts(positions, depth, diameter) {
    for (p = positions)
        translate([p[0], p[1], -EPS]) cylinder(d=diameter, h=depth + EPS);
}

module top_interface_markers(positions, diameter) {
    color([0.1, 0.35, 0.9, 0.35])
    for (p = positions)
        translate([p[0], p[1], 0.15]) cylinder(d=diameter, h=0.4);
}

module hutchfinity_casing(
    cells_x=CELLS_X,
    cells_y=CELLS_Y,
    cells_z=CELLS_Z,
    pitch_xy=PITCH_XY,
    pitch_z=PITCH_Z,
    tub_wall_thickness=TUB_WALL_THICKNESS,
    clearance_slide=CLEARANCE_SLIDE,
    side_wall_thickness=SIDE_WALL_THICKNESS,
    back_wall_thickness=BACK_WALL_THICKNESS,
    top_thickness=TOP_THICKNESS,
    bottom_thickness=BOTTOM_THICKNESS,
    peg_preview_count_x=PEG_PREVIEW_COUNT_X,
    peg_preview_count_y=PEG_PREVIEW_COUNT_Y,
    peg_preview_spacing_x=PEG_PREVIEW_SPACING_X,
    peg_preview_spacing_y=PEG_PREVIEW_SPACING_Y,
    peg_preview_edge_margin=PEG_PREVIEW_EDGE_MARGIN
) {
    inner_x = casing_inner_x(cells_x, pitch_xy, tub_wall_thickness, clearance_slide);
    inner_y = casing_inner_y(cells_y, pitch_xy, tub_wall_thickness, clearance_slide);
    outer_x = inner_x + 2 * side_wall_thickness;
    outer_y = inner_y + back_wall_thickness;
    print_z = top_thickness + slot_height(cells_z, pitch_z);
    peg_preview_extent_x = (peg_preview_count_x - 1) * peg_preview_spacing_x;
    peg_preview_extent_y = (peg_preview_count_y - 1) * peg_preview_spacing_y;
    positions = preview_peg_positions(
        outer_x, outer_y,
        peg_preview_count_x, peg_preview_count_y,
        peg_preview_spacing_x, peg_preview_spacing_y
    );

    assert(cells_x > 0 && cells_y > 0, "cells_x and cells_y must be positive");
    assert(cells_z >= 0, "cells_z must be >= 0; use 0 for a flat footer");
    assert(clearance_slide >= 0, "clearance_slide must be non-negative");
    assert(side_wall_thickness > 0 && back_wall_thickness > 0 && top_thickness > 0,
        "side wall, back wall, and top thicknesses must be positive");
    assert(bottom_thickness == 0,
        "bottom_thickness must stay 0; the casing intentionally has no floor/bottom");
    assert(peg_preview_count_x >= 1 && peg_preview_count_y >= 1,
        "peg preview counts must be positive");
    assert(peg_preview_count_x == floor(peg_preview_count_x) && peg_preview_count_y == floor(peg_preview_count_y),
        "peg preview counts must be integers");
    assert((peg_preview_count_x == 1 || peg_preview_spacing_x > 0) &&
        (peg_preview_count_y == 1 || peg_preview_spacing_y > 0),
        "peg preview spacing must be positive when count is greater than 1");
    assert(peg_preview_edge_margin >= 0,
        "peg preview edge margin must be non-negative");
    assert(peg_preview_extent_x <= outer_x - 2 * peg_preview_edge_margin &&
        peg_preview_extent_y <= outer_y - 2 * peg_preview_edge_margin,
        "peg preview count and spacing must fit inside the casing footprint");

    difference() {
        casing_shell(outer_x, outer_y, print_z, side_wall_thickness, back_wall_thickness, top_thickness);
        if (ENABLE_PROVISIONAL_TOP_PEG_SOCKETS)
            provisional_top_peg_socket_cuts(positions, min(PEG_SOCKET_DEPTH, top_thickness - EPS), PEG_SOCKET_D);
    }

    if (SHOW_INTERFACE_MARKERS && !ENABLE_PROVISIONAL_TOP_PEG_SOCKETS)
        %top_interface_markers(positions, PEG_SOCKET_D);
}

hutchfinity_casing();
