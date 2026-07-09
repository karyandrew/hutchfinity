#!/usr/bin/env bash
# Build the casing-fit-trial-01 mini/regular/mega print set.
#
# Usage: scad/testbed/build-mini-regular-mega-print-set.sh [output-dir]

set -euo pipefail
cd "$(dirname "$0")/../.."

OUT="${1:-preview/casing-fit-trial-01/mini-regular-mega-print-set}"
SOURCE="scad/testbed/mini_regular_mega_print_set.scad"
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

export_part() {
  local part="$1"
  local file="$2"
  run_openscad -D "PRINT_PART=\"$part\"" -o "$OUT/$file" "$SOURCE"
}

mkdir -p "$OUT"

export_part casing-mini casing-mini-23u-magnetic.stl
export_part casing-regular casing-regular-23u-magnetic.stl
export_part casing-mega casing-mega-23u-magnetic.stl

export_part tub-mini tub-mini-magnetic.stl
export_part tub-regular tub-regular-magnetic.stl
export_part tub-mega tub-mega-magnetic.stl

cp scad/gridfinity/stl/baseplate-mini.stl "$OUT/grid-mini-baseplate.stl"
cp scad/gridfinity/stl/baseplate-regular.stl "$OUT/grid-regular-baseplate.stl"
cp scad/gridfinity/stl/baseplate-mega.stl "$OUT/grid-mega-baseplate.stl"

export_part knob knob-glue-on.stl
export_part hex-peg-set hex-peg-set-7.stl
