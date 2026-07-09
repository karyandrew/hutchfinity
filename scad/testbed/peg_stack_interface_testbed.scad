// peg_stack_interface_testbed.scad
// version: 0.5.1
// Coupon for the two-ended Hutchfinity vertical stack hex-peg interface.
// This tests the integrated stack-land condition from casing.scad.

use <../casing.scad>;
use <../peg.scad>;

$fn = 64;

SOCKET_NOMINAL_DIAMETER = 8.0;
PEG_DIAMETER = 8.45;
PEG_CLEARANCE = 0.45;
PEG_LENGTH = 20.0;
PEG_SOCKET_DEPTH = 10.0;
PEG_CHAMFER = 2.5;

STACK_LAND_WIDTH = 40.0;
STACK_LAND_LENGTH = 50.0;
COUPON_X = STACK_LAND_WIDTH;
COUPON_Y = STACK_LAND_LENGTH;
TOP_COUPON_Z = PEG_SOCKET_DEPTH;
FOOT_COUPON_Z = 20.0;
COUPON_GAP = 10.0;
PEG_GAP_Y = 18.0;
function foot_origin_x() = COUPON_X + COUPON_GAP;
function socket_diameter() = peg_socket_diameter(SOCKET_NOMINAL_DIAMETER, PEG_CLEARANCE);
function socket_x() = STACK_LAND_WIDTH / 2;
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
    translate([COUPON_X / 2 - PEG_LENGTH / 2, -PEG_GAP_Y, 0])
    hutchfinity_peg_print_layout(
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
