// through_peg_socket_testbed.scad
// version: 0.1.1
// Unvalidated physical coupon for the continuous peg bore and insertion stop.
// Print whole to test fit; SECTION=true exposes the hourglass profile for review.

use <../casing.scad>;
use <../peg.scad>;

// Match the production casing's bore approximation for physical fit tests.
$fn = 32;
SECTION = false;
HEIGHT = 30;
BORE = 8.45;
THROAT_REDUCTION = 1.0;
DEPTH = min(10, (HEIGHT - 2) / 2);
PEG_LENGTH = 2 * DEPTH - 0.4;
END_CHAMFER = min(2.5, PEG_LENGTH / 4);

module stop_coupon(section=SECTION) {
    difference() {
        cube([18, 18, HEIGHT]);
        through_peg_socket_cut([9, 9], BORE, HEIGHT, DEPTH, 0.5,
            END_CHAMFER, THROAT_REDUCTION);
        if (section) translate([-1, -1, -1]) cube([20, 10, HEIGHT + 2]);
    }
}

stop_coupon();
translate([26, 5, 0]) hutchfinity_peg_print_layout(
    diameter=BORE, length=PEG_LENGTH, end_chamfer=END_CHAMFER);
