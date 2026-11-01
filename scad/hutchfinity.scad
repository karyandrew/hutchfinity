// hutchfinity.scad
// version: 1.0.0
// One file for every sized Hutchfinity part. Open it in OpenSCAD and use the
// Customizer panel, or run ../hutchfinity.py for the small local app.
// Casing, pegs, and pull are derived from the same tub size so they stay matched.

use <tub.scad>;
use <casing.scad>;
use <peg.scad>;
use <knob.scad>;

/* [Part] */
part = "tub"; // [tub, grid-insert, casing, pegs, pull]

/* [Tub size] */
cells_x = 12; // [1:1:30]
cells_y = 16; // [1:1:30]
// Tallest bin the tub must hold, in 3.5 mm units.
bin_h = 20; // [1:1:40]
floor_mode = "integral-grid"; // [integral-grid, plain]
pull_guide = true;

/* [Casing] */
side_wall = 18; // [12:1:30]
back_wall = 18; // [12:1:30]
riding_slab = 1.3; // [1.3:0.1:10]
side_clearance = 1.0;
back_clearance = 0.5;
top_clearance = 1.0;
peg_spacing = 190;

/* [Hidden] */
$fn = 64;
PEG_BORE = 8.45;
PEG_DEPTH = 10;
PEG_CHAMFER = 0.5;
PEG_EDGE_LAND = 1.2;
PEG_LENGTH = 19.6;
PEG_END_CHAMFER = 2.5;

tub_x = tub_outer_x(cells_x);
tub_y = tub_outer_y(cells_y);
tub_z = tub_total_z(bin_h, floor_mode);
slot_x = tub_x + 2 * side_clearance;
slot_y = tub_y + back_clearance;
slot_z = tub_z + top_clearance;
casing_x = slot_x + 2 * side_wall;
casing_y = slot_y + back_wall;
casing_z = slot_z + riding_slab;
peg_positions = peg_reference_positions(
    casing_x, casing_y, side_wall, back_wall, peg_spacing,
    peg_socket_end_inset(side_wall, back_wall, 8, 0.45, PEG_CHAMFER, PEG_EDGE_LAND));

// Printed slab-down, then inverted for installation.
module sized_casing() {
    assert(2 * PEG_DEPTH < casing_z, "casing is too short for opposed peg sockets");
    assert((min(side_wall, back_wall) - PEG_BORE - 2 * PEG_CHAMFER) / 2 >= 4, "walls too thin for peg sockets");
    echo(str("casing: ", casing_x, " x ", casing_y, " x ", casing_z, " mm; ", len(peg_positions), " pegs"));
    difference() {
        casing_shell(casing_x, casing_y, casing_z, side_wall, back_wall, riding_slab);
        chamfered_peg_socket_cuts(peg_positions, PEG_BORE, PEG_DEPTH, PEG_CHAMFER);
        chamfered_peg_foot_socket_cuts(peg_positions, PEG_BORE, PEG_DEPTH, PEG_CHAMFER, casing_z);
    }
}

module sized_pegs() {
    echo(str("pegs: ", len(peg_positions)));
    for (i = [0:len(peg_positions) - 1])
        translate([(i % 4) * 26, PEG_BORE / 2 + floor(i / 4) * 14, 0])
            hutchfinity_peg_print_layout(diameter = PEG_BORE, length = PEG_LENGTH, end_chamfer = PEG_END_CHAMFER);
}

// The standard pull is 90 x 34 mm; a smaller tub gets it scaled to its guide.
module sized_pull() {
    flange = pull_flange(cells_x, bin_h, floor_mode);
    assert(flange[0] > 0, "this tub is too small for a pull");
    echo(str("pull flange: ", flange[0], " x ", flange[1], " mm"));
    scale([flange[0] / 90, flange[1] / 34, 1]) hutchfinity_knob();
}

if (part == "tub") hutchfinity_tub(cells_x, cells_y, bin_h, floor_mode, pull_guide);
else if (part == "grid-insert") hutchfinity_grid_insert(cells_x, cells_y);
else if (part == "casing") sized_casing();
else if (part == "pegs") sized_pegs();
else if (part == "pull") sized_pull();
else assert(false, "unknown part");
