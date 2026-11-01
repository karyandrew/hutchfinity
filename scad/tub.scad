// tub.scad
// version: 1.1.0
// Parametric Hutchfinity drawer tub: thin floor, integral or removable grid.
//
// Heights are derived from the tallest bin the tub must hold, not from a fixed
// tub unit:
//   body_top = floor + bin_h * 3.5 + BIN_LIP + STACK_GAP
//   total    = body_top + STACK_OVERLAP
// body_top is where the next tub's underside seats. STACK_GAP is the real air gap
// above the tallest bin's lip when tubs are stacked.

PITCH = 21.0;
PITCH_Z = 3.5;
WALL = 2.2;
MIN_WALL = 0.4;
TOP_SLOPE = WALL - MIN_WALL;
BIN_LIP = 3.74;
STACK_GAP = 0.5;

FOOT_VERTICAL_Z = 2.0;
XY_TOLERANCE = 0.5;
FOOT_INSET = WALL + XY_TOLERANCE;
FOOT_TOP_Z = FOOT_VERTICAL_Z + FOOT_INSET;
// Foot/rim contact between stacked tubs (equal 45-degree profiles).
STACK_OVERLAP = FOOT_VERTICAL_Z + XY_TOLERANCE + TOP_SLOPE;

OUTER_RADIUS = 4.0 + WALL;
INNER_RADIUS = 4.0;
INTEGRAL_FLOOR = 1.30;
PLAIN_FLOOR = 1.20;
GRID_Z = 5.0;
INSERT_CLEARANCE = 1.0;
EDGE_CHANNEL_OVERLAP = 0.12;
EDGE_CHANNEL_MARGIN = 2.0;
CORNER_SLIVER = 2.4;

// Receiving recess for one 21 mm cell: [z, width, corner radius].
CELL_PROFILE = [
    [0.00, 15.30, 1.15],
    [0.35, 15.30, 1.15],
    [1.05, 16.70, 1.85],
    [2.85, 16.70, 1.85],
    [5.00, 20.98, 3.99],
];

PULL_FLANGE_X = 90.0;
PULL_FLANGE_Z = 32.9; // Largest that fits a 10h tub's wall band, so one pull serves 10h and up.
PULL_FLANGE_RADIUS = 5.0;
GUIDE_CLEARANCE = 0.5;
GUIDE_RING = 1.4;
GUIDE_PROJECTION = 0.6;
GUIDE_OVERLAP = 0.08;

EPS = 0.01;
// Facets per 90-degree corner. These keep chord error under about 0.04 mm,
// well below what a 0.4 mm nozzle resolves; more only inflates the file.
CORNER_STEPS = 8;
CELL_CORNER_STEPS = 6;

function tub_outer_x(cells_x) = cells_x * PITCH + 2 * WALL;
function tub_outer_y(cells_y) = cells_y * PITCH + 2 * WALL;
function tub_floor(floor_mode) = floor_mode == "plain" ? PLAIN_FLOOR : INTEGRAL_FLOOR;
function tub_body_top(bin_h, floor_mode) =
    tub_floor(floor_mode) + bin_h * PITCH_Z + BIN_LIP + STACK_GAP;
function tub_total_z(bin_h, floor_mode) = tub_body_top(bin_h, floor_mode) + STACK_OVERLAP;

// Wall band above the grid and below the rim slope: the only place a pull can sit.
function tub_wall_band_bottom(floor_mode) = tub_floor(floor_mode) + GRID_Z;
function tub_wall_band(bin_h, floor_mode) =
    tub_total_z(bin_h, floor_mode) - TOP_SLOPE - tub_wall_band_bottom(floor_mode);

// One pull design, scaled uniformly: full size wherever it fits, smaller on smaller tubs.
function pull_scale_factor(cells_x, bin_h, floor_mode) =
    let (margin = 2 * (GUIDE_CLEARANCE + GUIDE_RING))
    max(0, min(
        1,
        (tub_wall_band(bin_h, floor_mode) - margin) / PULL_FLANGE_Z,
        (cells_x * PITCH - 2 * INNER_RADIUS - margin) / PULL_FLANGE_X
    ));
