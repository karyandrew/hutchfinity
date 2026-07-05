// casing.scad
// version: 0.7.0
// First-pass Hutchfinity casing shell. Standalone slot geometry: no tub import,
// no front, no bottom. Installed-top and installed-bottom peg sockets are
// prototype casing-to-casing stack geometry; magnet wells remain deferred.

$fn = 64;
EPS = 0.01;

// Representative first-pass parameters. These describe the casing slot directly;
// hutchfinity-assembly.scad is responsible for choosing values that match a tub.
// Current default is a regular source tub oriented width-wise: the drawer opens along
// the tub's short axis, so the casing opening spans the tub's long dimension.
// The default height tracks the current 23h tub source total: 23 * 3.5 + 3.74.
SLOT_WIDTH = 339.2;
SLOT_DEPTH = 255.2;
SLOT_HEIGHT = 84.24;
SIDE_THICKNESS = 25;
BACK_THICKNESS = 25;
TOP_THICKNESS = 10;
PEG_SPACING = 190.0;
PEG_DIAMETER = 8.0;
PEG_CLEARANCE = 0.45;
PEG_SOCKET_DEPTH = TOP_THICKNESS;
PEG_CHAMFER = 2.5;
PEG_SOCKET_EDGE_LAND = 4.0;
STACK_LAND_WIDTH = 40.0;
STACK_LAND_LENGTH = 50.0;
ENABLE_PEG_HOLES = true;
SHOW_DEBUG_MARKERS = false;

DEBUG_MARKER_D = 3.0;

function casing_outer_x(slot_width, side_thickness) = slot_width + 2 * side_thickness;
function casing_outer_y(slot_depth, back_thickness) = slot_depth + back_thickness;
function casing_print_z(slot_height, top_thickness) = top_thickness + slot_height;
function peg_socket_diameter(peg_diameter, peg_clearance) = peg_diameter + peg_clearance;
function peg_socket_opening_radius(peg_diameter, peg_clearance, peg_chamfer) =
    peg_socket_diameter(peg_diameter, peg_clearance) / 2 + peg_chamfer;
function peg_socket_inset(peg_diameter, peg_clearance, peg_chamfer, edge_land=PEG_SOCKET_EDGE_LAND) =
    peg_socket_opening_radius(peg_diameter, peg_clearance, peg_chamfer) + edge_land;
function peg_socket_end_inset(side_thickness, back_thickness, peg_diameter, peg_clearance, peg_chamfer, edge_land, stack_land_length) =
    max(
        max(max(side_thickness, back_thickness), stack_land_length / 2),
        peg_socket_inset(peg_diameter, peg_clearance, peg_chamfer, edge_land)
    );

// Peg reference points are derived from one spacing target. Centers sit on the
// centers of integrated external stack lands, not on bare side/back wall edges.
function peg_axis_intervals_between(start, end, peg_spacing) =
    max(1, ceil((end - start) / peg_spacing));
function peg_axis_positions_between(start, end, peg_spacing) =
    let(intervals = peg_axis_intervals_between(start, end, peg_spacing), usable = end - start)
    [for (i = [0 : intervals]) start + i * usable / intervals];
function peg_axis_middle_positions_between(start, end, peg_spacing) =
    let(intervals = peg_axis_intervals_between(start, end, peg_spacing), usable = end - start)
    intervals <= 1 ? [] : [for (i = [1 : intervals - 1]) start + i * usable / intervals];
function peg_side_socket_x_left(side_thickness, stack_land_width) =
    side_thickness - stack_land_width / 2;
function peg_side_socket_x_right(width, side_thickness, stack_land_width) =
    width - side_thickness + stack_land_width / 2;
function peg_back_socket_y(depth, back_thickness, stack_land_width) =
    depth - back_thickness + stack_land_width / 2;
function peg_side_y_positions(depth, peg_spacing, end_inset) =
    peg_axis_positions_between(end_inset, depth - end_inset, peg_spacing);
function peg_back_x_positions(width, peg_spacing, end_inset) =
    peg_axis_middle_positions_between(end_inset, width - end_inset, peg_spacing);
