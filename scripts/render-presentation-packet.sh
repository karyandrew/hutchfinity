#!/bin/sh
set -eu

SOURCE_COMMIT=29273ab21605eba859088c18fd1bc50087d86709
EXPECTED_OPENSCAD_VERSION='OpenSCAD version 2026.09.23'
OPENSCAD_BIN=${OPENSCAD:-openscad}

repo_root=$(git rev-parse --show-toplevel)
GIT_WORK_TREE=$repo_root
export GIT_WORK_TREE
manifest="$repo_root/docs/presentation/hutchfinity-32-manifest.json"
verifier="$repo_root/scripts/verify_presentation_packet.py"
output_dir="$repo_root/preview/issue-32"
work_dir=$(mktemp -d)
source_tree="$work_dir/source"
stage_tree="$work_dir/stage"
audit_dir="$work_dir/audit"
summary_dir="$work_dir/summary"
log_dir="$work_dir/log"

cleanup() {
    rm -rf "$work_dir"
}
trap cleanup EXIT HUP INT TERM

actual_version=$($OPENSCAD_BIN --version 2>&1)
if [ "$actual_version" != "$EXPECTED_OPENSCAD_VERSION" ]; then
    printf 'FAIL OPENSCAD_VERSION_MISMATCH: expected %s, got %s\n' \
        "$EXPECTED_OPENSCAD_VERSION" "$actual_version" >&2
    exit 1
fi

mkdir -p "$source_tree" "$stage_tree/preview/issue-32" "$audit_dir" "$summary_dir" "$log_dir"
git -C "$repo_root" archive "$SOURCE_COMMIT" | tar -x -C "$source_tree"
mkdir -p "$source_tree/scad/presentation"
cp "$repo_root/scad/presentation/single-slot-hero.scad" "$source_tree/scad/presentation/"
cp "$repo_root/scad/presentation/single-slot-exploded.scad" "$source_tree/scad/presentation/"

render_scene() {
    scene_id=$1
    width=$2
    height=$3
    camera=$4
    source_file="$source_tree/scad/presentation/$scene_id.scad"
    output_file="$stage_tree/preview/issue-32/$scene_id.png"
    audit_file="$audit_dir/$scene_id.echo"
    summary_file="$summary_dir/$scene_id.json"
    deps_file="$summary_dir/$scene_id.deps"
    log_file="$log_dir/$scene_id.log"

    "$OPENSCAD_BIN" --hardwarnings \
        -o "$audit_file" \
        "$source_file" >"$log_file" 2>&1
    if grep -Eq '^(ERROR|WARNING):' "$audit_file" "$log_file"; then
        printf 'FAIL OPENSCAD_AUDIT_ERROR: %s\n' "$scene_id" >&2
        sed -n '1,120p' "$audit_file" >&2
        sed -n '1,120p' "$log_file" >&2
        exit 1
    fi

    "$OPENSCAD_BIN" --hardwarnings --render --backend Manifold \
        --projection p \
        --camera "$camera" \
        --imgsize "$width,$height" \
        --colorscheme Tomorrow \
        --summary all \
        --summary-file "$summary_file" \
        -d "$deps_file" \
        -o "$output_file" \
        "$source_file" >"$log_file" 2>&1
    if grep -Eq '^(ERROR|WARNING):' "$log_file"; then
        printf 'FAIL OPENSCAD_RENDER_ERROR: %s\n' "$scene_id" >&2
        sed -n '1,160p' "$log_file" >&2
        exit 1
    fi
}

render_scene single-slot-hero 2048 2048 '975.28,-1074.6,599,154,70,-50'
render_scene single-slot-exploded 1800 2400 '1149.5,-1896.1,1106.9,154,-80,-80'

python3 "$verifier" \
    --manifest "$manifest" \
    --repo-root "$repo_root" \
    --source-root "$source_tree" \
    --packet-root "$repo_root" \
    --output-root "$stage_tree" \
    --audit "single-slot-hero=$audit_dir/single-slot-hero.echo" \
    --audit "single-slot-exploded=$audit_dir/single-slot-exploded.echo" \
    --summary "single-slot-hero=$summary_dir/single-slot-hero.json" \
    --summary "single-slot-exploded=$summary_dir/single-slot-exploded.json" \
    --dependencies "single-slot-hero=$summary_dir/single-slot-hero.deps" \
    --dependencies "single-slot-exploded=$summary_dir/single-slot-exploded.deps"

mkdir -p "$output_dir"
for name in single-slot-hero.png single-slot-exploded.png; do
    cp "$stage_tree/preview/issue-32/$name" "$output_dir/.$name.tmp"
    mv "$output_dir/.$name.tmp" "$output_dir/$name"
done

printf 'Rendered and verified deterministic packet at %s\n' "$output_dir"
