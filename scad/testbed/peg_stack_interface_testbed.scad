// peg_stack_interface_testbed.scad
// version: 0.1.0
// Coupon for the two-ended Hutchfinity vertical stack peg interface.

use <../casing.scad>;
use <../peg.scad>;

$fn = 64;

PEG_DIAMETER = 8.0;
PEG_CLEARANCE = 0.45;
PEG_LENGTH = 20.0;
PEG_SOCKET_DEPTH = 10.0;
PEG_CHAMFER = 2.5;

COUPON_X = 34;
COUPON_Y = 34;
TOP_COUPON_Z = PEG_SOCKET_DEPTH;
FOOT_COUPON_Z = 20;
COUPON_GAP = 10;
PEG_GAP_Y = 18;
function foot_origin_x() = COUPON_X + COUPON_GAP;
function socket_center() = [COUPON_X / 2, COUPON_Y / 2];
function socket_diameter() = peg_socket_diameter(PEG_DIAMETER, PEG_CLEARANCE);

module top_slab_socket_coupon() {
    union() {
        difference() {
            cube([COUPON_X, COUPON_Y, TOP_COUPON_Z]);
            chamfered_peg_socket_cut(
                socket_center(),
                socket_diameter(),
                PEG_SOCKET_DEPTH,
                PEG_CHAMFER
            );
        }
    }
}

module wall_foot_receiver_coupon() {
    translate([foot_origin_x(), 0, 0])
    union() {
        difference() {
            cube([COUPON_X, COUPON_Y, FOOT_COUPON_Z]);
            chamfered_peg_socket_cut(
                socket_center(),
                socket_diameter(),
                PEG_SOCKET_DEPTH,
                PEG_CHAMFER,
                FOOT_COUPON_Z - PEG_SOCKET_DEPTH
            );
        }
    }
}

module loose_peg() {
    translate([COUPON_X / 2, -PEG_GAP_Y, 0])
    hutchfinity_peg(
        diameter=PEG_DIAMETER,
        length=PEG_LENGTH,
        end_chamfer=PEG_CHAMFER
    );
}

module peg_stack_interface_testbed() {
    assert(PEG_LENGTH == 2 * PEG_SOCKET_DEPTH,
        "peg length should match lower top-slab socket plus upper foot receiver depth");

    top_slab_socket_coupon();
    wall_foot_receiver_coupon();
    loose_peg();
}

peg_stack_interface_testbed();
