// peg_socket_fit_testbed.scad
// version: 0.3.0
// Cheap physical coupon for provisional Hutchfinity laid-down ribbed-peg/socket fit.

use <../casing.scad>;
use <../peg.scad>;

$fn = 64;

PEG_DIAMETER = 8.0;
PEG_LENGTH = 20.0;
PEG_SOCKET_DEPTH = 10.0;
PEG_CHAMFER = 2.5;
CLEARANCE_CANDIDATES = [0.30, 0.45, 0.60];

COUPON_X = 34;
COUPON_Y = 26;
COUPON_Z = PEG_SOCKET_DEPTH;
COUPON_GAP = 10;
PEG_GAP_Y = 16;
INDEX_MARK_W = 2.0;
INDEX_MARK_GAP = 1.2;
INDEX_MARK_H = 0.6;

function coupon_origin_x(index) = index * (COUPON_X + COUPON_GAP);
function socket_center() = [COUPON_X / 2, COUPON_Y / 2];

module index_marks(index) {
    for (i = [0 : index])
        translate([
            4 + i * (INDEX_MARK_W + INDEX_MARK_GAP),
            2,
            COUPON_Z
        ])
        cube([INDEX_MARK_W, 5, INDEX_MARK_H]);
}

module socket_coupon(clearance, index) {
    translate([coupon_origin_x(index), 0, 0])
    union() {
        difference() {
            cube([COUPON_X, COUPON_Y, COUPON_Z]);
            chamfered_peg_socket_cut(
                socket_center(),
                peg_socket_diameter(PEG_DIAMETER, clearance),
                PEG_SOCKET_DEPTH,
                PEG_CHAMFER
            );
        }
        index_marks(index);
    }
}

module test_peg(index) {
    translate([
        coupon_origin_x(index) + COUPON_X / 2 - PEG_LENGTH / 2,
        -PEG_GAP_Y,
        0
    ])
    hutchfinity_peg_print_layout(
        diameter=PEG_DIAMETER,
        length=PEG_LENGTH,
        end_chamfer=PEG_CHAMFER
    );
}

module peg_socket_fit_testbed(clearances=CLEARANCE_CANDIDATES) {
    assert(len(clearances) > 0, "clearance candidate list must not be empty");

    for (i = [0 : len(clearances) - 1]) {
        assert(clearances[i] >= 0, "peg clearance candidates must be non-negative");
        socket_coupon(clearances[i], i);
        test_peg(i);
    }
}

peg_socket_fit_testbed();
