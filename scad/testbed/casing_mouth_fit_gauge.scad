// casing_mouth_fit_gauge.scad
// version: 0.2.0
// Current low-filament entry/ceiling gauge. The generator supplies all fit
// dimensions; set cells_x, cells_y, bin_h, and design variables with -D.
// Print slab-down, then invert so the slab is above the tub for the fit test.
// This checks the mouth only; full-depth sliding and stacking remain separate.

use <../hutchfinity.scad>;

GAUGE_SLOT_DEPTH = 40;
GAUGE_BACK_THICKNESS = 8;

sized_casing_mouth_gauge(GAUGE_SLOT_DEPTH, GAUGE_BACK_THICKNESS);
