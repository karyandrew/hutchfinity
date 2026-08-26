// basket_carrier_comparison.scad
// version: 0.1.0
// Reproducible Mini-size geometry comparisons for issue #26.

use <../tub.scad>;
use <basket_carrier_probe.scad>;

COMPARISON_PART = "candidate";
CURRENT_MAGNETS = false;
CANDIDATE_MAGNETS = false;
COMPARE_FLOOR_MODE = "plain";

MINI_BASEPLATE_STL = "../gridfinity/stl/baseplate-mini.stl";
OVERLAP_WITNESS_OFFSET = [0, 0, -2];
MATCHED_WALL_THICKNESS = 2.2;
MATCHED_STANDOFF = 1.75;
MATCHED_XY_TOLERANCE = 0.5;
MATCHED_Z_TOLERANCE = 0.25;
MINI_OUTER_X = 130.4;
MINI_OUTER_Y = 340.4;
MINI_OUTER_Z = 84.24;
SIDE_CLEARANCE = 1.0;
BACK_CLEARANCE = 0.5;
TOP_CLEARANCE = 1.0;
COMPARISON_EPS = 0.01;
REMOVABLE_GRID_CONTACT_LIFT = 0.01;
CENTER_FLOOR_PROBE_XY = 1.0;

module current_mini() {
    hutchfinity_mini_tub(enable_magnet_holes = CURRENT_MAGNETS);
}

module candidate_mini(
    floor_mode = COMPARE_FLOOR_MODE,
    enable_magnet_holes = CANDIDATE_MAGNETS
) {
    hutchfinity_basket_carrier_probe(
        floor_mode = floor_mode,
        enable_magnet_holes = enable_magnet_holes
    );
}

module candidate_current_intersection() {
    intersection() {
        current_mini();
        candidate_mini();
    }
}

module current_only() {
    difference() {
        current_mini();
        candidate_mini();
    }
}

module candidate_only() {
    difference() {
        candidate_mini();
        current_mini();
    }
}

module center_floor_probe() {
    translate([
        -CENTER_FLOOR_PROBE_XY / 2,
        -CENTER_FLOOR_PROBE_XY / 2,
        0
    ])
        cube([
            CENTER_FLOOR_PROBE_XY,
            CENTER_FLOOR_PROBE_XY,
            MINI_OUTER_Z
        ]);
}

module current_center_floor_probe() {
    intersection() {
        current_mini();
        center_floor_probe();
    }
}

module candidate_center_floor_probe() {
    intersection() {
        candidate_mini(
            floor_mode = "plain",
            enable_magnet_holes = false
        );
        center_floor_probe();
    }
}

module overlap_witness() {
    translate(OVERLAP_WITNESS_OFFSET)
        cube([1, 1, 1]);
}

module self_stack_overlap_witness() {
    overlap_witness();
    hutchfinity_basket_carrier_self_stack_intersection(
        floor_mode = COMPARE_FLOOR_MODE
    );
}

module removable_grid_interference(z_lift = 0) {
    floor_z = basket_carrier_plain_floor_z(
        MATCHED_WALL_THICKNESS,
        MATCHED_STANDOFF,
        MATCHED_XY_TOLERANCE,
        MATCHED_Z_TOLERANCE
    );

    intersection() {
        candidate_mini(
            floor_mode = "removable",
            enable_magnet_holes = false
        );
        translate([0, 0, floor_z + z_lift])
            import(MINI_BASEPLATE_STL);
    }
}

module removable_grid_interference_witness() {
    overlap_witness();
    removable_grid_interference();
}

module removable_grid_side_interference_witness() {
    overlap_witness();
    removable_grid_interference(REMOVABLE_GRID_CONTACT_LIFT);
}

module removable_grid_assembly() {
    floor_z = basket_carrier_plain_floor_z(
        MATCHED_WALL_THICKNESS,
        MATCHED_STANDOFF,
        MATCHED_XY_TOLERANCE,
        MATCHED_Z_TOLERANCE
    );

    candidate_mini(
        floor_mode = "removable",
        enable_magnet_holes = false
    );
    translate([0, 0, floor_z])
        import(MINI_BASEPLATE_STL);
}

module casing_slot_overflow_witness() {
    slot_width = MINI_OUTER_X + 2 * SIDE_CLEARANCE;
    slot_depth = MINI_OUTER_Y + BACK_CLEARANCE;
    slot_height = MINI_OUTER_Z + TOP_CLEARANCE;

    overlap_witness();
    difference() {
        candidate_mini(
            floor_mode = "plain",
            enable_magnet_holes = false
        );
        translate([0, BACK_CLEARANCE / 2, slot_height / 2])
            cube([
                slot_width + 2 * COMPARISON_EPS,
                slot_depth + 2 * COMPARISON_EPS,
                slot_height + 2 * COMPARISON_EPS
            ], center = true);
    }
}

assert(
    COMPARISON_PART == "candidate" ||
    COMPARISON_PART == "current" ||
    COMPARISON_PART == "intersection" ||
    COMPARISON_PART == "current-only" ||
    COMPARISON_PART == "candidate-only" ||
    COMPARISON_PART == "current-center-floor-probe" ||
    COMPARISON_PART == "candidate-center-floor-probe" ||
    COMPARISON_PART == "self-stack-overlap-witness" ||
    COMPARISON_PART == "removable-grid-interference" ||
    COMPARISON_PART == "removable-grid-interference-witness" ||
    COMPARISON_PART == "removable-grid-side-interference-witness" ||
    COMPARISON_PART == "casing-slot-overflow-witness" ||
    COMPARISON_PART == "removable-grid-assembly",
    str("unknown COMPARISON_PART: ", COMPARISON_PART)
);

if (COMPARISON_PART == "candidate") {
    candidate_mini();
} else if (COMPARISON_PART == "current") {
    current_mini();
} else if (COMPARISON_PART == "intersection") {
    candidate_current_intersection();
} else if (COMPARISON_PART == "current-only") {
    current_only();
} else if (COMPARISON_PART == "candidate-only") {
    candidate_only();
} else if (COMPARISON_PART == "current-center-floor-probe") {
    current_center_floor_probe();
} else if (COMPARISON_PART == "candidate-center-floor-probe") {
    candidate_center_floor_probe();
} else if (COMPARISON_PART == "self-stack-overlap-witness") {
    self_stack_overlap_witness();
} else if (COMPARISON_PART == "removable-grid-interference") {
    removable_grid_interference();
} else if (COMPARISON_PART == "removable-grid-interference-witness") {
    removable_grid_interference_witness();
} else if (COMPARISON_PART == "removable-grid-side-interference-witness") {
    removable_grid_side_interference_witness();
} else if (COMPARISON_PART == "casing-slot-overflow-witness") {
    casing_slot_overflow_witness();
} else if (COMPARISON_PART == "removable-grid-assembly") {
    removable_grid_assembly();
}
