// magnet_well_shape_inspection.scad
// version: 0.1.0
// Real-CAD face coupons for inspecting the current tub and casing magnet wells.

use <../magnet_well.scad>;

$fn = 96;

COUPON_SIZE = 22;
COUPON_THICKNESS = 4;
COUPON_GAP = 10;

TUB_MAGNET_BORE_DIAMETER = 5.40;
TUB_MAGNET_RIB_TIP_DIAMETER = 5.25;
TUB_MAGNET_WELL_DEPTH = 1.10;

CASING_MAGNET_BORE_DIAMETER = 6.40;
CASING_MAGNET_RIB_TIP_DIAMETER = 6.10;
CASING_MAGNET_WELL_DEPTH = 1.60;

MAGNET_CHAMFER = 0.30;

module visible_well_coupon(x, bore_diameter, rib_tip_diameter, well_depth) {
    translate([x, 0, 0])
    rotate([180, 0, 0])
    difference() {
        translate([-COUPON_SIZE / 2, -COUPON_SIZE / 2, 0])
            cube([COUPON_SIZE, COUPON_SIZE, COUPON_THICKNESS]);
        hutchfinity_magnet_well_cut(
            [0, 0],
            bore_diameter,
            rib_tip_diameter,
            well_depth,
            MAGNET_CHAMFER
        );
    }
}

visible_well_coupon(
    -COUPON_SIZE / 2 - COUPON_GAP / 2,
    TUB_MAGNET_BORE_DIAMETER,
    TUB_MAGNET_RIB_TIP_DIAMETER,
    TUB_MAGNET_WELL_DEPTH
);

visible_well_coupon(
    COUPON_SIZE / 2 + COUPON_GAP / 2,
    CASING_MAGNET_BORE_DIAMETER,
    CASING_MAGNET_RIB_TIP_DIAMETER,
    CASING_MAGNET_WELL_DEPTH
);
