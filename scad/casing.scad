// casing.scad
// version: 0.13.0
// First-pass Hutchfinity casing shell. Standalone slot geometry: no tub import,
// no front, no bottom. Continuous hourglass peg bores connect both faces
// inside the flat side/back wall footprints. Optional legacy magnet wells
// remain a separate, physically unvalidated interface. casing_core selects the
// wall construction: "solid" (default) or "webbed" (casing_core.scad). "open-infill"
// is a named value that is not yet available and is refused.

use <magnet_well.scad>;
use <peg.scad>;
use <casing_core.scad>;

$fn = 64;
EPS = 0.01;

// Representative first-pass parameters. These describe the casing slot directly;
// hutchfinity-assembly.scad is responsible for choosing values that match a tub.
// Current default uses the tub's shared 16-cell front-to-back dimension as
// drawer travel depth; casing width follows tub width.
// The default height tracks the 20h integral-grid tub in tub.scad.
SLOT_WIDTH = 256.4;
SLOT_DEPTH = 340.4;
SLOT_HEIGHT = 79.84;
SIDE_THICKNESS = 25;
BACK_THICKNESS = 25;
TOP_THICKNESS = 3;
PEG_SPACING = 190.0;
PEG_DIAMETER = 8.0;
PEG_CLEARANCE = 0.45;
PEG_SOCKET_DEPTH = 10;
PEG_CHAMFER = 2.5;
PEG_END_CHAMFER = 2.5;
PEG_THROAT_REDUCTION = 1.0;
PEG_SOCKET_EDGE_LAND = 4.0;
ENABLE_PEG_HOLES = true;
ENABLE_MAGNET_HOLES = false;
CASING_MAGNET_BORE_DIAMETER = 6.40;
CASING_MAGNET_RIB_TIP_DIAMETER = 6.10;
CASING_MAGNET_WELL_DEPTH = 1.60;
CASING_MAGNET_CHAMFER = 0.30;
CASING_MAGNET_FORE_AFT_INSET = 8.0;
CASING_MAGNET_PARAMEDIAN_OFFSET = 21.0;
EXTENDED_WARNING_TRAVEL_FRACTION = 0.75;
SHOW_DEBUG_MARKERS = false;

DEBUG_MARKER_D = 3.0;

function casing_outer_x(slot_width, side_thickness) = slot_width + 2 * side_thickness;
function casing_outer_y(slot_depth, back_thickness) = slot_depth + back_thickness;
function casing_print_z(slot_height, top_thickness) = top_thickness + slot_height;
function peg_socket_diameter(peg_diameter, peg_clearance) = peg_diameter + peg_clearance;
function peg_socket_opening_radius(peg_diameter, peg_clearance, peg_chamfer) =
    peg_socket_diameter(peg_diameter, peg_clearance) / 2 + peg_chamfer;
function peg_socket_inset(peg_diameter, peg_clearance, peg_chamfer, edge_land=PEG_SOCKET_EDGE_LAND) =
    peg_socket_opening_radius(peg_diameter, peg_clearance, peg_chamfer) + edge_land;
function peg_socket_end_inset(side_thickness, back_thickness, peg_diameter, peg_clearance, peg_chamfer, edge_land) =
    max(
        max(side_thickness, back_thickness),
        peg_socket_inset(peg_diameter, peg_clearance, peg_chamfer, edge_land)
    );

// Peg reference points are derived from one spacing target. Centers sit on the
// side/back wall centerlines so stack sockets do not require exterior lands.
// Spacing is a target, subordinate to keeping a material web between mouths.
// A short or reversed span has one centered position, never overlapping ends.
function peg_axis_intervals_between(start, end, peg_spacing, minimum_spacing=0) =
    let(usable = end - start,
        wanted = max(1, ceil(usable / peg_spacing)),
        available = minimum_spacing > 0 ? floor(usable / minimum_spacing) : wanted)
    usable <= 0 || available < 1 ? 0 : min(wanted, available);
function peg_axis_positions_between(start, end, peg_spacing, minimum_spacing=0) =
    let(intervals = peg_axis_intervals_between(start, end, peg_spacing, minimum_spacing), usable = end - start)
    intervals == 0 ? [(start + end) / 2] :
        [for (i = [0 : intervals]) start + i * usable / intervals];
