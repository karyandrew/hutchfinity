// casing.scad
// version: 0.2.0
// First-pass Hutchfinity casing shell. Standalone slot geometry: no tub import,
// no front, no bottom. Peg and magnet recipes remain provisional.

$fn = 48;

// Representative first-pass parameters. These describe the casing slot directly;
// hutchfinity-assembly.scad is responsible for choosing values that match a tub.
SLOT_WIDTH = 210;
SLOT_DEPTH = 210;
SLOT_HEIGHT = 84;
SIDE_THICKNESS = 2.4;
BACK_THICKNESS = 2.4;
TOP_THICKNESS = 2.4;
PEG_SPACING = 190.0;
SHOW_DEBUG_MARKERS = false;

DEBUG_MARKER_D = 3.0;

function casing_outer_x(slot_width, side_thickness) = slot_width + 2 * side_thickness;
function casing_outer_y(slot_depth, back_thickness) = slot_depth + back_thickness;
function casing_print_z(slot_height, top_thickness) = top_thickness + slot_height;

// Peg reference points are derived from one spacing target. Corners are always
// indexed; extra points divide the side evenly when the span exceeds spacing.
function peg_axis_intervals(span, peg_spacing) = max(1, ceil(span / peg_spacing));
function peg_axis_positions(span, peg_spacing) =
    let(intervals = peg_axis_intervals(span, peg_spacing))
    [for (i = [0 : intervals]) i * span / intervals];
function peg_axis_middle_positions(span, peg_spacing) =
    let(intervals = peg_axis_intervals(span, peg_spacing))
    intervals <= 1 ? [] : [for (i = [1 : intervals - 1]) i * span / intervals];
function peg_reference_positions(width, depth, peg_spacing) = concat(
    [for (x = peg_axis_positions(width, peg_spacing)) [x, 0]],
    [for (y = peg_axis_middle_positions(depth, peg_spacing)) [width, y]],
    [for (x = peg_axis_positions(width, peg_spacing)) [x, depth]],
    [for (y = peg_axis_middle_positions(depth, peg_spacing)) [0, y]]
);
function peg_count(width, depth, peg_spacing) = len(peg_reference_positions(width, depth, peg_spacing));

module casing_shell(outer_x, outer_y, print_z, side_thickness, back_thickness, top_thickness) {
    union() {
        // Top slab: bed-facing in print, upper riding surface in installed use.
        cube([outer_x, outer_y, top_thickness]);

        // Side and back walls rise from the top slab in print orientation.
        cube([side_thickness, outer_y, print_z]);
        translate([outer_x - side_thickness, 0, 0]) cube([side_thickness, outer_y, print_z]);
        translate([0, outer_y - back_thickness, 0]) cube([outer_x, back_thickness, print_z]);
    }
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
    show_debug_markers=SHOW_DEBUG_MARKERS
) {
    outer_x = casing_outer_x(slot_width, side_thickness);
    outer_y = casing_outer_y(slot_depth, back_thickness);
    print_z = casing_print_z(slot_height, top_thickness);
    peg_positions = peg_reference_positions(outer_x, outer_y, peg_spacing);

    assert(slot_width > 0 && slot_depth > 0 && slot_height > 0,
        "slot dimensions must be positive");
    assert(side_thickness > 0 && back_thickness > 0 && top_thickness > 0,
        "side, back, and top thicknesses must be positive");
    assert(peg_spacing > 0, "peg_spacing must be positive");

    casing_shell(outer_x, outer_y, print_z, side_thickness, back_thickness, top_thickness);

    if (show_debug_markers)
        %peg_debug_markers(peg_positions);
}

hutchfinity_casing();
