// peg.scad
// version: 0.4.0
// Prototype laid-down hex peg for vertical Hutchfinity casing stacks.

$fn = 64;
EPS = 0.01;

// Diameter is point-to-point across the hex. The default matches the current
// casing socket default: 8.0mm nominal peg + 0.45mm socket clearance.
PEG_DIAMETER = 8.45;
PEG_LENGTH = 20.0;
PEG_END_CHAMFER = 2.5;
PEG_CORE_SIDES = 6;
PEG_PRINT_FACE_ROTATION = 30;

function peg_tip_diameter(diameter, chamfer) = max(0.8, diameter - 2 * chamfer);
function peg_flat_to_flat_diameter(diameter, core_sides) =
    diameter * cos(180 / core_sides);

module chamfered_peg_core(diameter, length, chamfer, core_sides) {
    tip_d = peg_tip_diameter(diameter, chamfer);

    union() {
        cylinder(d1=tip_d, d2=diameter, h=chamfer, $fn=core_sides);
        translate([0, 0, chamfer])
            cylinder(d=diameter, h=max(EPS, length - 2 * chamfer), $fn=core_sides);
        translate([0, 0, length - chamfer])
            cylinder(d1=diameter, d2=tip_d, h=chamfer, $fn=core_sides);
    }
}

module hutchfinity_peg(
    diameter=PEG_DIAMETER,
    length=PEG_LENGTH,
    end_chamfer=PEG_END_CHAMFER,
    core_sides=PEG_CORE_SIDES
) {
    chamfer = min(end_chamfer, length / 2 - EPS);

    assert(diameter > 0 && length > 0, "peg diameter and length must be positive");
    assert(end_chamfer >= 0, "peg end chamfer must be non-negative");
    assert(core_sides >= 3, "peg core needs at least three sides");

    chamfered_peg_core(diameter, length, chamfer, core_sides);
}

module hutchfinity_peg_print_layout(
    diameter=PEG_DIAMETER,
    length=PEG_LENGTH,
    end_chamfer=PEG_END_CHAMFER,
    core_sides=PEG_CORE_SIDES,
    print_face_rotation=PEG_PRINT_FACE_ROTATION
) {
    translate([0, 0, peg_flat_to_flat_diameter(diameter, core_sides) / 2])
        rotate([0, 90, 0])
            rotate([0, 0, print_face_rotation])
                hutchfinity_peg(
                    diameter=diameter,
                    length=length,
                    end_chamfer=end_chamfer,
                    core_sides=core_sides
                );
}

hutchfinity_peg_print_layout();
