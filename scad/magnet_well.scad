// magnet_well.scad
// version: 0.2.0
// Shared disc-magnet press-fit recipes and well cutters. Product parts pass a
// named recipe so identical magnet specifications cannot drift by caller.

$fn = 64;
EPS = 0.01;

MAGNET_RECIPE_BORE_DIAMETER = 0;
MAGNET_RECIPE_RIB_TIP_DIAMETER = 1;
MAGNET_RECIPE_RIB_PROTRUSION = 2;
MAGNET_RECIPE_WELL_DEPTH = 3;
MAGNET_RECIPE_CHAMFER = 4;
MAGNET_RECIPE_RIB_COUNT = 5;
MAGNET_RECIPE_RIB_WIDTH = 6;
MAGNET_RECIPE_FIELD_COUNT = 7;

// Canonical product recipe for a 6 x 1.5mm disc magnet. The proven 0.25mm
// radial crush defines the 5.60mm rib-tip diameter from the 6.10mm bore.
// The selected 2.30mm depth remains pending physical confirmation.
function hutchfinity_magnet_recipe_6x1_5() =
    let(
        bore_diameter = 6.10,
        rib_protrusion = 0.25
    ) [
        bore_diameter,
        bore_diameter - 2 * rib_protrusion,
        rib_protrusion,
        2.30,
        0.30,
        8,
        0.80
    ];

function hutchfinity_magnet_recipe_bore_diameter(recipe) =
    recipe[MAGNET_RECIPE_BORE_DIAMETER];
function hutchfinity_magnet_recipe_rib_tip_diameter(recipe) =
    recipe[MAGNET_RECIPE_RIB_TIP_DIAMETER];
function hutchfinity_magnet_recipe_rib_protrusion(recipe) =
    recipe[MAGNET_RECIPE_RIB_PROTRUSION];
function hutchfinity_magnet_recipe_well_depth(recipe) =
    recipe[MAGNET_RECIPE_WELL_DEPTH];
function hutchfinity_magnet_recipe_chamfer(recipe) =
    recipe[MAGNET_RECIPE_CHAMFER];
function hutchfinity_magnet_recipe_rib_count(recipe) =
    recipe[MAGNET_RECIPE_RIB_COUNT];
function hutchfinity_magnet_recipe_rib_width(recipe) =
    recipe[MAGNET_RECIPE_RIB_WIDTH];

function hutchfinity_magnet_recipe_is_valid(recipe) =
    is_list(recipe) &&
    len(recipe) == MAGNET_RECIPE_FIELD_COUNT &&
    hutchfinity_magnet_recipe_bore_diameter(recipe) > 0 &&
    hutchfinity_magnet_recipe_rib_tip_diameter(recipe) > 0 &&
    hutchfinity_magnet_recipe_rib_protrusion(recipe) >= 0 &&
    abs(
        hutchfinity_magnet_recipe_bore_diameter(recipe) -
        hutchfinity_magnet_recipe_rib_tip_diameter(recipe) -
        2 * hutchfinity_magnet_recipe_rib_protrusion(recipe)
    ) <= EPS &&
    hutchfinity_magnet_recipe_well_depth(recipe) > 0 &&
    hutchfinity_magnet_recipe_chamfer(recipe) >= 0 &&
    hutchfinity_magnet_recipe_rib_count(recipe) >= 3 &&
    hutchfinity_magnet_recipe_rib_width(recipe) > 0;

module hutchfinity_magnet_well_cut(
    position,
    recipe = hutchfinity_magnet_recipe_6x1_5(),
    z = 0
) {
    bore_diameter = hutchfinity_magnet_recipe_bore_diameter(recipe);
    rib_tip_diameter = hutchfinity_magnet_recipe_rib_tip_diameter(recipe);
    rib_protrusion = hutchfinity_magnet_recipe_rib_protrusion(recipe);
    well_depth = hutchfinity_magnet_recipe_well_depth(recipe);
    well_chamfer = hutchfinity_magnet_recipe_chamfer(recipe);
    rib_count = hutchfinity_magnet_recipe_rib_count(recipe);
    rib_width = hutchfinity_magnet_recipe_rib_width(recipe);
    bore_r = bore_diameter / 2;
    tip_r = rib_tip_diameter / 2;
    chamfer = min(well_chamfer, well_depth / 2);
    rib_depth = max(EPS, well_depth - chamfer);

    assert(hutchfinity_magnet_recipe_is_valid(recipe),
        "magnet recipe must contain one consistent bore, rib, depth, chamfer, count, and width");

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
    recipe = hutchfinity_magnet_recipe_6x1_5(),
    z = 0
) {
    for (p = positions)
        hutchfinity_magnet_well_cut(p, recipe, z);
}