function peg_axis_middle_positions_between(start, end, peg_spacing, minimum_spacing=0) =
    let(intervals = peg_axis_intervals_between(start, end, peg_spacing, minimum_spacing), usable = end - start)
    intervals <= 1 ? [] : [for (i = [1 : intervals - 1]) start + i * usable / intervals];
function peg_side_y_positions(depth, peg_spacing, end_inset, minimum_spacing=0) =
    peg_axis_positions_between(end_inset, depth - end_inset, peg_spacing, minimum_spacing);
function peg_back_x_positions(width, peg_spacing, end_inset, minimum_spacing=0) =
    peg_axis_middle_positions_between(end_inset, width - end_inset, peg_spacing, minimum_spacing);
function peg_reference_positions(width, depth, side_thickness, back_thickness, peg_spacing, end_inset,
    minimum_spacing=PEG_DIAMETER + PEG_CLEARANCE + 2 * PEG_CHAMFER + 2 * PEG_SOCKET_EDGE_LAND) = concat(
    [for (y = peg_side_y_positions(depth, peg_spacing, end_inset, minimum_spacing))
        [side_thickness / 2, y]],
    [for (y = peg_side_y_positions(depth, peg_spacing, end_inset, minimum_spacing))
        [width - side_thickness / 2, y]],
    [for (x = peg_back_x_positions(width, peg_spacing, end_inset, minimum_spacing))
        [x, depth - back_thickness / 2]]
);
function casing_peg_positions(width, depth, side_thickness, back_thickness, peg_spacing,
    socket_diameter, socket_chamfer, edge_land) =
    peg_reference_positions(width, depth, side_thickness, back_thickness, peg_spacing,
        peg_socket_end_inset(side_thickness, back_thickness, socket_diameter, 0, socket_chamfer, edge_land),
        socket_diameter + 2 * socket_chamfer + 2 * edge_land);
function peg_count(width, depth, side_thickness, back_thickness, peg_spacing, end_inset) =
    len(peg_reference_positions(width, depth, side_thickness, back_thickness, peg_spacing, end_inset));
function magnet_column_offsets(paramedian_offset) =
    paramedian_offset == 0 ? [0] : [-paramedian_offset, 0, paramedian_offset];
function casing_magnet_x_positions(slot_width, side_thickness, magnet_paramedian_offset) =
    [for (x = magnet_column_offsets(magnet_paramedian_offset))
        side_thickness + slot_width / 2 + x];
function casing_closed_magnet_positions(slot_width, slot_depth, side_thickness, magnet_fore_aft_inset, magnet_paramedian_offset) =
    [for (x = casing_magnet_x_positions(slot_width, side_thickness, magnet_paramedian_offset))
        for (y = [magnet_fore_aft_inset, slot_depth - magnet_fore_aft_inset])
            [x, y]];
function casing_extended_warning_magnet_y(slot_depth, magnet_fore_aft_inset, travel_fraction) =
    slot_depth - magnet_fore_aft_inset - slot_depth * travel_fraction;
function casing_extended_warning_magnet_positions(slot_width, slot_depth, side_thickness, magnet_fore_aft_inset, magnet_paramedian_offset, travel_fraction) =
    [for (x = casing_magnet_x_positions(slot_width, side_thickness, magnet_paramedian_offset))
        [x, casing_extended_warning_magnet_y(slot_depth, magnet_fore_aft_inset, travel_fraction)]];
function casing_magnet_positions(slot_width, slot_depth, side_thickness, magnet_fore_aft_inset, magnet_paramedian_offset, travel_fraction) =
    concat(
        casing_closed_magnet_positions(slot_width, slot_depth, side_thickness, magnet_fore_aft_inset, magnet_paramedian_offset),
        casing_extended_warning_magnet_positions(slot_width, slot_depth, side_thickness, magnet_fore_aft_inset, magnet_paramedian_offset, travel_fraction)
    );

module casing_shell(outer_x, outer_y, print_z, side_thickness, back_thickness, top_thickness) {
    union() {
        // Top slab: bed-facing in print, upper riding surface in installed use.
        cube([outer_x, outer_y, top_thickness]);

