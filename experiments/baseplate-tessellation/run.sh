#!/usr/bin/env bash
# Baseplate-only tessellation experiment. Outputs are intentionally untracked.
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
BASE="$ROOT/scad/gridfinity/vendor/extended/gridfinity_baseplate.scad"
MATRIX="$ROOT/experiments/baseplate-tessellation/matrix.tsv"
AUDIT="$ROOT/experiments/baseplate-tessellation/mesh_audit.py"
OPENSCAD_BIN=${OPENSCAD_BIN:-openscad}
OPENSCAD_BACKEND=${OPENSCAD_BACKEND:-Manifold}
RENDER_TIMEOUT_SECONDS=${RENDER_TIMEOUT_SECONDS:-900}
COMPARE_TIMEOUT_SECONDS=${COMPARE_TIMEOUT_SECONDS:-300}

if [[ $# -ne 1 ]]; then
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  exit 2
fi
OUT=$1
mkdir -p "$OUT"
if find "$OUT" -mindepth 1 -print -quit | grep -q .; then
  echo "output directory must be empty: $OUT" >&2
  exit 2
fi

if ! command -v "$OPENSCAD_BIN" >/dev/null 2>&1; then
  echo "OpenSCAD unavailable: $OPENSCAD_BIN" >&2
  exit 127
fi

version=$($OPENSCAD_BIN --version 2>&1 | head -n 1)
arch=$(uname -m)
commit=$(git -C "$ROOT" rev-parse HEAD)
vendor_hash=$(sha256sum "$BASE" | awk '{print $1}')
script_hash=$(sha256sum "$ROOT/scad/gridfinity/dental/build-stl.sh" | awk '{print $1}')
matrix_hash=$(sha256sum "$MATRIX" | awk '{print $1}')
openscad_command=$(command -v "$OPENSCAD_BIN")
openscad_command_hash=$(sha256sum "$openscad_command" | awk '{print $1}')
runner_hash=$(sha256sum "$ROOT/experiments/baseplate-tessellation/run.sh" | awk '{print $1}')
audit_hash=$(sha256sum "$AUDIT" | awk '{print $1}')
manifest_hash=$(sha256sum "$ROOT/experiments/baseplate-tessellation/run_manifest.py" | awk '{print $1}')
cases="$OUT/cases.tsv"
printf 'phase\tcandidate\tartifact\texit_code\n' > "$cases"
failed=0

while IFS=$'\t' read -r id fn fa fs; do
  [[ "$id" == "id" || -z "$id" ]] && continue
  for spec in mini:6 regular:12 mega:18; do
    name=${spec%%:*}
    width=${spec##*:}
    dir="$OUT/$id"
    stl="$dir/baseplate-$name.stl"
    timing="$dir/baseplate-$name.time"
    mkdir -p "$dir"
    set +e
    /usr/bin/time -p -o "$timing" timeout "$RENDER_TIMEOUT_SECONDS" "$OPENSCAD_BIN" \
      --backend "$OPENSCAD_BACKEND" \
      -D 'pitch=[21,21,3.5]' -D 'Depth=[16,0]' -D "Width=[$width,0]" \
      -D "fn=$fn" -D "fa=$fa" -D "fs=$fs" -o "$stl" "$BASE" \
      >"$dir/baseplate-$name.stdout" 2>"$dir/baseplate-$name.stderr"
    status=$?
    set -e
    printf 'render\t%s\t%s\t%s\n' "$id" "$name" "$status" >> "$cases"
    if [[ $status -ne 0 ]]; then
      failed=1
      continue
    fi
    set +e
    timeout "$COMPARE_TIMEOUT_SECONDS" python3 "$AUDIT" analyze "$stl" > "$dir/baseplate-$name.audit.json"
    status=$?
    set -e
    printf 'audit\t%s\t%s\t%s\n' "$id" "$name" "$status" >> "$cases"
    [[ $status -eq 0 ]] || failed=1
  done
done < "$MATRIX"

if [[ $failed -ne 0 ]]; then
  echo "Render/audit matrix incomplete; exact cases are in $cases" >&2
  exit 1
fi

for id in fine medium coarse; do
  for name in mini regular mega; do
    set +e
    timeout "$COMPARE_TIMEOUT_SECONDS" python3 "$AUDIT" compare \
      "$OUT/current/baseplate-$name.stl" "$OUT/$id/baseplate-$name.stl" \
      > "$OUT/$id/baseplate-$name.compare.json"
    status=$?
    set -e
    printf 'compare\t%s\t%s\t%s\n' "$id" "$name" "$status" >> "$cases"
    if [[ $status -ne 0 ]]; then
      failed=1
    fi
  done
done

if [[ $failed -ne 0 ]]; then
  echo "Comparison matrix incomplete; exact cases are in $cases" >&2
  exit 1
fi

python3 "$ROOT/experiments/baseplate-tessellation/run_manifest.py" \
  --output "$OUT" --commit "$commit" --version "$version" --arch "$arch" \
  --backend "$OPENSCAD_BACKEND" \
  --canonical-vendor-hash "$vendor_hash" --render-source-hash "$vendor_hash" \
  --build-script-hash "$script_hash" \
  --matrix-hash "$matrix_hash" --openscad-command-hash "$openscad_command_hash" \
  --runner-hash "$runner_hash" --audit-hash "$audit_hash" --manifest-hash "$manifest_hash" \
  --matrix "$MATRIX" \
  > "$OUT/run.complete.json"
mv "$OUT/run.complete.json" "$OUT/run.json"

echo "Experiment complete: $OUT/run.json"
