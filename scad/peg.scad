// peg.scad
// version: 0.1.0
// Prototype press-fit dowel for vertical Hutchfinity casing stacks.

$fn = 64;
EPS = 0.01;

PEG_DIAMETER = 8.0;
PEG_LENGTH = 20.0;
PEG_END_CHAMFER = 2.5;

function peg_tip_diameter(diameter, chamfer) = max(0.8, diameter - 2 * chamfer);

module hutchfinity_peg(
    diameter=PEG_DIAMETER,
    length=PEG_LENGTH,
    end_chamfer=PEG_END_CHAMFER
) {
    chamfer = min(end_chamfer, length / 2 - EPS);
    tip_d = peg_tip_diameter(diameter, chamfer);

    assert(diameter > 0 && length > 0, "peg diameter and length must be positive");
    assert(end_chamfer >= 0, "peg end chamfer must be non-negative");

    union() {
        cylinder(d1=tip_d, d2=diameter, h=chamfer);
        translate([0, 0, chamfer]) cylinder(d=diameter, h=max(EPS, length - 2 * chamfer));
        translate([0, 0, length - chamfer]) cylinder(d1=diameter, d2=tip_d, h=chamfer);
    }
}

hutchfinity_peg();
