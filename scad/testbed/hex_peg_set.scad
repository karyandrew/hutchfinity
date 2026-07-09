// hex_peg_set.scad
// version: 0.1.0
// Printable set of loose hex pegs for one representative casing stack interface.

use <../peg.scad>;

PEG_COUNT = 7;
PEG_COLUMNS = 4;
PEG_X_PITCH = 30;
PEG_Y_PITCH = 22;

module hex_peg_set(
    peg_count = PEG_COUNT,
    peg_columns = PEG_COLUMNS,
    peg_x_pitch = PEG_X_PITCH,
    peg_y_pitch = PEG_Y_PITCH
) {
    assert(peg_count > 0, "peg_count must be positive");
    assert(peg_columns > 0, "peg_columns must be positive");
    assert(peg_x_pitch > 0 && peg_y_pitch > 0,
        "peg set pitch values must be positive");

    for (i = [0 : peg_count - 1])
        translate([
            (i % peg_columns) * peg_x_pitch,
            floor(i / peg_columns) * peg_y_pitch,
            0
        ])
        hutchfinity_peg_print_layout();
}

hex_peg_set();
