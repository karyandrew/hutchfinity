// casing_core.scad
// version: 0.2.0
// Webbed casing walls. Each side and back wall keeps two flat skins and is
// otherwise hollowed into vertical pockets separated by cross webs, with a
// solid pillar around every peg bore. Pockets run from the top of the riding
// slab to the feet and are open there, so nothing bridges and the slab stays
// intact. Lengths are multiples of one deposited road (default 1.4 mm): a
// member of two roads is two contour loops with no infill between them.
//
// The layout depends only on plan dimensions (outer size, wall thicknesses,
// peg positions, bore, chamfer, road), never on height or slab thickness, so
// stacked casings with the same footprint put skin on skin and web on web.
//
// A pocket is [x0, y0, x1, y1] in casing coordinates, as printed slab-down.
// Placement, per wall (0 left side, 1 right side, 2 back):
//   side walls: x from one skin inside the exterior face to one skin inside the
//     slot face, y from one skin behind the front end to the back wall's inner
//     face; the corner blocks where a side wall meets the back wall stay solid
//   back wall: x between the two side walls, y one skin inside each face
// Along a wall, pockets fill the gaps between solid zones (the pillars and the
// wall ends): a gap is split into the fewest equal pockets whose pocket plus
// web is at most `pitch`, and a gap narrower than the minimum pocket is solid.
//
// The open-infill core builds no pockets. Its body is the solid casing, and this file
// supplies the setting regions that the generator exports beside it: a slab plate over
// the whole footprint and one block per peg bore (the same pillar zones as above).
// A region is [x0, y0, z0, x1, y1, z1]. Regions mark where the slicer must fill solid;
// they are never printed material.

// A casing with less cavity depth than this is built solid.
function casing_core_min_cavity_depth() = 8;
CORE_EPS = 0.01;

// Radius of the solid zone around a peg bore: the larger of the receiver and
// the mouth chamfer circle, plus the collar.
function casing_core_zone_radius(bore_diameter, mouth_chamfer, collar) =
    bore_diameter / 2 + max(0, mouth_chamfer) + collar;

// Which wall a peg centre sits on: 0 left, 1 right, 2 back.
function casing_core_peg_wall(position, outer_x, side_thickness) =
    abs(position[0] - side_thickness / 2) < 0.000001 ? 0 :
    abs(position[0] - (outer_x - side_thickness / 2)) < 0.000001 ? 1 : 2;

// The pillar around one peg: full wall thickness, reaching `radius` to each
// side along the wall. Shared by every mode that reinforces the bores.
function casing_core_pillar_zone(position, wall, side_thickness, back_thickness, radius) =
    wall == 2 ?
        [position[0] - radius, position[1] - back_thickness / 2,
         position[0] + radius, position[1] + back_thickness / 2] :
        [position[0] - side_thickness / 2, position[1] - radius,
         position[0] + side_thickness / 2, position[1] + radius];

function casing_core_pillar_zones(positions, outer_x, side_thickness, back_thickness, radius) =
    [for (p = positions)
        casing_core_pillar_zone(p, casing_core_peg_wall(p, outer_x, side_thickness),
            side_thickness, back_thickness, radius)];

// Pockets that fill one gap [lo, hi] between solid zones, as [start, end] pairs.
function casing_core_gap_pockets(lo, hi, web, pitch, min_pocket) =
    let(gap = hi - lo)
    gap < min_pocket - 0.000001 ? [] :
    let(count = max(1, ceil((gap + web) / pitch - 0.000001)),
        length = (gap + web) / count - web)
    length < min_pocket - 0.000001 ? [] :
    [for (i = [0 : count - 1]) [lo + i * (length + web), lo + i * (length + web) + length]];

// Pockets along one wall axis between `lo` and `hi`, around solid [start, end] zones.
function casing_core_axis_pockets(lo, hi, zones, web, pitch, min_pocket) =
    let(starts = concat([lo], [for (z = zones) z[1]]),
        ends = concat([for (z = zones) z[0]], [hi]))
    [for (i = [0 : len(starts) - 1])
        for (g = casing_core_gap_pockets(starts[i], ends[i], web, pitch, min_pocket)) g];

