#!/usr/bin/env python3
"""Assemble one complete run manifest after all renders and comparisons finish."""
import argparse
import json
import re
from pathlib import Path

DIMENSIONS = {"mini": [6, 16], "regular": [12, 16], "mega": [18, 16]}


def timing(time_path, stderr_path):
    rows = dict(line.split(maxsplit=1) for line in time_path.read_text().splitlines())
    wall_seconds = float(rows["real"])
    match = re.search(
        r"^Total rendering time:\s*(\d+):(\d+):(\d+(?:\.\d+)?)$",
        stderr_path.read_text(),
        re.MULTILINE,
    )
    if not match:
        raise ValueError(f"missing OpenSCAD rendering time: {stderr_path}")
    hours, minutes, seconds = match.groups()
    return {
        "render_seconds": int(hours) * 3600 + int(minutes) * 60 + float(seconds),
        "process_wall_seconds": wall_seconds if wall_seconds >= 0 else None,
    }


def variants(output, candidate, inputs):
    result = []
    for artifact, dimensions in DIMENSIONS.items():
        directory = output / candidate
        audit = json.loads((directory / f"baseplate-{artifact}.audit.json").read_text())
        times = timing(
            directory / f"baseplate-{artifact}.time",
            directory / f"baseplate-{artifact}.stderr",
        )
        result.append({
            "artifact": artifact,
            "dimensions_cells": dimensions,
            "stl_hash": audit["sha256"],
            "bytes": audit["bytes"],
            "facets": audit["facets"],
            "components": audit["components"],
            "manifold_or_watertight": audit["manifold_or_watertight"],
            "consistently_oriented": audit["consistently_oriented"],
            "euler_characteristic": audit["euler_characteristic"],
            "genus": audit["genus"],
            "bounds_mm": audit["bounds_mm"],
            **times,
            "effective_tessellation_inputs": inputs,
        })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--arch", required=True)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--canonical-vendor-hash", required=True)
    parser.add_argument("--render-source-hash", required=True)
    parser.add_argument("--render-source-transformation-hash")
    parser.add_argument("--build-script-hash", required=True)
    parser.add_argument("--matrix-hash", required=True)
    parser.add_argument("--openscad-command-hash", required=True)
    parser.add_argument("--runner-hash", required=True)
    parser.add_argument("--audit-hash", required=True)
    parser.add_argument("--manifest-hash", required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    args = parser.parse_args()
    rows = [line.split("\t") for line in args.matrix.read_text().splitlines()[1:] if line]
    matrix = [
        (row[0], {"fn": int(row[1]), "fa": float(row[2]), "fs": float(row[3])})
        for row in rows
    ]
    baseline_inputs = matrix[0][1]
    result = {
        "schema": "hutchfinity-baseplate-tessellation-run/v1",
        "source_commit": args.commit,
        "openscad_version": args.version,
        "openscad_arch": args.arch,
        "openscad_backend": args.backend,
        "vendor_source_hashes": [args.canonical_vendor_hash],
        "render_source_hash": args.render_source_hash,
        "render_source_matches_vendor": args.render_source_hash == args.canonical_vendor_hash,
        "build_script_hash": args.build_script_hash,
        "matrix_hash": args.matrix_hash,
        "openscad_command_hash": args.openscad_command_hash,
        "experiment_harness_hashes": {
            "run.sh": args.runner_hash,
            "mesh_audit.py": args.audit_hash,
            "run_manifest.py": args.manifest_hash,
        },
        "variants": variants(args.output, "current", baseline_inputs),
        "candidates": [],
        "production_fit": False,
    }
    if args.render_source_transformation_hash:
        result["render_source_transformation_hash"] = args.render_source_transformation_hash
    for candidate, inputs in matrix[1:]:
        result["candidates"].append({
            "id": candidate,
            "effective_tessellation_inputs": inputs,
            "variants": variants(args.output, candidate, inputs),
            "comparisons": {
                artifact: json.loads((args.output / candidate / f"baseplate-{artifact}.compare.json").read_text())
                for artifact in DIMENSIONS
            },
        })
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
