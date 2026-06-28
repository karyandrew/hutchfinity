// hutchfinity-assembly.scad
// version: 0.1.0
// Assembly caller for fit previews. Casing stays tub-agnostic; tub geometry
// belongs here once an authored tub module exists.

use <casing.scad>;

hutchfinity_casing(
    slot_width=210,
    slot_depth=210,
    slot_height=84,
    side_thickness=2.4,
    back_thickness=2.4,
    top_thickness=2.4,
    peg_spacing=190
);