function pull_flange(cells_x, bin_h, floor_mode) =
    let (k = pull_scale_factor(cells_x, bin_h, floor_mode))
    [k * PULL_FLANGE_X, k * PULL_FLANGE_Z];

function _corner(cx, cy, r, a0, n) =
    [for (i = [0:n]) let (a = a0 + 90 * i / n) [cx + r * cos(a), cy + r * sin(a)]];

// Counterclockwise rounded rectangle with a fixed point count, so that any two
// profiles can be lofted vertex to vertex.
function rounded_rect_points(w, d, r, n) = concat(
    _corner(w / 2 - r, d / 2 - r, r, 0, n),
    _corner(-w / 2 + r, d / 2 - r, r, 90, n),
    _corner(-w / 2 + r, -d / 2 + r, r, 180, n),
    _corner(w / 2 - r, -d / 2 + r, r, 270, n)
);

// Ruled loft through [[z, w, d, r], ...] in ascending z.
module rounded_loft(profiles, n = CORNER_STEPS) {
    m = 4 * (n + 1);
    layers = len(profiles);
    points = [
        for (p = profiles)
            for (q = rounded_rect_points(p[1], p[2], p[3], n))
                [q.x, q.y, p[0]]
    ];
    bottom = [for (i = [0:m - 1]) i];
    top = [for (i = [m - 1:-1:0]) (layers - 1) * m + i];
    sides = [
        for (k = [0:layers - 2])
            for (i = [0:m - 1])
                let (
                    j = (i + 1) % m,
                    a = k * m + i,
                    b = k * m + j,
                    c = (k + 1) * m + j,
                    d = (k + 1) * m + i
                )
                each [[a, d, c], [a, c, b]]
    ];
    polyhedron(points, concat([bottom], sides, [top]), convexity = 4);
}

function _outer_profile_at(z, ox, oy) =
    let (fx = ox - 2 * FOOT_INSET, fy = oy - 2 * FOOT_INSET, fr = OUTER_RADIUS - FOOT_INSET)
    z <= FOOT_VERTICAL_Z ? [fx, fy, fr]
    : z < FOOT_TOP_Z
        ? let (t = (z - FOOT_VERTICAL_Z) / (FOOT_TOP_Z - FOOT_VERTICAL_Z))
            [fx + (ox - fx) * t, fy + (oy - fy) * t, fr + (OUTER_RADIUS - fr) * t]
        : [ox, oy, OUTER_RADIUS];

function _inner_profile_at(z, ox, oy) =
    let (p = _outer_profile_at(z, ox, oy))
    [p[0] - 2 * WALL, p[1] - 2 * WALL, max(p[2] - WALL, 0.05)];

function _with_z(z, p) = [z, p[0], p[1], p[2]];

module _tub_envelope(ox, oy, total_z) {
    rounded_loft([
        _with_z(0, _outer_profile_at(0, ox, oy)),
        _with_z(FOOT_VERTICAL_Z, _outer_profile_at(FOOT_VERTICAL_Z, ox, oy)),
        _with_z(FOOT_TOP_Z, _outer_profile_at(FOOT_TOP_Z, ox, oy)),
        _with_z(total_z, _outer_profile_at(FOOT_TOP_Z, ox, oy)),
    ]);
}

module _tub_cavity(ox, oy, floor_top, total_z) {
    rim = [ox - 2 * MIN_WALL, oy - 2 * MIN_WALL, OUTER_RADIUS - MIN_WALL];
    rounded_loft([
        _with_z(floor_top, _inner_profile_at(floor_top, ox, oy)),
        _with_z(FOOT_VERTICAL_Z, _inner_profile_at(FOOT_VERTICAL_Z, ox, oy)),
        _with_z(FOOT_TOP_Z, _inner_profile_at(FOOT_TOP_Z, ox, oy)),
        [total_z - TOP_SLOPE, ox - 2 * WALL, oy - 2 * WALL, INNER_RADIUS],
        _with_z(total_z, rim),
        _with_z(total_z + 0.1, rim),
    ]);
}

