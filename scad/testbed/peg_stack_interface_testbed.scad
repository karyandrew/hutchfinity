// peg_stack_interface_testbed.scad
// version: 0.2.0
// Coupon for the two-ended Hutchfinity vertical stack peg interface.
// This tests the side-wall edge condition: socket chamfers sit close to
// the same outer edge they use in casing.scad, not centered in a block.

use <../casing.scad>;
use <../peg.scad>;

$fn = 64;

PEG_DIAMETER = 8.0;
PEG_CLEARANCE = 0.45;
PEG_LENGTH = 20.0;
PEG_SOCKET_DEPTH = 10.0;
PEG_CHAMFER = 2.5;

SIDE_THICKNESS = 25.0;
COUPON_X = SIDE_THICKNESS;
COUPON_Y = 34.0;
TOP_COUPON_Z = PEG_SOCKET_DEPTH;
FOOT_COUPON_Z = 20.0;
COUPON_GAP = 10.0;
PEG_GAP_Y = 18.0;
function foot_origin_x() = COUPON_X + COUPON_GAP;
function socket_diameter() = peg_socket_diameter(PEG_DIAMETER, PEG_CLEARANCE);
function socket_x() = peg_socket_inset(PEG_DIAMETER, PEG_CLEARANCE, PEG_CHAMFER);
function socket_center() = [socket_x(), COUPON_Y / 2];

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
