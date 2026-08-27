#!/usr/bin/env bash
# Renders dental gridfinity STLs from the vendor libs.
# Per PRD v4.0.0: vendor lib invoked directly via -D global overrides;
# project-level constants in TUB_FLAGS / BASEPLATE_FLAGS / BIN_FLAGS,
# SKU-level params (pitch X, Width, bin W×D×H) inline.
#
# Usage: ./build-stl.sh
# Outputs to ../stl/

set -euo pipefail
cd "$(dirname "$0")/.."

CUP=vendor/extended/gridfinity_basic_cup.scad
BASE=vendor/extended/gridfinity_baseplate.scad
OUT=stl
OPENSCAD_BIN="${OPENSCAD_BIN:-openscad}"

OPENSCAD_CMD=("$OPENSCAD_BIN")
if [[ -n "${OPENSCAD_ARCH:-}" ]]; then
  OPENSCAD_CMD=(arch "$OPENSCAD_ARCH" "$OPENSCAD_BIN")
elif ! "$OPENSCAD_BIN" --version >/dev/null 2>&1; then
  if [[ "$(uname -s)" == "Darwin" ]] &&
     command -v arch >/dev/null 2>&1 &&
     arch -x86_64 "$OPENSCAD_BIN" --version >/dev/null 2>&1; then
    OPENSCAD_CMD=(arch -x86_64 "$OPENSCAD_BIN")
  else
    echo "OpenSCAD launcher failed: $OPENSCAD_BIN" >&2
    "$OPENSCAD_BIN" --version >&2 || true
    exit 1
  fi
fi

run_openscad() {
  "${OPENSCAD_CMD[@]}" "$@"
}

# Project-level tub constants (PRD v4.0.0 — fit math + tolerances).
# pitch_xy formula: N × 21 + 2W + C = N×21 + 4.4 + 0.5 = N×21 + 4.9
# Each cup is 1×1 cells of custom pitch; walls live outside the cell grid (HR-12).
# wall_thickness=2.2 fixes the printed tub strength/stacking improvement previously
# achieved with +0.6mm slicer contour compensation, while keeping that compensation
# out of the casing model.
# height=23h (=80.5mm body): at half-pitch (3.5mm/h), the bin's foot bottom rests at
# tub interior cavity floor (Z=4.75) since the baseplate pocket is open through (4mm).
# Bin lip top = 4.75 + N_bin*3.5 + 3.74. For tub-on-tub stacking the upper tub's
# external bottom sits at lower body top (= N_tub*3.5), so for non-intersection the
# bin lip must not exceed lower body top → N_bin ≤ N_tub - 2.43, i.e. N_bin ≤ N_tub-3.
# 23h tub holds 20h max bin with 2.01mm clearance below the upper tub bottom. See #146.
TUB_FLAGS=(
  -D 'height=[23,0]'
  -D 'width=[1,0]'
  -D 'depth=[1,0]'
  -D 'wall_thickness=2.2'
  -D 'floor_thickness=1.2'
  -D 'lip_style="minimum"'
  -D 'flat_base="gridfinity"'
  -D 'vertical_chambers=1'
  -D 'horizontal_chambers=1'
  -D 'enable_magnets=false'
  -D 'enable_screws=false'
)

# Project-level baseplate constants. Standard 21mm Gridfinity pitch.
# Library default clearance yields exterior = N × 21 (per PRD v3.1.0 fix).
BASEPLATE_FLAGS=(
  -D 'pitch=[21,21,3.5]'
  -D 'Depth=[16,0]'
)

# Project-level bin constants. Half-pitch (21mm XY, 3.5mm Z) per PRD §"What you're building".
# HR-13: no magnets, no screws, no label holders, no scoops (fingerslide). Library
# defaults already match; set explicit here so the rule is visible at the build site.
# flat_base left at library default "off" — bins get N×M individual feet at 21mm pitch
# to mate with baseplate pockets. (Tubs use flat_base="gridfinity" because they stack
# tub-on-tub via lip; bins sit in baseplate pockets.)
# lip_style="minimum" matches the dental tub aesthetic and keeps inner reach unobstructed.
BIN_FLAGS=(
  -D 'pitch=[21,21,3.5]'
  -D 'lip_style="minimum"'
  -D 'enable_magnets=false'
  -D 'enable_screws=false'
  -D 'label_style="disabled"'
  -D 'fingerslide="none"'
  -D 'vertical_chambers=1'
  -D 'horizontal_chambers=1'
)

# Tubs: name | cells X (mini=6, regular=12, mega=18) → pitch X = N×21 + 4.9
run_openscad "${TUB_FLAGS[@]}" -D 'pitch=[130.9,340.9,3.5]' -o "$OUT/tub-mini.stl"    "$CUP"
run_openscad "${TUB_FLAGS[@]}" -D 'pitch=[256.9,340.9,3.5]' -o "$OUT/tub-regular.stl" "$CUP"
run_openscad "${TUB_FLAGS[@]}" -D 'pitch=[382.9,340.9,3.5]' -o "$OUT/tub-mega.stl"    "$CUP"

# Baseplates: name | Width (mini bumped 5→6 to match new mini tub cavity)
run_openscad "${BASEPLATE_FLAGS[@]}" -D 'Width=[6,0]'  -o "$OUT/baseplate-mini.stl"    "$BASE"
run_openscad "${BASEPLATE_FLAGS[@]}" -D 'Width=[12,0]' -o "$OUT/baseplate-regular.stl" "$BASE"
run_openscad "${BASEPLATE_FLAGS[@]}" -D 'Width=[18,0]' -o "$OUT/baseplate-mega.stl"    "$BASE"

