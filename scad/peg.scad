// peg.scad
// version: 0.3.0
// Prototype laid-down hex-core crush-rib peg for vertical Hutchfinity casing stacks.

$fn = 64;
EPS = 0.01;

PEG_DIAMETER = 8.0;
PEG_LENGTH = 20.0;
PEG_END_CHAMFER = 2.5;
PEG_CORE_SIDES = 6;
PEG_PRINT_FACE_ROTATION = 30;
PEG_CRUSH_RIBS = true;
PEG_RIB_COUNT = 6;
PEG_RIB_ROOT_RELIEF = 0.60;
PEG_RIB_PEAK_OVERAGE = 0.60;
PEG_RIB_WIDTH = 0.85;
PEG_RIB_END_RELIEF = 0.75;

function peg_tip_diameter(diameter, chamfer) = max(0.8, diameter - 2 * chamfer);
function peg_core_diameter(diameter, rib_root_relief) =
    max(0.8, diameter - rib_root_relief);
function peg_rib_peak_diameter(diameter, rib_peak_overage) =
    diameter + rib_peak_overage;
function peg_rib_height(core_diameter, peak_diameter) =
    max(0, (peak_diameter - core_diameter) / 2);
function peg_rib_length(length, chamfer, rib_end_relief) =
    max(EPS, length - 2 * (chamfer + rib_end_relief));

module chamfered_peg_core(core_diameter, length, chamfer, core_sides) {
    tip_d = peg_tip_diameter(core_diameter, chamfer);

    union() {
        cylinder(d1=tip_d, d2=core_diameter, h=chamfer, $fn=core_sides);
        translate([0, 0, chamfer])
            cylinder(d=core_diameter, h=max(EPS, length - 2 * chamfer), $fn=core_sides);
        translate([0, 0, length - chamfer])
            cylinder(d1=core_diameter, d2=tip_d, h=chamfer, $fn=core_sides);
    }
}

module peg_crush_rib(core_diameter, peak_diameter, rib_width, rib_start, rib_length) {
    rib_h = peg_rib_height(core_diameter, peak_diameter);

    translate([core_diameter / 2 - EPS, -rib_width / 2, rib_start])
        cube([rib_h + EPS, rib_width, rib_length]);
}

module peg_crush_ribs(core_diameter, peak_diameter, rib_count, rib_width, rib_start, rib_length) {
    for (i = [0 : rib_count - 1])
        rotate([0, 0, i * 360 / rib_count])
            peg_crush_rib(
                core_diameter,
                peak_diameter,
                rib_width,
                rib_start,
                rib_length
            );
}

module hutchfinity_peg(
    diameter=PEG_DIAMETER,
    length=PEG_LENGTH,
    end_chamfer=PEG_END_CHAMFER,
    core_sides=PEG_CORE_SIDES,
    enable_crush_ribs=PEG_CRUSH_RIBS,
    rib_count=PEG_RIB_COUNT,
    rib_root_relief=PEG_RIB_ROOT_RELIEF,
    rib_peak_overage=PEG_RIB_PEAK_OVERAGE,
    rib_width=PEG_RIB_WIDTH,
    rib_end_relief=PEG_RIB_END_RELIEF
) {
    chamfer = min(end_chamfer, length / 2 - EPS);
    core_d = enable_crush_ribs ? peg_core_diameter(diameter, rib_root_relief) : diameter;
    peak_d = enable_crush_ribs ? peg_rib_peak_diameter(diameter, rib_peak_overage) : diameter;
    rib_start = chamfer + rib_end_relief;
    rib_len = peg_rib_length(length, chamfer, rib_end_relief);

    assert(diameter > 0 && length > 0, "peg diameter and length must be positive");
    assert(end_chamfer >= 0, "peg end chamfer must be non-negative");
    assert(core_sides >= 3, "peg core needs at least three sides");
    assert(!enable_crush_ribs || rib_count >= 3,
        "ribbed pegs need at least three ribs");
    assert(rib_root_relief >= 0 && rib_peak_overage >= 0,
        "rib root relief and peak overage must be non-negative");
    assert(rib_width > 0 && rib_end_relief >= 0,
        "rib width must be positive and rib end relief must be non-negative");
    assert(!enable_crush_ribs || core_d < peak_d,
        "ribbed peg core diameter must be smaller than rib peak diameter");
    assert(!enable_crush_ribs || rib_start < length / 2,
        "rib end relief plus chamfer leaves no ribbed shaft length");

    union() {
        chamfered_peg_core(core_d, length, chamfer, core_sides);
        if (enable_crush_ribs)
            peg_crush_ribs(core_d, peak_d, rib_count, rib_width, rib_start, rib_len);
    }
}

module hutchfinity_peg_print_layout(
    diameter=PEG_DIAMETER,
    length=PEG_LENGTH,
    end_chamfer=PEG_END_CHAMFER,
    core_sides=PEG_CORE_SIDES,
    print_face_rotation=PEG_PRINT_FACE_ROTATION,
    enable_crush_ribs=PEG_CRUSH_RIBS,
    rib_count=PEG_RIB_COUNT,
    rib_root_relief=PEG_RIB_ROOT_RELIEF,
    rib_peak_overage=PEG_RIB_PEAK_OVERAGE,
    rib_width=PEG_RIB_WIDTH,
    rib_end_relief=PEG_RIB_END_RELIEF
) {
    peak_d = enable_crush_ribs ?
        peg_rib_peak_diameter(diameter, rib_peak_overage) :
        diameter;

    translate([0, 0, peak_d / 2])
        rotate([0, 90, 0])
            rotate([0, 0, print_face_rotation])
                hutchfinity_peg(
                    diameter=diameter,
                    length=length,
                    end_chamfer=end_chamfer,
                    core_sides=core_sides,
                    enable_crush_ribs=enable_crush_ribs,
                    rib_count=rib_count,
                    rib_root_relief=rib_root_relief,
                    rib_peak_overage=rib_peak_overage,
                    rib_width=rib_width,
                    rib_end_relief=rib_end_relief
                );
}

hutchfinity_peg_print_layout();
