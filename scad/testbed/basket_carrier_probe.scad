// basket_carrier_probe.scad
// version: 0.1.0
// Experimental, general-parameter Basket/Carrier probe for issue #26.
// This is testbed geometry, not a fifth production module or a catalog SKU.
//
// Gridfinity Basket source:
//   https://github.com/LeKoYa/gridfinity-basket-openscad
//   pinned revision 549dc4015e4511daeb7b942de96d2531101701db
//   Copyright (c) 2025 LeKoYa, MIT License
// The unchanged upstream source and license are retained under
// scad/gridfinity/vendor/basket/.

use <../magnet_well.scad>;
use <../tub.scad>;

PROBE_PART = "candidate";
PROBE_FLOOR_MODE = "plain";
PROBE_MAGNETS = true;

MINI_CELLS_X = 6;
MINI_CELLS_Y = 16;
MINI_CELLS_Z = 23;
HUTCHFINITY_PITCH_XY = 21;
HUTCHFINITY_PITCH_Z = 3.5;
MINIMUM_LIP_Z = 3.74;

PROBE_WALL_THICKNESS = 2.2;
PROBE_ADDITIONAL_FLOOR_HEIGHT = 1.29;
PROBE_STANDOFF = 1.75;
PROBE_TOP_PADDING = 1.25;
PROBE_XY_TOLERANCE = 0.5;
PROBE_Z_TOLERANCE = 0.25;

// Current provisional tub-side interface from tub.scad v0.2.2.
PROBE_MAGNET_BORE_DIAMETER = 5.40;
PROBE_MAGNET_RIB_TIP_DIAMETER = 5.25;
PROBE_MAGNET_WELL_DEPTH = 1.10;
PROBE_MAGNET_CHAMFER = 0.30;
PROBE_MAGNET_FORE_AFT_INSET = 8.0;
PROBE_MAGNET_PARAMEDIAN_OFFSET = 21.0;

UPSTREAM_Z_UNIT = 7;
UPSTREAM_GRID_LIP_HEIGHT = 4.4;
UPSTREAM_MIN_WALL_THICKNESS = 0.4;

function basket_carrier_valid_floor_mode(floor_mode) =
    floor_mode == "plain" ||
    floor_mode == "integral" ||
    floor_mode == "removable";
function basket_carrier_grid_xy(cells_x, cells_y, pitch_xy) =
    [cells_x * pitch_xy, cells_y * pitch_xy];
function basket_carrier_outer_xy(cells_x, cells_y, pitch_xy, wall_thickness) =
    basket_carrier_grid_xy(cells_x, cells_y, pitch_xy) +
    [2 * wall_thickness, 2 * wall_thickness];
function basket_carrier_target_height(cells_z, pitch_z, minimum_lip_z) =
    cells_z * pitch_z + minimum_lip_z;
function basket_carrier_upstream_grid_z(
    target_height,
    wall_thickness,
    additional_floor_height,
    standoff,
    top_padding,
    z_tolerance
) =
    (
        target_height -
        UPSTREAM_GRID_LIP_HEIGHT -
        additional_floor_height -
        standoff -
        z_tolerance -
        (wall_thickness - UPSTREAM_MIN_WALL_THICKNESS) -
        top_padding
    ) / UPSTREAM_Z_UNIT;
function basket_carrier_plain_floor_z(
    wall_thickness,
    standoff,
    xy_tolerance,
    z_tolerance
) =
    standoff + z_tolerance + wall_thickness + xy_tolerance;
function basket_carrier_stack_offset(target_height, standoff, z_tolerance) =
    target_height - standoff - z_tolerance;
function basket_carrier_removable_grid_clearance() = [0, 0];

// The upstream file is included inside this module so its helper modules retain
// their original lexical scope. The assignments after the include supersede the
// upstream Customizer defaults with explicit adapter arguments.
module gridfinity_basket_from_pinned_source(
    adapter_baseplate_dimensions,
    adapter_grid_size,
    adapter_use_gridfinity_base,
    adapter_padding,
    adapter_wall_thickness,
    adapter_additional_floor_height,
    adapter_standoff,
    adapter_top_padding,
    adapter_xy_tolerance,
    adapter_z_tolerance
) {
    include <../gridfinity/vendor/basket/gridfinityBasket.scad>;

    BASEPLATE_DIMENSIONS = adapter_baseplate_dimensions;
    GridSize = adapter_grid_size;
    UseMulticolor = false;
    UseGridfinityBase = adapter_use_gridfinity_base;
    Padding = adapter_padding;
    WallThickness = adapter_wall_thickness;
    AdditionalFloorHeight = adapter_additional_floor_height;
    SolidFloor = true;
    MagnetDiameter = 0;
    MagnetHeight = 0;
    AddMagnetChamfer = false;
    WallPattern = 0;
    AddHandle = false;
    Standoff = adapter_standoff;
    TopPadding = adapter_top_padding;
    XYTolerance = adapter_xy_tolerance;
    ZTolerance = adapter_z_tolerance;
    Render = false;
}

