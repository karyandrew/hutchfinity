// tub.scad
// version: 0.2.2
// Hutchfinity tub wrappers with provisional bottom magnet wells.

use <magnet_well.scad>;

$fn = 64;
EPS = 0.01;

MINI_TUB_EXTERIOR_X = 130.4;
REGULAR_TUB_EXTERIOR_X = 256.4;
MEGA_TUB_EXTERIOR_X = 382.4;
STANDARD_TUB_EXTERIOR_Y = 340.4;
MINI_TUB_STL = "gridfinity/stl/tub-mini.stl";
REGULAR_TUB_STL = "gridfinity/stl/tub-regular.stl";
MEGA_TUB_STL = "gridfinity/stl/tub-mega.stl";
TUB_MAGNET_BORE_DIAMETER = 5.40;
TUB_MAGNET_RIB_TIP_DIAMETER = 5.25;
TUB_MAGNET_WELL_DEPTH = 1.10;
TUB_MAGNET_CHAMFER = 0.30;
TUB_MAGNET_FORE_AFT_INSET = 8.0;
TUB_MAGNET_PARAMEDIAN_OFFSET = 21.0;

function magnet_column_offsets(paramedian_offset) =
    paramedian_offset == 0 ? [0] : [-paramedian_offset, 0, paramedian_offset];
function tub_magnet_positions(tub_x, tub_y, magnet_fore_aft_inset, magnet_paramedian_offset) =
    [for (y = [-tub_y / 2 + magnet_fore_aft_inset, tub_y / 2 - magnet_fore_aft_inset])
        for (x = magnet_column_offsets(magnet_paramedian_offset))
            [x, y]];

module hutchfinity_tub_from_stl(
    tub_stl,
    enable_magnet_holes = true,
    tub_x = REGULAR_TUB_EXTERIOR_X,
    tub_y = STANDARD_TUB_EXTERIOR_Y,
    tub_magnet_bore_diameter = TUB_MAGNET_BORE_DIAMETER,
    tub_magnet_rib_tip_diameter = TUB_MAGNET_RIB_TIP_DIAMETER,
    tub_magnet_well_depth = TUB_MAGNET_WELL_DEPTH,
    tub_magnet_chamfer = TUB_MAGNET_CHAMFER,
    tub_magnet_fore_aft_inset = TUB_MAGNET_FORE_AFT_INSET,
    tub_magnet_paramedian_offset = TUB_MAGNET_PARAMEDIAN_OFFSET
) {
    magnet_positions = tub_magnet_positions(tub_x, tub_y, tub_magnet_fore_aft_inset, tub_magnet_paramedian_offset);

    assert(tub_x > 0 && tub_y > 0, "tub dimensions must be positive");
    assert(tub_magnet_bore_diameter > 0 && tub_magnet_rib_tip_diameter > 0,
        "tub magnet diameters must be positive");
    assert(tub_magnet_rib_tip_diameter <= tub_magnet_bore_diameter,
        "tub magnet rib-tip diameter must not exceed bore diameter");
    assert(tub_magnet_well_depth > 0 && tub_magnet_chamfer >= 0,
        "tub magnet well depth must be positive and chamfer must be non-negative");
    assert(tub_magnet_fore_aft_inset > tub_magnet_bore_diameter / 2,
        "tub magnet fore/aft inset must keep wells inside the tub footprint");
    assert(tub_magnet_paramedian_offset >= 0,
        "tub magnet paramedian offset must be non-negative");
    assert(tub_magnet_paramedian_offset < tub_x / 2 - tub_magnet_bore_diameter / 2,
        "tub magnet paramedian columns must stay inside the tub footprint");

    difference() {
        import(tub_stl);
        if (enable_magnet_holes)
            hutchfinity_magnet_well_cuts(
                magnet_positions,
                tub_magnet_bore_diameter,
                tub_magnet_rib_tip_diameter,
                tub_magnet_well_depth,
                tub_magnet_chamfer
            );
    }
}

module hutchfinity_mini_tub(
    enable_magnet_holes = true,
    tub_magnet_bore_diameter = TUB_MAGNET_BORE_DIAMETER,
    tub_magnet_rib_tip_diameter = TUB_MAGNET_RIB_TIP_DIAMETER,
    tub_magnet_well_depth = TUB_MAGNET_WELL_DEPTH,
    tub_magnet_chamfer = TUB_MAGNET_CHAMFER,
    tub_magnet_fore_aft_inset = TUB_MAGNET_FORE_AFT_INSET,
    tub_magnet_paramedian_offset = TUB_MAGNET_PARAMEDIAN_OFFSET
) {
    hutchfinity_tub_from_stl(
        MINI_TUB_STL,
        enable_magnet_holes,
        MINI_TUB_EXTERIOR_X,
        STANDARD_TUB_EXTERIOR_Y,
        tub_magnet_bore_diameter,
        tub_magnet_rib_tip_diameter,
        tub_magnet_well_depth,
        tub_magnet_chamfer,
        tub_magnet_fore_aft_inset,
        tub_magnet_paramedian_offset
    );
}

module hutchfinity_regular_tub(
    enable_magnet_holes = true,
    tub_magnet_bore_diameter = TUB_MAGNET_BORE_DIAMETER,
    tub_magnet_rib_tip_diameter = TUB_MAGNET_RIB_TIP_DIAMETER,
    tub_magnet_well_depth = TUB_MAGNET_WELL_DEPTH,
    tub_magnet_chamfer = TUB_MAGNET_CHAMFER,
    tub_magnet_fore_aft_inset = TUB_MAGNET_FORE_AFT_INSET,
    tub_magnet_paramedian_offset = TUB_MAGNET_PARAMEDIAN_OFFSET
) {
    hutchfinity_tub_from_stl(
        REGULAR_TUB_STL,
        enable_magnet_holes,
        REGULAR_TUB_EXTERIOR_X,
        STANDARD_TUB_EXTERIOR_Y,
        tub_magnet_bore_diameter,
        tub_magnet_rib_tip_diameter,
        tub_magnet_well_depth,
        tub_magnet_chamfer,
        tub_magnet_fore_aft_inset,
        tub_magnet_paramedian_offset
    );
}

module hutchfinity_mega_tub(
    enable_magnet_holes = true,
    tub_magnet_bore_diameter = TUB_MAGNET_BORE_DIAMETER,
    tub_magnet_rib_tip_diameter = TUB_MAGNET_RIB_TIP_DIAMETER,
    tub_magnet_well_depth = TUB_MAGNET_WELL_DEPTH,
    tub_magnet_chamfer = TUB_MAGNET_CHAMFER,
    tub_magnet_fore_aft_inset = TUB_MAGNET_FORE_AFT_INSET,
    tub_magnet_paramedian_offset = TUB_MAGNET_PARAMEDIAN_OFFSET
) {
    hutchfinity_tub_from_stl(
        MEGA_TUB_STL,
        enable_magnet_holes,
        MEGA_TUB_EXTERIOR_X,
        STANDARD_TUB_EXTERIOR_Y,
        tub_magnet_bore_diameter,
        tub_magnet_rib_tip_diameter,
        tub_magnet_well_depth,
        tub_magnet_chamfer,
        tub_magnet_fore_aft_inset,
        tub_magnet_paramedian_offset
    );
}

hutchfinity_regular_tub();
