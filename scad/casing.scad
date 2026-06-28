// casing.scad
// version: 0.1.2
// First-pass Hutchfinity casing shell. Emits print orientation: top on bed,
// no front, no bottom. Magnet and peg recipes are reserved but provisional.

$fn = 48;
EPS = 0.01;

// Representative first-pass parameters.
CELLS_X = 6;
CELLS_Y = 8;
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
SHOW_INTERFACE_MARKERS = true;
ENABLE_PROVISIONAL_TOP_PEG_SOCKETS = false;
PEG_SOCKET_D = 6.0;
PEG_SOCKET_DEPTH = 1.2;
PEG_INSET = 10.0;
PEG_MAX_SPACING = 180.0;

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
function span_count(span, max_spacing) = max(2, ceil(span / max_spacing) + 1);
function interpolate(a, b, i, count) = count <= 1 ? a : a + (b - a) * i / (count - 1);
function edge_points_y(x, y0, y1, max_spacing) =
    let(count = span_count(abs(y1 - y0), max_spacing))
    [for (i = [0:count - 1]) [x, interpolate(y0, y1, i, count)]];
function interior_edge_points_x(y, x0, x1, max_spacing) =
    let(count = span_count(abs(x1 - x0), max_spacing))
    [for (i = [0:count - 1])
        if (i > 0 && i < count - 1) [interpolate(x0, x1, i, count), y]];
function peg_positions(outer_x, outer_y, inset, max_spacing) =
    let(
        left_x = inset,
        right_x = outer_x - inset,
        front_y = inset,
        back_y = outer_y - inset
    )
    concat(
        edge_points_y(left_x, front_y, back_y, max_spacing),
        edge_points_y(right_x, front_y, back_y, max_spacing),
        interior_edge_points_x(back_y, left_x, right_x, max_spacing)
    );

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
    bottom_thickness=BOTTOM_THICKNESS
) {
    inner_x = casing_inner_x(cells_x, pitch_xy, tub_wall_thickness, clearance_slide);
    inner_y = casing_inner_y(cells_y, pitch_xy, tub_wall_thickness, clearance_slide);
    outer_x = inner_x + 2 * side_wall_thickness;
    outer_y = inner_y + back_wall_thickness;
    print_z = top_thickness + slot_height(cells_z, pitch_z);
    positions = peg_positions(outer_x, outer_y, PEG_INSET, PEG_MAX_SPACING);

    assert(cells_x > 0 && cells_y > 0, "cells_x and cells_y must be positive");
    assert(cells_z >= 0, "cells_z must be >= 0; use 0 for a flat footer");
    assert(clearance_slide >= 0, "clearance_slide must be non-negative");
    assert(side_wall_thickness > 0 && back_wall_thickness > 0 && top_thickness > 0,
        "side wall, back wall, and top thicknesses must be positive");
    assert(bottom_thickness == 0,
        "bottom_thickness must stay 0; the casing intentionally has no floor/bottom");
    assert(PEG_MAX_SPACING > PEG_SOCKET_D,
        "peg max spacing must be larger than the peg/socket diameter");
    assert(outer_x > 2 * PEG_INSET && outer_y > 2 * PEG_INSET,
        "peg inset must fit inside the casing footprint");

    difference() {
        casing_shell(outer_x, outer_y, print_z, side_wall_thickness, back_wall_thickness, top_thickness);
        if (ENABLE_PROVISIONAL_TOP_PEG_SOCKETS)
            provisional_top_peg_socket_cuts(positions, min(PEG_SOCKET_DEPTH, top_thickness - EPS), PEG_SOCKET_D);
    }

    if (SHOW_INTERFACE_MARKERS && !ENABLE_PROVISIONAL_TOP_PEG_SOCKETS)
        %top_interface_markers(positions, PEG_SOCKET_D);
}

hutchfinity_casing();
