#!/usr/bin/env bash
# Render and measure the issue #26 Mini Basket/Carrier comparison packet.
#
# Usage: scad/testbed/build-basket-carrier-mini-probe.sh [output-dir]

set -euo pipefail
cd "$(dirname "$0")/../.."

OUT="${1:-preview/issue-26/basket-carrier-mini-probe}"
SOURCE="scad/testbed/basket_carrier_comparison.scad"
OPENSCAD_BIN="${OPENSCAD_BIN:-openscad}"

mkdir -p "$OUT"
rendered_files=()

render_comparison() {
  local part="$1"
  local current_magnets="$2"
  local candidate_magnets="$3"
  local floor_mode="$4"
  local output_file="$5"

  "$OPENSCAD_BIN" \
    -D "COMPARISON_PART=\"$part\"" \
    -D "CURRENT_MAGNETS=$current_magnets" \
    -D "CANDIDATE_MAGNETS=$candidate_magnets" \
    -D "COMPARE_FLOOR_MODE=\"$floor_mode\"" \
    -o "$OUT/$output_file" \
    "$SOURCE"
  rendered_files+=("$output_file")
}

render_comparison candidate false false plain candidate-plain-no-magnets.stl
render_comparison candidate false true plain candidate-plain-magnetic.stl
render_comparison candidate false false integral candidate-integral-no-magnets.stl
render_comparison candidate false false removable candidate-removable-no-magnets.stl
render_comparison current false false plain current-mini-no-magnets.stl
render_comparison current true false plain current-mini-magnetic.stl
render_comparison current-center-floor-probe false false plain current-center-floor-probe.stl
render_comparison candidate-center-floor-probe false false plain candidate-center-floor-probe.stl

render_comparison intersection false false plain shared-no-magnets.stl
render_comparison current-only false false plain current-only-no-magnets.stl
render_comparison candidate-only false false plain candidate-only-no-magnets.stl
render_comparison intersection true false plain shared-current-magnetic-candidate-plain.stl
render_comparison current-only true false plain current-only-current-magnetic-candidate-plain.stl
render_comparison candidate-only true false plain candidate-only-current-magnetic-candidate-plain.stl
render_comparison intersection true true plain shared-both-magnetic.stl
render_comparison current-only true true plain current-only-both-magnetic.stl
render_comparison candidate-only true true plain candidate-only-both-magnetic.stl

render_comparison self-stack-overlap-witness false false plain self-stack-overlap-witness.stl
render_comparison removable-grid-interference false false removable removable-grid-interference.stl
render_comparison removable-grid-interference-witness false false removable removable-grid-interference-witness.stl
render_comparison removable-grid-side-interference-witness false false removable removable-grid-side-interference-witness.stl
render_comparison casing-slot-overflow-witness false false plain casing-slot-overflow-witness.stl

metrics_file="$OUT/metrics.tsv"
printf 'file\tmin_x\tmin_y\tmin_z\tmax_x\tmax_y\tmax_z\tsize_x\tsize_y\tsize_z\tvolume_mm3\tfacets\n' > "$metrics_file"

for output_file in "${rendered_files[@]}"; do
  mesh_file="$OUT/$output_file"
  awk -v file="$output_file" '
    BEGIN { vertex_index = 0 }
    /vertex/ {
      x[vertex_index] = $2
      y[vertex_index] = $3
      z[vertex_index] = $4

      if (!seen || $2 < min_x) min_x = $2
      if (!seen || $2 > max_x) max_x = $2
      if (!seen || $3 < min_y) min_y = $3
      if (!seen || $3 > max_y) max_y = $3
      if (!seen || $4 < min_z) min_z = $4
      if (!seen || $4 > max_z) max_z = $4
      seen = 1

      vertex_index++
      if (vertex_index == 3) {
        volume += (x[0] * (y[1] * z[2] - z[1] * y[2]) - y[0] * (x[1] * z[2] - z[1] * x[2]) + z[0] * (x[1] * y[2] - y[1] * x[2])) / 6
        facets++
        vertex_index = 0
      }
    }
    END {
      if (volume < 0) volume = -volume
      printf "%s\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%d\n",
        file,
        min_x, min_y, min_z,
        max_x, max_y, max_z,
        max_x - min_x, max_y - min_y, max_z - min_z,
        volume, facets
    }
  ' "$mesh_file" >> "$metrics_file"
done

awk -F '\t' '
  function abs(value) {
    return value < 0 ? -value : value
  }
  $1 == "candidate-plain-no-magnets.stl" {
    envelope_ok = abs($8 - 130.4) < 0.000001 && abs($9 - 340.4) < 0.000001 && abs($10 - 84.24) < 0.000001
  }
  $1 == "current-center-floor-probe.stl" {
    current_floor_ok = abs($7 - 4.703059) < 0.000001
  }
  $1 == "candidate-center-floor-probe.stl" {
    candidate_floor_ok = abs($7 - 4.7) < 0.000001
  }
  $1 == "self-stack-overlap-witness.stl" {
    stack_ok = abs($11 - 1) < 0.000001 && $12 == 12
  }
  $1 == "casing-slot-overflow-witness.stl" {
    casing_ok = abs($11 - 1) < 0.000001 && $12 == 12
  }
  $1 == "removable-grid-interference.stl" {
    removable_evidence_ok = $11 > 0
  }
  END {
    if (!envelope_ok) {
      print "candidate envelope verification failed" > "/dev/stderr"
      exit 1
    }
    if (!current_floor_ok || !candidate_floor_ok) {
      print "center-floor probe verification failed" > "/dev/stderr"
      exit 1
    }
    if (!stack_ok) {
      print "self-stack overlap verification failed" > "/dev/stderr"
      exit 1
    }
    if (!casing_ok) {
      print "casing slot containment verification failed" > "/dev/stderr"
      exit 1
    }
    if (!removable_evidence_ok) {
      print "removable-grid boundary evidence is missing" > "/dev/stderr"
      exit 1
    }
  }
' "$metrics_file"

printf 'Rendered comparison packet: %s\n' "$OUT"
printf 'Metrics: %s\n' "$metrics_file"
printf 'Verification gates passed\n'
