// Hutchfinity optional glue-on knob prototype.
// Version: 0.2.0

$fn = 64;
EPS = 0.01;

BASE_WIDTH = 90.0;
BASE_DEPTH = 34.0;
BASE_THICKNESS = 2.0;
BASE_CORNER_RADIUS = 5.0;

FLARE_WIDTH = 62.0;
FLARE_DEPTH = 28.0;
FLARE_HEIGHT = 3.0;

NECK_WIDTH = 36.0;
NECK_DEPTH = 18.0;
END_BULGE_WIDTH = 56.0;
END_BULGE_DEPTH = 30.0;
GRIP_HEIGHT = 14.0;
GRIP_CORNER_RADIUS = 6.0;

module rounded_box(size, radius) {
    width = size[0];
    depth = size[1];
    height = size[2];
    linear_extrude(height = height)
        offset(r = radius)
            square([max(width - 2 * radius, EPS), max(depth - 2 * radius, EPS)], center = true);
}

module tapered_slug(bottom_size, top_size, height, radius) {
    hull() {
        translate([0, 0, 0])
            rounded_box([bottom_size[0], bottom_size[1], EPS], min(radius, bottom_size[0] / 2 - EPS, bottom_size[1] / 2 - EPS));
        translate([0, 0, height - EPS])
            rounded_box([top_size[0], top_size[1], EPS], min(radius, top_size[0] / 2 - EPS, top_size[1] / 2 - EPS));
    }
}

module hutchfinity_knob(
    base_width = BASE_WIDTH,
    base_depth = BASE_DEPTH,
    base_thickness = BASE_THICKNESS,
    base_corner_radius = BASE_CORNER_RADIUS,
    flare_width = FLARE_WIDTH,
    flare_depth = FLARE_DEPTH,
    flare_height = FLARE_HEIGHT,
    neck_width = NECK_WIDTH,
    neck_depth = NECK_DEPTH,
    end_bulge_width = END_BULGE_WIDTH,
    end_bulge_depth = END_BULGE_DEPTH,
    grip_height = GRIP_HEIGHT,
    grip_corner_radius = GRIP_CORNER_RADIUS
) {
    assert(base_width > end_bulge_width, "base_width must exceed end_bulge_width for a glue flange");
    assert(base_depth > end_bulge_depth, "base_depth must exceed end_bulge_depth for a glue flange");
    assert(end_bulge_width > neck_width, "end_bulge_width should exceed neck_width");
    assert(end_bulge_depth > neck_depth, "end_bulge_depth should exceed neck_depth");

    union() {
        rounded_box([base_width, base_depth, base_thickness], base_corner_radius);

        translate([0, 0, base_thickness - EPS])
            tapered_slug(
                [flare_width, flare_depth],
                [neck_width, neck_depth],
                flare_height + EPS,
                min(grip_corner_radius, flare_depth / 2 - EPS)
            );

        translate([0, 0, base_thickness + flare_height - EPS])
            tapered_slug(
                [neck_width, neck_depth],
                [end_bulge_width, end_bulge_depth],
                grip_height + EPS,
                grip_corner_radius
            );
    }
}

hutchfinity_knob();