        // Side and back walls rise from the top slab in print orientation.
        cube([side_thickness, outer_y, print_z]);
        translate([outer_x - side_thickness, 0, 0]) cube([side_thickness, outer_y, print_z]);
        translate([0, outer_y - back_thickness, 0]) cube([outer_x, back_thickness, print_z]);
    }
}

module chamfered_peg_socket_cut(position, socket_diameter, socket_depth, socket_chamfer, z=0) {
    chamfer = min(socket_chamfer, socket_depth / 2);
    translate([position[0], position[1], z - EPS])
    union() {
        cylinder(d=socket_diameter, h=socket_depth + 2 * EPS);
        cylinder(d1=socket_diameter + 2 * chamfer, d2=socket_diameter, h=chamfer + EPS);
        translate([0, 0, socket_depth - chamfer])
            cylinder(d1=socket_diameter, d2=socket_diameter + 2 * chamfer, h=chamfer + 2 * EPS);
    }
}

module chamfered_peg_socket_cuts(positions, socket_diameter, socket_depth, socket_chamfer) {
    for (p = positions)
        chamfered_peg_socket_cut(p, socket_diameter, socket_depth, socket_chamfer);
}

module chamfered_peg_foot_socket_cuts(positions, socket_diameter, socket_depth, socket_chamfer, print_z) {
    for (p = positions)
        chamfered_peg_socket_cut(
            p,
            socket_diameter,
            socket_depth,
            socket_chamfer,
            print_z - socket_depth
        );
}

// The peg tip may enter the smaller through-bore. Match the narrowing taper
// to the peg's end taper, so insertion_depth names the actual maximum tip
// depth, not the end of a straight cylinder. Default: 10 mm tip depth,
// 2.5 mm peg chamfer => 7.5 mm full-diameter receiver + 0.5 mm transition.
function peg_receiver_depth(insertion_depth, peg_end_chamfer) =
    insertion_depth - peg_end_chamfer;
function peg_socket_transition_height(socket_diameter, peg_end_chamfer, throat_reduction) =
    peg_end_chamfer == 0 ? throat_reduction / 2 :
    peg_end_chamfer * throat_reduction /
        (socket_diameter - peg_tip_diameter(socket_diameter, peg_end_chamfer));

module through_peg_socket_cut(position, socket_diameter, print_z, insertion_depth,
    socket_chamfer, peg_end_chamfer, throat_reduction=PEG_THROAT_REDUCTION) {
    receiver = peg_receiver_depth(insertion_depth, peg_end_chamfer);
    transition = peg_socket_transition_height(socket_diameter, peg_end_chamfer, throat_reduction);
    throat = socket_diameter - throat_reduction;
    mouth_chamfer = min(socket_chamfer, receiver);

    assert(throat_reduction > 0 && throat > 0, "peg throat must be smaller than the receiver and remain open");
    assert(peg_end_chamfer >= 0 && receiver > 0, "peg needs a positive full-diameter receiving zone");
    assert(socket_chamfer >= 0, "socket opening chamfer must be non-negative");
    assert(print_z > 2 * (receiver + transition), "casing is too short for two receivers and a stop throat");

    module receiving_end() {
        translate([0, 0, -EPS]) cylinder(d=socket_diameter, h=receiver + EPS);
        translate([0, 0, receiver]) cylinder(d1=socket_diameter, d2=throat, h=transition);
        if (mouth_chamfer > 0)
            translate([0, 0, -EPS])
                cylinder(d1=socket_diameter + 2 * mouth_chamfer,
                    d2=socket_diameter, h=mouth_chamfer + EPS);
    }

    translate([position[0], position[1], 0]) union() {
        translate([0, 0, -EPS]) cylinder(d=throat, h=print_z + 2 * EPS);
        receiving_end();
        translate([0, 0, print_z]) mirror([0, 0, 1]) receiving_end();
    }
}

module through_peg_socket_cuts(positions, socket_diameter, print_z, insertion_depth,
    socket_chamfer, peg_end_chamfer, throat_reduction=PEG_THROAT_REDUCTION) {
    for (p = positions)
        through_peg_socket_cut(p, socket_diameter, print_z, insertion_depth,
            socket_chamfer, peg_end_chamfer, throat_reduction);
}

module peg_debug_markers(positions) {
    color([0.1, 0.35, 0.9, 0.35])
    for (p = positions)
        translate([p[0], p[1], 0.15]) cylinder(d=DEBUG_MARKER_D, h=0.4);
}

