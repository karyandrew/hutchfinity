// magnet_well_shape_inspection.scad
// version: 0.2.0
// Printable face coupon for the canonical 6 x 1.5mm product magnet recipe.

use <../magnet_well.scad>;

$fn = 96;

COUPON_SIZE = 22;
COUPON_THICKNESS = 4;

module visible_well_coupon(recipe = hutchfinity_magnet_recipe_6x1_5()) {
    assert(COUPON_THICKNESS > hutchfinity_magnet_recipe_well_depth(recipe),
        "coupon must retain material below the magnet well");

    rotate([180, 0, 0])
    difference() {
        translate([-COUPON_SIZE / 2, -COUPON_SIZE / 2, 0])
            cube([COUPON_SIZE, COUPON_SIZE, COUPON_THICKNESS]);
        hutchfinity_magnet_well_cut([0, 0], recipe);
    }
}

visible_well_coupon();
