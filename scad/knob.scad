// knob.scad
// version: 0.1.0
// Optional glue-on tub pull. Broad, thin base flares into a raised grip.

$fn = 48;
EPS = 0.01;

BASE_WIDTH = 90;
BASE_DEPTH = 34;
BASE_THICKNESS = 2.0;
BASE_CORNER_RADIUS = 5;
FLARE_HEIGHT = 5;
GRIP_WIDTH = 44;
GRIP_DEPTH = 24;
GRIP_HEIGHT = 12;
GRIP_CORNER_RADIUS = 8;

function clamped_radius(width, depth, radius) = min(radius, min(width, depth) / 2 - EPS);

module rounded_box(width, depth, height, radius) {
    r = clamped_radius(width, depth, radius);
    hull() {
        for (x = [-width / 2 + r, width / 2 - r])
            for (y = [-depth / 2 + r, depth / 2 - r])
                translate([x, y, 0]) cylinder(r=r, h=height);
    }
}

module hutchfinity_knob(
    base_width=BASE_WIDTH,
    base_depth=BASE_DEPTH,
    base_thickness=BASE_THICKNESS,
    base_corner_radius=BASE_CORNER_RADIUS,
    flare_height=FLARE_HEIGHT,
    grip_width=GRIP_WIDTH,
    grip_depth=GRIP_DEPTH,
    grip_height=GRIP_HEIGHT,
    grip_corner_radius=GRIP_CORNER_RADIUS
) {
    assert(base_width > grip_width && base_depth > grip_depth,
        "knob base must be broader than the grip");
    assert(base_thickness > 0 && flare_height >= 0 && grip_height > 0,
        "knob thickness and grip height must be positive");

    union() {
        rounded_box(base_width, base_depth, base_thickness, base_corner_radius);

        translate([0, 0, base_thickness - EPS])
        hull() {
            rounded_box(base_width * 0.72, base_depth * 0.72, EPS, base_corner_radius);
            translate([0, 0, flare_height])
                rounded_box(grip_width, grip_depth, EPS, grip_corner_radius);
        }

        translate([0, 0, base_thickness + flare_height - EPS])
            rounded_box(grip_width, grip_depth, grip_height, grip_corner_radius);
    }
}

hutchfinity_knob();
