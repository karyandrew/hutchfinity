// casing.scad
// version: 0.1.0
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
CASING_WALL_THICKNESS = 2.4;
TOP_THICKNESS = 2.4;
FOOTER_THRESHOLD_XY = 450;
DETENT_POSITION = 0.75;

// Provisional interface toggles stay false until physical recipes land.
SHOW_INTERFACE_MARKERS = true;
ENABLE_PROVISIONAL_PEG_SOCKETS = false;
PEG_SOCKET_D = 6.0;
PEG_SOCKET_DEPTH = 3.0;
PEG_INSET = 10.0;

function tub_outer(cells, pitch_xy, tub_wall) = cells * pitch_xy + 2 * tub_wall;
function slot_height(cells_z, pitch_z) = max(cells_z * pitch_z, 0);
function casing_inner_x(cells_x, pitch_xy, tub_wall, clearance) =
    tub_outer(cells_x, pitch_xy, tub_wall) + 2 * clearance;
function casing_inner_y(cells_y, pitch_xy, tub_wall, clearance) =
    tub_outer(cells_y, pitch_xy, tub_wall) + clearance;
function casing_outer_x(cells_x, pitch_xy, tub_wall, clearance, wall) =
    casing_inner_x(cells_x, pitch_xy, tub_wall, clearance) + 2 * wall;
function casing_outer_y(cells_y, pitch_xy, tub_wall, clearance, wall) =
    casing_inner_y(cells_y, pitch_xy, tub_wall, clearance) + wall;
function peg_positions(outer_x, outer_y, inset) = [
    [inset, inset],
    [outer_x - inset, inset],
    [inset, outer_y - inset],
    [outer_x - inset, outer_y - inset]
];

module casing_shell(outer_x, outer_y, print_z, wall, top_thickness) {
    union() {
        // Top slab: bed-facing in print, upper riding surface in installed use.
        cube([outer_x, outer_y, top_thickness]);

        // Side and back walls rise from the top slab in print orientation.
        cube([wall, outer_y, print_z]);
        translate([outer_x - wall, 0, 0]) cube([wall, outer_y, print_z]);
        translate([0, outer_y - wall, 0]) cube([outer_x, wall, print_z]);
    }
}

module provisional_peg_socket_cuts(positions, depth, diameter, print_z) {
    for (p = positions) {
        translate([p[0], p[1], -EPS]) cylinder(d=diameter, h=depth + EPS);
        translate([p[0], p[1], print_z - depth]) cylinder(d=diameter, h=depth + EPS);
    }
}

module interface_markers(positions, diameter, print_z) {
    color([0.1, 0.35, 0.9, 0.35])
    for (p = positions) {
        translate([p[0], p[1], 0.15]) cylinder(d=diameter, h=0.4);
        translate([p[0], p[1], print_z - 0.55]) cylinder(d=diameter, h=0.4);
    }
}

module hutchfinity_casing(
    cells_x=CELLS_X,
    cells_y=CELLS_Y,
    cells_z=CELLS_Z,
    pitch_xy=PITCH_XY,
    pitch_z=PITCH_Z,
    tub_wall_thickness=TUB_WALL_THICKNESS,
    clearance_slide=CLEARANCE_SLIDE,
    casing_wall_thickness=CASING_WALL_THICKNESS,
    top_thickness=TOP_THICKNESS
) {
    inner_x = casing_inner_x(cells_x, pitch_xy, tub_wall_thickness, clearance_slide);
    inner_y = casing_inner_y(cells_y, pitch_xy, tub_wall_thickness, clearance_slide);
    outer_x = inner_x + 2 * casing_wall_thickness;
    outer_y = inner_y + casing_wall_thickness;
    print_z = top_thickness + slot_height(cells_z, pitch_z);
    positions = peg_positions(outer_x, outer_y, PEG_INSET);

    assert(cells_x > 0 && cells_y > 0, "cells_x and cells_y must be positive");
    assert(cells_z >= 0, "cells_z must be >= 0; use 0 for a flat footer");
    assert(clearance_slide >= 0, "clearance_slide must be non-negative");
    assert(casing_wall_thickness > 0 && top_thickness > 0,
        "wall and top thicknesses must be positive");

    difference() {
        casing_shell(outer_x, outer_y, print_z, casing_wall_thickness, top_thickness);
        if (ENABLE_PROVISIONAL_PEG_SOCKETS)
            provisional_peg_socket_cuts(positions, PEG_SOCKET_DEPTH, PEG_SOCKET_D, print_z);
    }

    if (SHOW_INTERFACE_MARKERS && !ENABLE_PROVISIONAL_PEG_SOCKETS)
        %interface_markers(positions, PEG_SOCKET_D, print_z);
}

hutchfinity_casing();