module hutchfinity_basket_carrier_probe(
    cells_x = MINI_CELLS_X,
    cells_y = MINI_CELLS_Y,
    cells_z = MINI_CELLS_Z,
    pitch_xy = HUTCHFINITY_PITCH_XY,
    pitch_z = HUTCHFINITY_PITCH_Z,
    minimum_lip_z = MINIMUM_LIP_Z,
    floor_mode = PROBE_FLOOR_MODE,
    wall_thickness = PROBE_WALL_THICKNESS,
    additional_floor_height = PROBE_ADDITIONAL_FLOOR_HEIGHT,
    standoff = PROBE_STANDOFF,
    top_padding = PROBE_TOP_PADDING,
    xy_tolerance = PROBE_XY_TOLERANCE,
    z_tolerance = PROBE_Z_TOLERANCE,
    enable_magnet_holes = PROBE_MAGNETS,
    magnet_bore_diameter = PROBE_MAGNET_BORE_DIAMETER,
    magnet_rib_tip_diameter = PROBE_MAGNET_RIB_TIP_DIAMETER,
    magnet_well_depth = PROBE_MAGNET_WELL_DEPTH,
    magnet_chamfer = PROBE_MAGNET_CHAMFER,
    magnet_fore_aft_inset = PROBE_MAGNET_FORE_AFT_INSET,
    magnet_paramedian_offset = PROBE_MAGNET_PARAMEDIAN_OFFSET
) {
    outer_xy = basket_carrier_outer_xy(
        cells_x,
        cells_y,
        pitch_xy,
        wall_thickness
    );
    target_height = basket_carrier_target_height(
        cells_z,
        pitch_z,
        minimum_lip_z
    );
    upstream_grid_z = basket_carrier_upstream_grid_z(
        target_height,
        wall_thickness,
        additional_floor_height,
        standoff,
        top_padding,
        z_tolerance
    );
    use_integral_grid = floor_mode == "integral";
    magnet_positions = tub_magnet_positions(
        outer_xy.x,
        outer_xy.y,
        magnet_fore_aft_inset,
        magnet_paramedian_offset
    );

    assert(cells_x > 0 && cells_y > 0 && cells_z > 0,
        "basket carrier cell counts must be positive");
    assert(pitch_xy > 0 && pitch_z > 0,
        "basket carrier pitches must be positive");
    assert(wall_thickness >= UPSTREAM_MIN_WALL_THICKNESS,
        "basket carrier wall is below the upstream minimum");
    assert(basket_carrier_valid_floor_mode(floor_mode),
        str("unknown basket carrier floor mode: ", floor_mode));
    assert(upstream_grid_z >= 1,
        "mapped upstream grid height must be at least one standard unit");
    assert(!enable_magnet_holes || magnet_well_depth <
        basket_carrier_plain_floor_z(
            wall_thickness,
            standoff,
            xy_tolerance,
            z_tolerance
        ),
        "magnet wells must remain within the candidate floor");

    difference() {
        gridfinity_basket_from_pinned_source(
            [pitch_xy, pitch_xy],
            [cells_x, cells_y, upstream_grid_z],
            use_integral_grid,
            0,
            wall_thickness,
            additional_floor_height,
            standoff,
            top_padding,
            xy_tolerance,
            z_tolerance
        );

        if (enable_magnet_holes)
            let($fn = 64)
                hutchfinity_magnet_well_cuts(
                    magnet_positions,
                    magnet_bore_diameter,
                    magnet_rib_tip_diameter,
                    magnet_well_depth,
                    magnet_chamfer
                );
    }
}

module hutchfinity_basket_carrier_self_stack(
    floor_mode = PROBE_FLOOR_MODE,
    enable_magnet_holes = false
) {
    target_height = basket_carrier_target_height(
        MINI_CELLS_Z,
        HUTCHFINITY_PITCH_Z,
        MINIMUM_LIP_Z
    );
    stack_offset = basket_carrier_stack_offset(
        target_height,
        PROBE_STANDOFF,
        PROBE_Z_TOLERANCE
    );

    hutchfinity_basket_carrier_probe(
        floor_mode = floor_mode,
        enable_magnet_holes = enable_magnet_holes
    );
    translate([0, 0, stack_offset])
        hutchfinity_basket_carrier_probe(
            floor_mode = floor_mode,
            enable_magnet_holes = enable_magnet_holes
        );
}

module hutchfinity_basket_carrier_self_stack_intersection(
    floor_mode = PROBE_FLOOR_MODE
) {
    target_height = basket_carrier_target_height(
        MINI_CELLS_Z,
        HUTCHFINITY_PITCH_Z,
        MINIMUM_LIP_Z
    );
    stack_offset = basket_carrier_stack_offset(
        target_height,
        PROBE_STANDOFF,
        PROBE_Z_TOLERANCE
    );

    intersection() {
        hutchfinity_basket_carrier_probe(
            floor_mode = floor_mode,
            enable_magnet_holes = false
        );
        translate([0, 0, stack_offset])
            hutchfinity_basket_carrier_probe(
                floor_mode = floor_mode,
                enable_magnet_holes = false
            );
    }
}

assert(
    PROBE_PART == "candidate" ||
    PROBE_PART == "self-stack" ||
    PROBE_PART == "self-stack-intersection",
    str("unknown PROBE_PART: ", PROBE_PART)
);

if (PROBE_PART == "candidate") {
    hutchfinity_basket_carrier_probe();
} else if (PROBE_PART == "self-stack") {
    hutchfinity_basket_carrier_self_stack();
} else if (PROBE_PART == "self-stack-intersection") {
    hutchfinity_basket_carrier_self_stack_intersection();
}