function peg_reference_positions(width, depth, side_thickness, back_thickness, peg_spacing, end_inset, stack_land_width) = concat(
    [for (y = peg_side_y_positions(depth, peg_spacing, end_inset))
        [peg_side_socket_x_left(side_thickness, stack_land_width), y]],
    [for (y = peg_side_y_positions(depth, peg_spacing, end_inset))
        [peg_side_socket_x_right(width, side_thickness, stack_land_width), y]],
    [for (x = peg_back_x_positions(width, peg_spacing, end_inset))
        [x, peg_back_socket_y(depth, back_thickness, stack_land_width)]]
);
function peg_count(width, depth, side_thickness, back_thickness, peg_spacing, end_inset, stack_land_width) =
    len(peg_reference_positions(width, depth, side_thickness, back_thickness, peg_spacing, end_inset, stack_land_width));

module casing_shell(
    outer_x,
    outer_y,
    print_z,
    side_thickness,
    back_thickness,
    top_thickness,
    stack_land_width,
    stack_land_length,
    side_ys,
    back_xs
) {
    union() {
        // Top slab: bed-facing in print, upper riding surface in installed use.
        cube([outer_x, outer_y, top_thickness]);

        // Side and back walls rise from the top slab in print orientation.
        cube([side_thickness, outer_y, print_z]);
        translate([outer_x - side_thickness, 0, 0]) cube([side_thickness, outer_y, print_z]);
        translate([0, outer_y - back_thickness, 0]) cube([outer_x, back_thickness, print_z]);

        // External stack lands give casing-to-casing peg sockets real material
        // without adding a bottom plate or intruding into the drawer slot.
        for (y = side_ys) {
            translate([
                side_thickness - stack_land_width,
                y - stack_land_length / 2,
                0
            ])
            cube([stack_land_width, stack_land_length, print_z]);

            translate([
                outer_x - side_thickness,
                y - stack_land_length / 2,
                0
            ])
            cube([stack_land_width, stack_land_length, print_z]);
        }

        for (x = back_xs)
            translate([
                x - stack_land_length / 2,
                outer_y - back_thickness,
                0
            ])
            cube([stack_land_length, stack_land_width, print_z]);
    }
}

module chamfered_peg_socket_cut(position, socket_diameter, socket_depth, socket_chamfer, z=0) {
    chamfer = min(socket_chamfer, socket_depth / 2);
    translate([position[0], position[1], z - EPS])
    union() {
        cylinder(d=socket_diameter, h=socket_depth + 2 * EPS);
        cylinder(d1=socket_diameter + 2 * chamfer, d2=socket_diameter, h=chamfer + EPS);
        translate([0, 0, socket_depth - chamfer])
            cylinder(d1=socket_diameter, d2=socket_diameter + 2 * chamfer, h=chamfer + 2 * EPS);
    }
}

module chamfered_peg_socket_cuts(positions, socket_diameter, socket_depth, socket_chamfer) {
    for (p = positions)
        chamfered_peg_socket_cut(p, socket_diameter, socket_depth, socket_chamfer);
}

module chamfered_peg_foot_socket_cuts(positions, socket_diameter, socket_depth, socket_chamfer, print_z) {
    for (p = positions)
        chamfered_peg_socket_cut(
            p,
            socket_diameter,
            socket_depth,
            socket_chamfer,
            print_z - socket_depth
        );
}

module peg_debug_markers(positions) {
    color([0.1, 0.35, 0.9, 0.35])
    for (p = positions)
        translate([p[0], p[1], 0.15]) cylinder(d=DEBUG_MARKER_D, h=0.4);
}