module _cell_cutter() {
    top = CELL_PROFILE[len(CELL_PROFILE) - 1];
    rounded_loft(concat(
        [for (p = CELL_PROFILE) [p[0], p[1], p[1], p[2]]],
        [[top[0] + 0.03, top[1], top[1], top[2]]]
    ), CELL_CORNER_STEPS);
}

module _cell_cutters(cells_x, cells_y, z0) {
    for (ix = [0:cells_x - 1], iy = [0:cells_y - 1])
        translate([
            (ix - (cells_x - 1) / 2) * PITCH,
            (iy - (cells_y - 1) / 2) * PITCH,
            z0
        ])
            _cell_cutter();
}

module _pull_guide(cells_y, flange, band_bottom, total_z) {
    ix = flange[0] + 2 * GUIDE_CLEARANCE;
    iz = flange[1] + 2 * GUIDE_CLEARANCE;
    inner_r = PULL_FLANGE_RADIUS * flange[0] / PULL_FLANGE_X + GUIDE_CLEARANCE;
    center_z = (band_bottom + total_z - TOP_SLOPE) / 2;
    translate([0, -tub_outer_y(cells_y) / 2 + GUIDE_OVERLAP, center_z])
        rotate([90, 0, 0])
            linear_extrude(GUIDE_PROJECTION + GUIDE_OVERLAP)
                difference() {
                    polygon(rounded_rect_points(
                        ix + 2 * GUIDE_RING, iz + 2 * GUIDE_RING, inner_r + GUIDE_RING, CORNER_STEPS));
                    polygon(rounded_rect_points(ix, iz, inner_r, CORNER_STEPS));
                }
}

// floor_mode: "integral-grid" has the grid built in; "plain" is a flat floor that
// takes bins directly or a removable grid insert.
module hutchfinity_tub(cells_x, cells_y, bin_h, floor_mode = "integral-grid", pull_guide = true) {
    assert(floor_mode == "integral-grid" || floor_mode == "plain", "unknown floor_mode");
    assert(cells_x >= 1 && cells_y >= 1 && bin_h >= 1, "tub size must be at least 1 x 1 x 1h");

    ox = tub_outer_x(cells_x);
    oy = tub_outer_y(cells_y);
    floor_top = tub_floor(floor_mode);
    total_z = tub_total_z(bin_h, floor_mode);
    flange = pull_flange(cells_x, bin_h, floor_mode);

    echo(str("tub ", cells_x, "x", cells_y, "x", bin_h, "h ", floor_mode,
        ": ", ox, " x ", oy, " x ", total_z, " mm; pull flange ", flange[0], " x ", flange[1], " mm"));

    difference() {
        _tub_envelope(ox, oy, total_z);
        _tub_cavity(ox, oy, floor_top, total_z);
    }
    if (floor_mode == "integral-grid")
        difference() {
            intersection() {
                _tub_envelope(ox, oy, total_z);
                rounded_loft([
                    [floor_top - EPS, cells_x * PITCH + 0.02, cells_y * PITCH + 0.02, INNER_RADIUS + 0.01],
                    [floor_top + GRID_Z, cells_x * PITCH + 0.02, cells_y * PITCH + 0.02, INNER_RADIUS + 0.01],
                ]);
            }
            _cell_cutters(cells_x, cells_y, floor_top);
        }
    if (pull_guide && flange[0] > 0)
        _pull_guide(cells_y, flange, tub_wall_band_bottom(floor_mode), total_z);
}

