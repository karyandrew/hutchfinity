// casing-fit-test.scad
// version: 0.5.0
// Current full-depth casing fit target. Uses the generator's tub height,
// clearances, slab, and peg interface. Set cells_x, cells_y, bin_h, and the
// same design variables as hutchfinity.scad with OpenSCAD -D overrides.
// The retired 23u trial geometry remains available in git history.

use <hutchfinity.scad>;

sized_casing();