# Bins: name | width × depth × height (in cells; half-pitch units → 21mm XY, 3.5mm Z)
# Footprints: 1×1, 2×1, 2×2 (baseline) + 2×9, 3×3, 2×4, 2×5, 5×9, 3×5, 6×2 (inventory, #272/#275).
# Heights: 5h (17.5mm), 10h (35mm), 20h (70mm).
# Stack-fit invariant: bin lip top ≤ lower tub body top → N_bin ≤ N_tub - 3 at half-pitch.
# 23h tub holds 20h max bin with 2.01mm clearance below upper tub bottom when stacked.
# Bins rotate freely on the square 21mm foot grid → W×D is a label, not a placement
# constraint; the long axis seats along whichever tub axis has ≥ cells (all tubs 16-deep).
run_openscad "${BIN_FLAGS[@]}" -D 'width=[1,0]' -D 'depth=[1,0]' -D 'height=[5,0]'  -o "$OUT/bin-1x1x5h.stl"  "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[1,0]' -D 'height=[5,0]'  -o "$OUT/bin-2x1x5h.stl"  "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[2,0]' -D 'height=[5,0]'  -o "$OUT/bin-2x2x5h.stl"  "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[1,0]' -D 'depth=[1,0]' -D 'height=[10,0]' -o "$OUT/bin-1x1x10h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[1,0]' -D 'height=[10,0]' -o "$OUT/bin-2x1x10h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[2,0]' -D 'height=[10,0]' -o "$OUT/bin-2x2x10h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[1,0]' -D 'depth=[1,0]' -D 'height=[20,0]' -o "$OUT/bin-1x1x20h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[1,0]' -D 'height=[20,0]' -o "$OUT/bin-2x1x20h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[2,0]' -D 'height=[20,0]' -o "$OUT/bin-2x2x20h.stl" "$CUP"

# Inventory-driven SKUs (#272/#275). X2D / PETG. flat_base library default "off".
# SKU names are GEOMETRY (W×D×H cells), item-agnostic. The item→SKU map lives in the
# kary-dental inventory guide, NOT here — notes below are sizing rationale only, the
# parenthetical item is the example that motivated the size, not a binding/name.
# Measured interior on a long axis of N cells ≈ N×21 − 2.6mm
#   (effective wall ~1.05mm/side incl. minimum lip; verified against all SKUs below).
#   2×9×10h  interior ~186.4mm           (≤186mm item; e.g. 7"/177.8mm suction tip)
#   3×3×10h  interior ~60.4mm sq          (≤60mm square; e.g. 49mm 2×2 gauze stack)
#   2×4×10h  interior ~81.4mm            (≥80mm-internal class; e.g. 40mm cotton roll)
#   2×5×10h  interior ~102.4mm           (roomier ≥80mm-internal class)
#   5×9×5h   interior ~186.4 × ~102.4mm, 17.5mm well (≤185×82×~13mm flat object)
#   3×5×10h  interior ~60.4 × ~102.4mm, 35mm well
#   6×2×5h   interior ~123.4 × ~39.4mm, 17.5mm well
#   6×2×10h  interior ~123.4 × ~39.4mm, 35mm well
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[9,0]' -D 'height=[10,0]' -o "$OUT/bin-2x9x10h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[3,0]' -D 'depth=[3,0]' -D 'height=[10,0]' -o "$OUT/bin-3x3x10h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[4,0]' -D 'height=[10,0]' -o "$OUT/bin-2x4x10h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[5,0]' -D 'height=[10,0]' -o "$OUT/bin-2x5x10h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[5,0]' -D 'depth=[9,0]' -D 'height=[5,0]'  -o "$OUT/bin-5x9x5h.stl"  "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[3,0]' -D 'depth=[5,0]' -D 'height=[10,0]' -o "$OUT/bin-3x5x10h.stl" "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[6,0]' -D 'depth=[2,0]' -D 'height=[5,0]'  -o "$OUT/bin-6x2x5h.stl"  "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[6,0]' -D 'depth=[2,0]' -D 'height=[10,0]' -o "$OUT/bin-6x2x10h.stl" "$CUP"

# Owner-requested ad-hoc SKU (#282). Geometry-first / item-agnostic.
#   2×3×10h  interior ~39.4 × ~60.4mm, 35mm well
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[3,0]'  -D 'height=[10,0]' -o "$OUT/bin-2x3x10h.stl"  "$CUP"

# Owner-requested ad-hoc SKU batch (#284). Geometry-first / item-agnostic.
#   3×3×5h    interior ~60.4 × ~60.4mm,  17.5mm well
#   4×6×10h   interior ~81.4 × ~123.4mm, 35mm well
#   8×2×10h   interior ~165.4 × ~39.4mm, 35mm well
#   2×10×10h  interior ~39.4 × ~207.4mm, 35mm well
run_openscad "${BIN_FLAGS[@]}" -D 'width=[3,0]' -D 'depth=[3,0]'  -D 'height=[5,0]'  -o "$OUT/bin-3x3x5h.stl"   "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[4,0]' -D 'depth=[6,0]'  -D 'height=[10,0]' -o "$OUT/bin-4x6x10h.stl"  "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[8,0]' -D 'depth=[2,0]'  -D 'height=[10,0]' -o "$OUT/bin-8x2x10h.stl"  "$CUP"
run_openscad "${BIN_FLAGS[@]}" -D 'width=[2,0]' -D 'depth=[10,0]' -D 'height=[10,0]' -o "$OUT/bin-2x10x10h.stl" "$CUP"
