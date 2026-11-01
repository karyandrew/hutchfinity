// hutchfinity.scad
// version: 1.2.0
// One file for every sized Hutchfinity part. Open it in OpenSCAD and use the
// Customizer panel, or run ../hutchfinity.py for the app and Orca-ready output.
// Casing, pegs, and pull are derived from the same tub size so they stay matched.
// tub.scad is included, not used, so that -D can override its dimensions too.

include <tub.scad>;
use <casing.scad>;
use <peg.scad>;
use <knob.scad>;

/* [Part] */
part = "tub"; // [tub, grid-insert, casing, peg, pegs, pull]

/* [Tub size] */
cells_x = 12; // [1:1:30]
cells_y = 16; // [1:1:30]
// Tallest bin the tub must hold, in 3.5 mm units.
bin_h = 20; // [5:1:40]
floor_mode = "integral-grid"; // [integral-grid, plain]
pull_guide = true;

/* [Casing] */
side_wall = 18; // [18:1:40]
back_wall = 18; // [18:1:40]
riding_slab = 1.3; // [1.3:0.1:10]
side_clearance = 1.0;
back_clearance = 0.5;
top_clearance = 1.0;
peg_spacing = 190;
casing_fn = 32;

/* [Pegs] */
peg_bore = 8.45;
peg_depth_max = 10;
peg_chamfer = 0.5;
peg_edge_land = 1.2;
peg_end_chamfer = 2.5;

tub_x = tub_outer_x(cells_x);
tub_y = tub_outer_y(cells_y);
tub_z = tub_total_z(bin_h, floor_mode);
slot_x = tub_x + 2 * side_clearance;
slot_y = tub_y + back_clearance;
slot_z = tub_z + top_clearance;
casing_x = slot_x + 2 * side_wall;
casing_y = slot_y + back_wall;
casing_z = slot_z + riding_slab;
// Short casings get shallower sockets and shorter pegs.
peg_depth = min(peg_depth_max, (casing_z - 2) / 2);
peg_length = 2 * peg_depth - 0.4;
peg_positions = peg_reference_positions(
    casing_x, casing_y, side_wall, back_wall, peg_spacing,
    peg_socket_end_inset(side_wall, back_wall, 8, 0.45, peg_chamfer, peg_edge_land));

// Printed slab-down, then inverted for installation.
module sized_casing() {
    assert((min(side_wall, back_wall) - peg_bore - 2 * peg_chamfer) / 2 >= 4, "walls too thin for peg sockets");
    echo(str("casing: ", casing_x, " x ", casing_y, " x ", casing_z, " mm; ", len(peg_positions), " pegs"));
    difference() {
        casing_shell(casing_x, casing_y, casing_z, side_wall, back_wall, riding_slab);
        chamfered_peg_socket_cuts(peg_positions, peg_bore, peg_depth, peg_chamfer, $fn = casing_fn);
        chamfered_peg_foot_socket_cuts(peg_positions, peg_bore, peg_depth, peg_chamfer, casing_z, $fn = casing_fn);
    }
}

module one_peg() {
    hutchfinity_peg_print_layout(
        diameter = peg_bore, length = peg_length,
        end_chamfer = min(peg_end_chamfer, peg_length / 4));
}

module sized_pegs() {
    for (i = [0:len(peg_positions) - 1])
        translate([(i % 4) * (peg_length + 6), peg_bore / 2 + floor(i / 4) * 14, 0]) one_peg();
}

// The same pull everywhere, scaled uniformly when the tub is too small for it.
module sized_pull() {
    k = pull_scale_factor(cells_x, bin_h, floor_mode);
    assert(k > 0, "this tub has no wall band for a pull");
    echo(str("pull flange: ", k * PULL_FLANGE_X, " x ", k * PULL_FLANGE_Z, " mm"));
    scale(k) hutchfinity_knob(base_width = PULL_FLANGE_X, base_depth = PULL_FLANGE_Z, end_bulge_depth = 30);
}

if (part == "tub") hutchfinity_tub(cells_x, cells_y, bin_h, floor_mode, pull_guide);
else if (part == "grid-insert") hutchfinity_grid_insert(cells_x, cells_y);
else if (part == "casing") sized_casing();
else if (part == "peg") one_peg();
else if (part == "pegs") sized_pegs();
else if (part == "pull") sized_pull();
else assert(false, "unknown part");
assert(bin_h >= 5, "a tub must hold at least a 5h bin");