module hutchfinity_casing(
    slot_width=SLOT_WIDTH,
    slot_depth=SLOT_DEPTH,
    slot_height=SLOT_HEIGHT,
    side_thickness=SIDE_THICKNESS,
    back_thickness=BACK_THICKNESS,
    top_thickness=TOP_THICKNESS,
    peg_spacing=PEG_SPACING,
    peg_diameter=PEG_DIAMETER,
    peg_clearance=PEG_CLEARANCE,
    peg_socket_depth=PEG_SOCKET_DEPTH,
    peg_chamfer=PEG_CHAMFER,
    peg_socket_edge_land=PEG_SOCKET_EDGE_LAND,
    enable_peg_holes=ENABLE_PEG_HOLES,
    enable_magnet_holes=ENABLE_MAGNET_HOLES,
    casing_magnet_bore_diameter=CASING_MAGNET_BORE_DIAMETER,
    casing_magnet_rib_tip_diameter=CASING_MAGNET_RIB_TIP_DIAMETER,
    casing_magnet_well_depth=CASING_MAGNET_WELL_DEPTH,
    casing_magnet_chamfer=CASING_MAGNET_CHAMFER,
    casing_magnet_fore_aft_inset=CASING_MAGNET_FORE_AFT_INSET,
    casing_magnet_paramedian_offset=CASING_MAGNET_PARAMEDIAN_OFFSET,
    casing_magnet_drawer_depth=undef,
    extended_warning_travel_fraction=EXTENDED_WARNING_TRAVEL_FRACTION,
    show_debug_markers=SHOW_DEBUG_MARKERS,
    peg_end_chamfer=PEG_END_CHAMFER,
    peg_throat_reduction=PEG_THROAT_REDUCTION,
    casing_core="solid",
    core_road=1.4,
    core_skin=undef,
    core_web=undef,
    core_collar=undef,
    web_pitch=24
) {
    outer_x = casing_outer_x(slot_width, side_thickness);
    outer_y = casing_outer_y(slot_depth, back_thickness);
    print_z = casing_print_z(slot_height, top_thickness);
    socket_diameter = peg_socket_diameter(peg_diameter, peg_clearance);
    // Socket engagement is in the side/back walls, independent of slab thickness.
    socket_depth = min(peg_socket_depth, (print_z - 2) / 2);
    socket_peg_chamfer = min(peg_end_chamfer, (2 * socket_depth - 0.4) / 4);
    socket_opening_radius = peg_socket_opening_radius(peg_diameter, peg_clearance, peg_chamfer);
    magnet_drawer_depth = is_undef(casing_magnet_drawer_depth) ?
        slot_depth :
        casing_magnet_drawer_depth;
    peg_positions = casing_peg_positions(
        outer_x,
        outer_y,
        side_thickness,
        back_thickness,
        peg_spacing,
        socket_diameter,
        peg_chamfer,
        peg_socket_edge_land
    );
    magnet_positions = casing_magnet_positions(
        slot_width,
        magnet_drawer_depth,
        side_thickness,
        casing_magnet_fore_aft_inset,
        casing_magnet_paramedian_offset,
        extended_warning_travel_fraction
    );

    webbed = casing_core == "webbed";
    skin = is_undef(core_skin) ? 2 * core_road : core_skin;
    web = is_undef(core_web) ? 2 * core_road : core_web;
    collar = is_undef(core_collar) ? 2 * core_road : core_collar;
    min_pocket = 3 * core_road;
    core_radius = casing_core_zone_radius(socket_diameter, peg_chamfer, collar);
    // Pillars exist only where there are bores; the gate keeps shallow casings solid.
    core_pockets = webbed && print_z - top_thickness >= casing_core_min_cavity_depth() ?
        casing_core_pockets(outer_x, outer_y, side_thickness, back_thickness,
            enable_peg_holes ? peg_positions : [], core_radius, skin, web, web_pitch, min_pocket) : [];

    assert(casing_core != "open-infill", "casing_core open-infill is not yet available; use solid or webbed");
    assert(casing_core == "solid" || webbed, "unknown casing_core: use solid or webbed");
    assert(!webbed || (core_road > 0 && skin > 0 && web > 0 && collar > 0),
        "core road, skin, web and collar must be positive");
    assert(!webbed || web_pitch >= web + min_pocket,
        "web_pitch must leave room for a web and a minimum pocket");
    assert(slot_width > 0 && slot_depth > 0 && slot_height > 0,
        "slot dimensions must be positive");
    assert(side_thickness > 0 && back_thickness > 0 && top_thickness > 0,
        "side, back, and top thicknesses must be positive");
    assert(peg_spacing > 0, "peg_spacing must be positive");
    assert(peg_diameter > 0 && peg_clearance >= 0,
        "peg diameter must be positive and peg clearance must be non-negative");
    assert(peg_socket_depth > 0 && peg_chamfer >= 0,
        "peg socket depth must be positive and peg chamfer must be non-negative");
    assert(peg_socket_edge_land > 0,
        "peg socket edge land must leave material beyond the chamfer opening");
    assert(casing_magnet_bore_diameter > 0 && casing_magnet_rib_tip_diameter > 0,
        "casing magnet diameters must be positive");
    assert(casing_magnet_rib_tip_diameter <= casing_magnet_bore_diameter,
        "casing magnet rib-tip diameter must not exceed bore diameter");
    assert(casing_magnet_well_depth > 0 && casing_magnet_chamfer >= 0,
        "casing magnet well depth must be positive and chamfer must be non-negative");
    assert(casing_magnet_fore_aft_inset > casing_magnet_bore_diameter / 2,
        "casing magnet fore/aft inset must keep wells inside the tub footprint");
    assert(casing_magnet_paramedian_offset >= 0,
        "casing magnet paramedian offset must be non-negative");
    assert(!enable_magnet_holes || casing_magnet_paramedian_offset < slot_width / 2 - casing_magnet_bore_diameter / 2,
        "casing magnet paramedian columns must stay inside the slot width");
    assert(extended_warning_travel_fraction > 0 && extended_warning_travel_fraction < 1,
        "extended warning travel fraction must be between 0 and 1");
    assert(!enable_magnet_holes || magnet_drawer_depth > 2 * casing_magnet_fore_aft_inset,
        "casing magnet drawer depth must leave room for closed-position fore/aft wells");
    assert(!enable_magnet_holes || casing_magnet_well_depth < top_thickness,
        "casing magnet wells must be shallower than the top slab");
    assert(!enable_magnet_holes ||
           casing_extended_warning_magnet_y(magnet_drawer_depth, casing_magnet_fore_aft_inset, extended_warning_travel_fraction) >
               casing_magnet_fore_aft_inset,
        "extended-warning magnets must remain inside the casing top footprint");
    assert(!enable_peg_holes ||
           (outer_x >= 2 * (socket_opening_radius + peg_socket_edge_land) &&
            outer_y >= 2 * (socket_opening_radius + peg_socket_edge_land)),
        "peg sockets must fit inside the casing footprint");
    assert(!enable_peg_holes ||
           (side_thickness / 2 >= socket_opening_radius + peg_socket_edge_land &&
            back_thickness / 2 >= socket_opening_radius + peg_socket_edge_land),
        "peg socket chamfer must fit inside the side/back wall thickness with edge land");

    difference() {
        casing_shell(outer_x, outer_y, print_z, side_thickness, back_thickness, top_thickness);
        if (webbed) casing_core_pocket_cuts(core_pockets, top_thickness, print_z);
        if (enable_peg_holes) {
            through_peg_socket_cuts(peg_positions, socket_diameter, print_z,
                socket_depth, peg_chamfer, socket_peg_chamfer, peg_throat_reduction);
        }
        if (enable_magnet_holes)
            hutchfinity_magnet_well_cuts(
                magnet_positions,
                casing_magnet_bore_diameter,
                casing_magnet_rib_tip_diameter,
                casing_magnet_well_depth,
                casing_magnet_chamfer
            );
    }

    if (webbed)
        echo(str("casing core: webbed; pockets=", len(core_pockets), "; foot_bearing=",
            round(1000 * casing_core_foot_bearing(outer_x, outer_y, side_thickness, back_thickness,
                core_pockets)) / 1000));

    if (show_debug_markers && !enable_peg_holes)
        %peg_debug_markers(peg_positions);
}

hutchfinity_casing();