module hutchfinity_casing(
    slot_width=SLOT_WIDTH,
    slot_depth=SLOT_DEPTH,
    slot_height=SLOT_HEIGHT,
    side_thickness=SIDE_THICKNESS,
    back_thickness=BACK_THICKNESS,
    top_thickness=TOP_THICKNESS,
    peg_spacing=PEG_SPACING,
    peg_diameter=PEG_DIAMETER,
    peg_clearance=PEG_CLEARANCE,
    peg_socket_depth=PEG_SOCKET_DEPTH,
    peg_chamfer=PEG_CHAMFER,
    peg_socket_edge_land=PEG_SOCKET_EDGE_LAND,
    stack_land_width=STACK_LAND_WIDTH,
    stack_land_length=STACK_LAND_LENGTH,
    enable_peg_holes=ENABLE_PEG_HOLES,
    show_debug_markers=SHOW_DEBUG_MARKERS
) {
    outer_x = casing_outer_x(slot_width, side_thickness);
    outer_y = casing_outer_y(slot_depth, back_thickness);
    print_z = casing_print_z(slot_height, top_thickness);
    socket_diameter = peg_socket_diameter(peg_diameter, peg_clearance);
    socket_depth = min(peg_socket_depth, top_thickness);
    socket_opening_radius = peg_socket_opening_radius(peg_diameter, peg_clearance, peg_chamfer);
    socket_end_inset = peg_socket_end_inset(
        side_thickness,
        back_thickness,
        peg_diameter,
        peg_clearance,
        peg_chamfer,
        peg_socket_edge_land,
        stack_land_length
    );
    side_ys = peg_side_y_positions(outer_y, peg_spacing, socket_end_inset);
    back_xs = peg_back_x_positions(outer_x, peg_spacing, socket_end_inset);
    stack_side_ys = enable_peg_holes ? side_ys : [];
    stack_back_xs = enable_peg_holes ? back_xs : [];
    peg_positions = peg_reference_positions(
        outer_x,
        outer_y,
        side_thickness,
        back_thickness,
        peg_spacing,
        socket_end_inset,
        stack_land_width
    );

    assert(slot_width > 0 && slot_depth > 0 && slot_height > 0,
        "slot dimensions must be positive");
    assert(side_thickness > 0 && back_thickness > 0 && top_thickness > 0,
        "side, back, and top thicknesses must be positive");
    assert(peg_spacing > 0, "peg_spacing must be positive");
    assert(peg_diameter > 0 && peg_clearance >= 0,
        "peg diameter must be positive and peg clearance must be non-negative");
    assert(peg_socket_depth > 0 && peg_chamfer >= 0,
        "peg socket depth must be positive and peg chamfer must be non-negative");
    assert(peg_socket_edge_land > 0,
        "peg socket edge land must leave material beyond the chamfer opening");
    assert(stack_land_width >= max(side_thickness, back_thickness),
        "stack land width must be at least the side/back wall thickness");
    assert(stack_land_length > 0, "stack land length must be positive");
    assert(!enable_peg_holes ||
           (outer_x > 2 * socket_end_inset && outer_y > 2 * socket_end_inset),
        "peg sockets must fit inside the casing footprint");
    assert(!enable_peg_holes ||
           (stack_land_width / 2 >= socket_opening_radius + peg_socket_edge_land &&
            stack_land_length / 2 >= socket_opening_radius + peg_socket_edge_land),
        "peg socket chamfer must fit inside the stack land with edge land");

    difference() {
        casing_shell(
            outer_x,
            outer_y,
            print_z,
            side_thickness,
            back_thickness,
            top_thickness,
            stack_land_width,
            stack_land_length,
            stack_side_ys,
            stack_back_xs
        );
        if (enable_peg_holes) {
            // In print orientation this opens on the bed-facing top slab.
            // In installed orientation it is the top socket face.
            chamfered_peg_socket_cuts(peg_positions, socket_diameter, socket_depth, peg_chamfer);
            // In print orientation this opens on the upper wall-foot face.
            // In installed orientation it is the bottom socket face.
            chamfered_peg_foot_socket_cuts(
                peg_positions,
                socket_diameter,
                socket_depth,
                peg_chamfer,
                print_z
            );
        }
    }

    if (show_debug_markers && !enable_peg_holes)
        %peg_debug_markers(peg_positions);
}

hutchfinity_casing();
