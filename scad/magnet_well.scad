// magnet_well.scad
// version: 0.1.0
// Shared disc-magnet press-fit well cutter. The cut volume is a bore with
// triangular notches removed from it, so the printed part retains inward ribs.

$fn = 64;
EPS = 0.01;
MAGNET_RIB_COUNT = 8;
MAGNET_RIB_WIDTH = 0.8;

module hutchfinity_magnet_well_cut(
    position,
    bore_diameter,
    rib_tip_diameter,
    well_depth,
    well_chamfer,
    rib_count = MAGNET_RIB_COUNT,
    rib_width = MAGNET_RIB_WIDTH,
    z = 0
) {
    bore_r = bore_diameter / 2;
    tip_r = rib_tip_diameter / 2;
    rib_protrusion = bore_r - tip_r;
    chamfer = min(well_chamfer, well_depth / 2);
    rib_depth = max(EPS, well_depth - chamfer);

    assert(bore_diameter > 0 && rib_tip_diameter > 0,
        "magnet well diameters must be positive");
    assert(rib_tip_diameter <= bore_diameter,
        "magnet well rib-tip diameter must not exceed bore diameter");
    assert(well_depth > 0 && well_chamfer >= 0,
        "magnet well depth must be positive and chamfer must be non-negative");
    assert(rib_count >= 3 && rib_width > 0,
        "magnet rib count and width must be positive");

    translate([position[0], position[1], z - EPS])
    union() {
        cylinder(r1=bore_r + chamfer, r2=bore_r, h=chamfer + EPS);

        translate([0, 0, chamfer])
        difference() {
            cylinder(r=bore_r, h=rib_depth + 2 * EPS);

            if (rib_protrusion > EPS) {
                for (i = [0 : rib_count - 1]) {
                    rotate([0, 0, i * (360 / rib_count)])
                    linear_extrude(height=rib_depth + 3 * EPS)
                    polygon([
                        [tip_r, 0],
                        [bore_r, -rib_width / 2],
                        [bore_r, rib_width / 2]
                    ]);
                }
            }
        }
    }
}

module hutchfinity_magnet_well_cuts(
    positions,
    bore_diameter,
    rib_tip_diameter,
    well_depth,
    well_chamfer,
    rib_count = MAGNET_RIB_COUNT,
    rib_width = MAGNET_RIB_WIDTH
) {
    for (p = positions)
        hutchfinity_magnet_well_cut(
            p,
            bore_diameter,
            rib_tip_diameter,
            well_depth,
            well_chamfer,
            rib_count,
            rib_width
        );
}