function _insert_profile_at(local_z, ox, oy) =
    let (p = _inner_profile_at(PLAIN_FLOOR + local_z, ox, oy))
    [p[0] - 2 * INSERT_CLEARANCE, p[1] - 2 * INSERT_CLEARANCE, max(p[2] - INSERT_CLEARANCE, 0.05)];

// One edge pocket's opening, extended out through the sloped insert boundary.
// axis 0 runs along X (left/right edges); axis 1 along Y (front/back edges).
module _edge_channel(axis, side, tangent, cells_x, cells_y, ox, oy) {
    edge_center = side * ((axis == 0 ? cells_x : cells_y) * PITCH / 2 - PITCH / 2);
    profiles = [
        for (p = CELL_PROFILE)
            let (
                e = _insert_profile_at(p[0], ox, oy),
                half = (axis == 0 ? e[0] : e[1]) / 2,
                inner = edge_center + side * (p[1] / 2 - EDGE_CHANNEL_OVERLAP),
                outer = side * (half + EDGE_CHANNEL_MARGIN)
            )
            [p[0], min(inner, outer), max(inner, outer), p[1]]
    ];
    // Each layer is one rectangle listed counterclockwise from above.
    function corners(p) = axis == 0
        ? [[p[2], tangent + p[3] / 2], [p[1], tangent + p[3] / 2], [p[1], tangent - p[3] / 2], [p[2], tangent - p[3] / 2]]
        : [[tangent + p[3] / 2, p[2]], [tangent - p[3] / 2, p[2]], [tangent - p[3] / 2, p[1]], [tangent + p[3] / 2, p[1]]];
    m = 4;
    layers = len(profiles);
    points = [for (p = profiles) for (q = corners(p)) [q.x, q.y, p[0]]];
    sides = [
        for (k = [0:layers - 2], i = [0:m - 1])
            let (j = (i + 1) % m, a = k * m + i, b = k * m + j, c = (k + 1) * m + j, d = (k + 1) * m + i)
            each [[a, d, c], [a, c, b]]
    ];
    polyhedron(points, concat([[0, 1, 2, 3]], sides, [[for (i = [3:-1:0]) (layers - 1) * m + i]]));
}

// Open-bottom grid that drops into a "plain" tub. Pockets open through to the tub
// floor; edge pockets open sideways so the perimeter has no unsupported span.
module hutchfinity_grid_insert(cells_x, cells_y) {
    assert(cells_x >= 2 && cells_y >= 2, "a grid insert needs at least 2 x 2 cells");
    ox = tub_outer_x(cells_x);
    oy = tub_outer_y(cells_y);
    events = [0, FOOT_VERTICAL_Z - PLAIN_FLOOR, FOOT_TOP_Z - PLAIN_FLOOR, GRID_Z];

    difference() {
        rounded_loft([for (z = events) _with_z(z, _insert_profile_at(z, ox, oy))]);
        _cell_cutters(cells_x, cells_y, -EPS);
        for (iy = [0:cells_y - 1], side = [-1, 1])
            _edge_channel(0, side, (iy - (cells_y - 1) / 2) * PITCH, cells_x, cells_y, ox, oy);
        for (ix = [0:cells_x - 1], side = [-1, 1])
            _edge_channel(1, side, (ix - (cells_x - 1) / 2) * PITCH, cells_x, cells_y, ox, oy);
        // The two channels meeting at a corner leave a loose sliver of grid; remove it.
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (ox / 2 - WALL - INSERT_CLEARANCE), sy * (oy / 2 - WALL - INSERT_CLEARANCE), GRID_Z / 2])
                cube([2 * CORNER_SLIVER, 2 * CORNER_SLIVER, GRID_Z + 1], center = true);
    }
}

// The three standard chest widths, all 16 cells deep and holding 20h bins.
module hutchfinity_mini_tub() { hutchfinity_tub(6, 16, 20); }
module hutchfinity_regular_tub() { hutchfinity_tub(12, 16, 20); }
module hutchfinity_mega_tub() { hutchfinity_tub(18, 16, 20); }
