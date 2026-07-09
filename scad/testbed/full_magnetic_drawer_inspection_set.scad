// full_magnetic_drawer_inspection_set.scad
// version: 0.3.2
// Aligned inspection exports for the regular magnetic drawer set. These are
// not print-orientation STLs; they share one installed-use coordinate system.

use <../casing.scad>;
use <../knob.scad>;
use <../peg.scad>;
use <../tub.scad>;

PITCH_Z = 3.5;
MINIMUM_LIP_Z = 3.74;

REGULAR_TUB_EXTERIOR_X = 256.4;
REGULAR_TUB_EXTERIOR_Y = 340.4;
REGULAR_TUB_SOURCE_HEIGHT_U = 23;
TUB_EXTERIOR_X = REGULAR_TUB_EXTERIOR_X;
TUB_EXTERIOR_Y = REGULAR_TUB_EXTERIOR_Y;
TUB_SOURCE_HEIGHT_U = REGULAR_TUB_SOURCE_HEIGHT_U;
TUB_EXTERIOR_Z = TUB_SOURCE_HEIGHT_U * PITCH_Z + MINIMUM_LIP_Z;
CUSTOM_TUB_STL = "";

SIDE_CLEARANCE = 1.0;
BACK_CLEARANCE = 0.5;
TOP_CLEARANCE = 1.0;

SIDE_THICKNESS = 25;
BACK_THICKNESS = 25;
TOP_THICKNESS = 10;
PEG_SPACING = 190;
PEG_DIAMETER = 8.0;
PEG_CLEARANCE = 0.45;
PEG_CHAMFER = 2.5;
PEG_SOCKET_EDGE_LAND = 4.0;
PEG_INSERT_Z = -10;
HANDLE_CENTER_Z = 36;

SLOT_WIDTH = TUB_EXTERIOR_X + 2 * SIDE_CLEARANCE;
SLOT_DEPTH = TUB_EXTERIOR_Y + BACK_CLEARANCE;
SLOT_HEIGHT = TUB_EXTERIOR_Z + TOP_CLEARANCE;
OUTER_X = SLOT_WIDTH + 2 * SIDE_THICKNESS;
OUTER_Y = SLOT_DEPTH + BACK_THICKNESS;
TUB_CENTER_X = SIDE_THICKNESS + SIDE_CLEARANCE + TUB_EXTERIOR_X / 2;
TUB_CENTER_Y = TUB_EXTERIOR_Y / 2;
TUB_SLOT_BOTTOM_Z = -TOP_THICKNESS - TOP_CLEARANCE - TUB_EXTERIOR_Z;

// 0: magnet-interface assembly, 1: casing installed, 2: tub on casing top,
// 3: slot-fit assembly, 4: tub in slot, 5: handle, 6: pegs installed.
INSPECTION_PART = 0;

function inspection_peg_end_inset() =
    peg_socket_end_inset(
        SIDE_THICKNESS,
        BACK_THICKNESS,
        PEG_DIAMETER,
        PEG_CLEARANCE,
        PEG_CHAMFER,
        PEG_SOCKET_EDGE_LAND
    );

function inspection_peg_positions() =
    peg_reference_positions(
        OUTER_X,
        OUTER_Y,
        SIDE_THICKNESS,
        BACK_THICKNESS,
        PEG_SPACING,
        inspection_peg_end_inset()
    );

module inspection_casing_installed() {
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

module selected_tub() {
    if (CUSTOM_TUB_STL == "")
        hutchfinity_regular_tub();
    else
        hutchfinity_tub_from_stl(
            CUSTOM_TUB_STL,
            tub_x = TUB_EXTERIOR_X,
            tub_y = TUB_EXTERIOR_Y
        );
}

module aligned_tub(bottom_z) {
    translate([TUB_CENTER_X, TUB_CENTER_Y, bottom_z])
        selected_tub();
}

module aligned_handle(bottom_z) {
    translate([TUB_CENTER_X, 0, bottom_z + HANDLE_CENTER_Z])
        rotate([90, 0, 0])
            hutchfinity_knob();
}

module installed_pegs() {
    for (p = inspection_peg_positions())
        translate([p[0], p[1], PEG_INSERT_Z])
            hutchfinity_peg();
}

module tub_on_casing_top_closed() {
    aligned_tub(0);
    aligned_handle(0);
}

module tub_in_slot_closed() {
    aligned_tub(TUB_SLOT_BOTTOM_Z);
    aligned_handle(TUB_SLOT_BOTTOM_Z);
}

if (INSPECTION_PART == 0) {
    inspection_casing_installed();
    tub_on_casing_top_closed();
    installed_pegs();
} else if (INSPECTION_PART == 1) {
    inspection_casing_installed();
} else if (INSPECTION_PART == 2) {
    tub_on_casing_top_closed();
} else if (INSPECTION_PART == 3) {
    inspection_casing_installed();
    tub_in_slot_closed();
    installed_pegs();
} else if (INSPECTION_PART == 4) {
    tub_in_slot_closed();
} else if (INSPECTION_PART == 5) {
    aligned_handle(0);
} else if (INSPECTION_PART == 6) {
    installed_pegs();
}