function casing_core_rect_gap(a, b) =
    norm([max(a[0] - b[2], b[0] - a[2], 0), max(a[1] - b[3], b[1] - a[3], 0)]);

// All pockets of a casing, as [x0, y0, x1, y1]. `positions` are the peg
// centres; a pocket that would come within `radius` of any of them is dropped.
function casing_core_pockets(outer_x, outer_y, side_thickness, back_thickness, positions, radius,
    skin, web, pitch, min_pocket) =
    let(
        zones = casing_core_pillar_zones(positions, outer_x, side_thickness, back_thickness, radius),
        walls = [for (p = positions) casing_core_peg_wall(p, outer_x, side_thickness)],
        slot_end = outer_y - back_thickness,
        left = side_thickness - 2 * skin >= min_pocket ?
            [for (g = casing_core_axis_pockets(skin, slot_end,
                    [for (i = [0 : len(zones) - 1]) if (walls[i] == 0) [zones[i][1], zones[i][3]]],
                    web, pitch, min_pocket))
                [skin, g[0], side_thickness - skin, g[1]]] : [],
        right = side_thickness - 2 * skin >= min_pocket ?
            [for (g = casing_core_axis_pockets(skin, slot_end,
                    [for (i = [0 : len(zones) - 1]) if (walls[i] == 1) [zones[i][1], zones[i][3]]],
                    web, pitch, min_pocket))
                [outer_x - side_thickness + skin, g[0], outer_x - skin, g[1]]] : [],
        back = back_thickness - 2 * skin >= min_pocket ?
            [for (g = casing_core_axis_pockets(side_thickness, outer_x - side_thickness,
                    [for (i = [0 : len(zones) - 1]) if (walls[i] == 2) [zones[i][0], zones[i][2]]],
                    web, pitch, min_pocket))
                [g[0], outer_y - back_thickness + skin, g[1], outer_y - skin]] : [],
        all = concat(left, right, back)
    )
    [for (r = all) if (len([for (p = positions) if (casing_core_rect_gap(r, [p[0], p[1], p[0], p[1]]) < radius - 0.000001) 1]) == 0) r];

function casing_core_pocket_area(pockets) =
    len(pockets) == 0 ? 0 : casing_core_sum([for (r = pockets) (r[2] - r[0]) * (r[3] - r[1])]);

function casing_core_sum(values, i = 0) = i >= len(values) ? 0 : values[i] + casing_core_sum(values, i + 1);

// Plan area of the three wall footprints together.
function casing_core_footprint_area(outer_x, outer_y, side_thickness, back_thickness) =
    outer_x * outer_y - (outer_x - 2 * side_thickness) * (outer_y - back_thickness);

// Share of the wall footprint that is solid at the feet (bores not counted).
function casing_core_foot_bearing(outer_x, outer_y, side_thickness, back_thickness, pockets) =
    1 - casing_core_pocket_area(pockets) / casing_core_footprint_area(outer_x, outer_y, side_thickness, back_thickness);

// The pockets as vertical prisms from the top of the slab up through the feet.
module casing_core_pocket_cuts(pockets, slab_top, feet) {
    for (r = pockets)
        translate([r[0], r[1], slab_top])
            cube([r[2] - r[0], r[3] - r[1], feet - slab_top + CORE_EPS]);
}

// Setting regions of the open-infill core: the slab plate (the whole footprint from the
// bed to the top of the riding slab), then one block per peg bore, from the bed to the
// feet, over the same pillar zone the webbed core keeps solid.
function casing_core_regions(outer_x, outer_y, side_thickness, back_thickness, slab, height, positions, radius) =
    concat(
        [[0, 0, 0, outer_x, outer_y, slab]],
        [for (z = casing_core_pillar_zones(positions, outer_x, side_thickness, back_thickness, radius))
            [z[0], z[1], 0, z[2], z[3], height]]);

module casing_core_region_volume(region) {
    translate([region[0], region[1], region[2]])
        cube([region[3] - region[0], region[4] - region[1], region[5] - region[2]]);
}

// All regions together, or the one at `index`.
module casing_core_region_volumes(regions, index=undef) {
    if (is_undef(index))
        for (region = regions) casing_core_region_volume(region);
    else
        casing_core_region_volume(regions[index]);
}
