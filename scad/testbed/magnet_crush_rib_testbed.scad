// magnet_crush_rib_testbed.scad
// version: 1.3.0
//
// Flat plate with a 6×2 grid of crush-rib wells — one row per magnet size,
// one column per rib-protrusion level. Print in PETG, press-fit each magnet
// by hand, note which protrusion holds without cracking the well.
//
// Row 0 (front): 5×1 mm magnets   (well-Ø = MAGNETS[0][0]+2×WELL_R_ADD, well-depth = MAGNETS[0][1]+WELL_D_ADD)
// Row 1 (back):  6×1.5 mm magnets (well-Ø = MAGNETS[1][0]+2×WELL_R_ADD, well-depth = MAGNETS[1][1]+WELL_D_ADD)
// Columns 0–5:   rib protrusion ∈ {0.05, 0.10, 0.15, 0.20, 0.25, 0.30} mm
//
// Crush-rib geometry: 8 axial ribs at 45° spacing, parallel to build-Z.
// 8 ribs is the experimentally validated count for FDM disc-magnet wells:
// ≤5 produces a polygon bore, 30 won't print at 0.4mm nozzle (gridfinity-rebuilt-openscad).
// Each rib is a wedge of plate material retained inside the bore — the bore
// subtraction has rib-shaped notches, so PETG material protrudes inward.
// Rib base width (at bore wall): RIB_WIDTH. Apex depth into bore: protrusion.
// Lead-in chamfer on well opening aids magnet centering before interference.
//
// Labels on top face show protrusion × 100 as integer (e.g. "10" = 0.10 mm).
// Row labels show magnet spec ("5x1", "6x1.5").

// ── Parameters ───────────────────────────────────────────────────────────────

PROTRUSIONS  = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]; // rib radial protrusion, mm
// NOTE: col 0 protrusion (0.05) == WELL_R_ADD (0.05) → zero net engagement; it's a baseline, not a low-friction test.
MAGNETS      = [[5.0, 1.0], [6.0, 1.5]];             // [OD mm, H mm] per row

WELL_R_ADD   = 0.05;  // added per side to magnet OD → well nominal radius = OD/2 + 0.05
WELL_D_ADD   = 0.10;  // added to magnet H → well depth
RIB_WIDTH    = 0.8;   // rib base chord width at bore wall (fixed for all protrusions)
RIB_COUNT    = 8;     // 8 = FDM-validated for disc magnets; ≤5 → polygon bore, 30 → unprintable at 0.4mm
CHAMFER_R    = 0.3;   // lead-in chamfer radius at well opening; small — don't eat rib engagement depth

PLATE_H      = 5.0;   // plate thickness
WELL_SPACING = 14.0;  // well centre-to-centre (X and Y)
MARGIN_X     = 9.0;   // edge → first/last well centre (X)
MARGIN_Y     = 9.0;   // edge → first/last well centre (Y)

LABEL_DEPTH  = 0.5;   // emboss depth
LABEL_SIZE   = 2.2;
ROW_LBL_SIZE = 1.8;

$fn = 36;  // testbed — 36 is sufficient for bore circles, halves render time vs 72

// ── Derived ──────────────────────────────────────────────────────────────────

COLS   = len(PROTRUSIONS);
ROWS   = len(MAGNETS);
PLATE_X = 2*MARGIN_X + (COLS-1)*WELL_SPACING;
PLATE_Y = 2*MARGIN_Y + (ROWS-1)*WELL_SPACING;

function well_r(row) = MAGNETS[row][0]/2 + WELL_R_ADD;
function well_d(row) = MAGNETS[row][1]   + WELL_D_ADD;
function cx(col)     = MARGIN_X + col*WELL_SPACING;
function cy(row)     = MARGIN_Y + row*WELL_SPACING;

// CHAMFER_R must be strictly less than every well depth — violated → negative linear_extrude height.
assert(CHAMFER_R < min([for (r=[0:len(MAGNETS)-1]) well_d(r)]),
       "CHAMFER_R must be < min(well_d): increase WELL_D_ADD or reduce CHAMFER_R");

// ── Modules ───────────────────────────────────────────────────────────────────

// Bore shape to subtract from the plate for one well.
// = cylinder (+ chamfer cone) with 8 rib-shaped notches removed → rib material stays in plate.
module bore_with_ribs(row, protrusion) {
    r = well_r(row);
    d = well_d(row);
    // Lead-in chamfer: 45° cone at the opening, removes a ring of material
    // so the magnet self-centers before hitting the ribs.
    translate([0, 0, d - CHAMFER_R])
        cylinder(r1=r, r2=r + CHAMFER_R, h=CHAMFER_R + 0.01);

    difference() {
        cylinder(r=r, h=d+0.01);
        for (i=[0:RIB_COUNT-1]) {
            rotate([0,0, i*(360/RIB_COUNT)])
            // Rib notch capped at d - CHAMFER_R so ribs don't enter the chamfer zone.
            linear_extrude(height=d - CHAMFER_R + 0.01)
            polygon([
                [ r - protrusion, 0          ],  // apex (inward)
                [ r,             -RIB_WIDTH/2 ], // wall left
                [ r,              RIB_WIDTH/2 ], // wall right
            ]);
        }
    }
}

// Embossed column label on top face, centred above the well.
// Shows protrusion × 100 as integer ("5", "10", …, "30").
module col_label(col, row) {
    lbl = str(round(PROTRUSIONS[col] * 100));
    // place label below well centre (toward front of plate)
    y_off = well_r(row) + 1.0;
    translate([cx(col), cy(row) - y_off, PLATE_H - LABEL_DEPTH])
    linear_extrude(height=LABEL_DEPTH + 0.01)
    text(lbl, size=LABEL_SIZE,
         font="Liberation Mono:style=Bold",
         halign="center", valign="top");
}

// Row label on the left margin showing magnet spec.
module row_label(row) {
    mag = MAGNETS[row];
    // "5x1" or "6x1.5" — avoid str(1.5) rendering as "1.5" vs "1.50" edge case
    lbl = str(mag[0], "x", mag[1]);
    // right-align against the bore left edge with 0.5mm gap; accounts for wider row-1 bore
    x_off = cx(0) - well_r(row) - 0.5;
    translate([x_off, cy(row), PLATE_H - LABEL_DEPTH])
    linear_extrude(height=LABEL_DEPTH + 0.01)
    text(lbl, size=ROW_LBL_SIZE,
         font="Liberation Mono:style=Bold",
         halign="right", valign="center");
}

// ── Assembly ──────────────────────────────────────────────────────────────────

difference() {
    cube([PLATE_X, PLATE_Y, PLATE_H]);

    // Wells (bore + retained ribs)
    for (row=[0:ROWS-1]) {
        for (col=[0:COLS-1]) {
            z0 = PLATE_H - well_d(row);
            translate([cx(col), cy(row), z0])
                bore_with_ribs(row, PROTRUSIONS[col]);
        }
    }

    // Column labels (one per cell — embossed on top)
    for (col=[0:COLS-1]) {
        for (row=[0:ROWS-1]) {
            col_label(col, row);
        }
    }

    // Row labels (magnet spec, left margin)
    for (row=[0:ROWS-1]) {
        row_label(row);
    }
}
