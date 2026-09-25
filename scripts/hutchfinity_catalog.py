#!/usr/bin/env python3
"""Build and evaluate the public Hutchfinity bin catalog.

The calculations in this module are intentionally source-derived.  They are
not physical-fit receipts and they never promote a mapping to ACCEPTED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import struct
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker, RefResolver


ROOT = Path(__file__).resolve().parents[1]
BUILD_SOURCE = Path("scad/gridfinity/dental/build-stl.sh")
CUP_SOURCE = Path("scad/gridfinity/vendor/extended/gridfinity_basic_cup.scad")
STL_DIR = Path("scad/gridfinity/stl")
SCHEMA_DIR = ROOT / "catalog/schemas"
AUTHORITATIVE_CATALOG = ROOT / "catalog/bin-skus.json"
AUTHORITATIVE_CLASSES = ROOT / "catalog/item-classes.json"
SKU_RE = re.compile(r"bin-(\d+)x(\d+)x(\d+)h(?:\.stl)?$")
PITCH_XY_MM = 21.0
PITCH_Z_MM = 3.5
CLEARANCE_XY_MM = 0.5
FLOOR_HEIGHT_MM = 5.7
MINIMUM_LIP_HEIGHT_MM = 3.74
GIT_SELECTOR_ENV = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
}
ACCEPTANCE_FIELDS = {
    "selection_status",
    "physical_fit_state",
    "physical_fit_receipt",
    "validation_lane",
    "validation_receipt",
}
FORMAT_CHECKER = FormatChecker()
SCHEMA_CACHE: dict[str, dict[str, Any]] | None = None


@FORMAT_CHECKER.checks("date-time")
def is_rfc3339_datetime(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def source_commit() -> str:
    environment = os.environ.copy()
    for key in GIT_SELECTOR_ENV:
        environment.pop(key, None)
    environment["GIT_WORK_TREE"] = str(ROOT)
    return subprocess.run(
        ["git", "log", "-1", "--format=%H", "HEAD", "--", str(BUILD_SOURCE), str(CUP_SOURCE), str(STL_DIR)], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE, env=environment,
    ).stdout.strip()


def validate_schema(value: Any, schema_name: str, label: str) -> None:
    global SCHEMA_CACHE
    if SCHEMA_CACHE is None:
        SCHEMA_CACHE = {
            path.name: read_json(path)
            for path in sorted(SCHEMA_DIR.glob("*.schema.json"))
        }
    schema = SCHEMA_CACHE[schema_name]
    store = {document["$id"]: document for document in SCHEMA_CACHE.values()}
    validator = Draft202012Validator(
        schema,
        format_checker=FORMAT_CHECKER,
        resolver=RefResolver.from_schema(schema, store=store),
    )
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.absolute_path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise ValueError(f"{label} schema validation failed at {location}: {error.message}")


def validate_item_class_set(classes: dict[str, Any]) -> None:
    validate_schema(classes, "item-class-set.schema.json", "item-class set")
    for index, item in enumerate(classes["items"]):
        validate_schema(item, "item-class.schema.json", f"item class {index}")
    identifiers = [item["item_class_id"] for item in classes["items"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("item-class set contains duplicate item_class_id values")


def validate_catalog_schema(catalog: dict[str, Any]) -> None:
    validate_schema(catalog, "bin-catalog.schema.json", "bin catalog")
    for index, sku in enumerate(catalog["items"]):
        validate_schema(sku, "bin-sku.schema.json", f"bin SKU {index}")
    identifiers = [sku["sku"] for sku in catalog["items"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("bin catalog contains duplicate SKU values")


def validate_map_set_schema(map_set: dict[str, Any]) -> None:
    validate_schema(map_set, "item-class-map-set.schema.json", "item-class map set")
    for index, mapping in enumerate(map_set["mappings"]):
        validate_schema(mapping, "item-class-map.schema.json", f"item-class map {index}")
    identifiers = [mapping["item_class_id"] for mapping in map_set["mappings"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("item-class map set contains duplicate item_class_id values")


def require_authoritative_path(path: Path, expected: Path, label: str) -> None:
    if path.resolve() != expected.resolve():
        raise ValueError(f"{label} must be the authoritative repository file: {expected.relative_to(ROOT)}")


def checked_repo_file(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError(f"referenced path escapes the repository: {relative_path}") from error
    if not candidate.is_file():
        raise ValueError(f"referenced file does not exist: {relative_path}")
    return candidate


def wall_thickness_mm(height_units: int) -> float:
    if height_units < 6:
        return 0.95
    if height_units < 12:
        return 1.2
    return 1.6


def source_dimensions(cells_x: int, cells_y: int, height_units: int) -> dict[str, Any]:
    wall = wall_thickness_mm(height_units)
    wall_x = cells_x * PITCH_XY_MM - CLEARANCE_XY_MM - 2 * wall
    wall_y = cells_y * PITCH_XY_MM - CLEARANCE_XY_MM - 2 * wall
    floor_edge_radius = 3.75 - wall
    total_z = height_units * PITCH_Z_MM + MINIMUM_LIP_HEIGHT_MM
    return {
        "external_bounds_mm": {
            "x": round(cells_x * PITCH_XY_MM - CLEARANCE_XY_MM, 3),
            "y": round(cells_y * PITCH_XY_MM - CLEARANCE_XY_MM, 3),
            "z": round(total_z, 3),
        },
        "verified_internal_bounds_mm": {
            "verification_basis": "current_source_geometry",
            "wall_span_mm": {
                "x": round(wall_x, 3),
                "y": round(wall_y, 3),
                "z": round(total_z - FLOOR_HEIGHT_MM, 3),
            },
            "conservative_flat_floor_span_mm": {
                "x": round(wall_x - 2 * floor_edge_radius, 3),
                "y": round(wall_y - 2 * floor_edge_radius, 3),
            },
            "floor_z_mm": FLOOR_HEIGHT_MM,
            "floor_edge_radius_mm": round(floor_edge_radius, 3),
            "interior_corner_radius_mm": round(3.75 - wall, 3),
            "top_open": True,
        },
        "wall_floor_lip_contract": {
            "wall_thickness_mm": wall,
            "floor_height_mm": FLOOR_HEIGHT_MM,
            "floor_edge_radius_mm": round(floor_edge_radius, 3),
            "lip_style": "minimum",
            "top_obstruction": "none",
            "fit_caveat": "Wall span is not a flat-floor fit oracle; the rounded floor edge reduces conservative full-footprint span.",
        },
    }


def mesh_metrics(path: Path) -> dict[str, Any]:
    minimum = [math.inf, math.inf, math.inf]
    maximum = [-math.inf, -math.inf, -math.inf]
    triangles: list[tuple[Any, Any, Any]] = []
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(84)
        triangle_count = struct.unpack("<I", header[80:84])[0] if len(header) == 84 else 0
        is_binary = 84 + triangle_count * 50 == size
        if is_binary:
            for _ in range(triangle_count):
                triangle = stream.read(50)
                values = struct.unpack("<12fH", triangle)
                vertices = tuple(tuple(values[offset:offset + 3]) for offset in (3, 6, 9))
                triangles.append(vertices)
                for vertex in vertices:
                    minimum = [min(old, value) for old, value in zip(minimum, vertex)]
                    maximum = [max(old, value) for old, value in zip(maximum, vertex)]
        else:
            stream.seek(0)
            vertices = []
            for raw_line in stream:
                fields = raw_line.decode("ascii").split()
                if len(fields) == 4 and fields[0] == "vertex":
                    vertex = tuple(float(value) for value in fields[1:])
                    vertices.append(vertex)
                    minimum = [min(old, value) for old, value in zip(minimum, vertex)]
                    maximum = [max(old, value) for old, value in zip(maximum, vertex)]
                    if len(vertices) == 3:
                        triangles.append(tuple(vertices))
                        vertices = []
    if not triangles:
        raise ValueError(f"no STL triangles found in {path}")
    signed_volume = 0.0
    for first, second, third in triangles:
        cross = (
            second[1] * third[2] - second[2] * third[1],
            second[2] * third[0] - second[0] * third[2],
            second[0] * third[1] - second[1] * third[0],
        )
        signed_volume += sum(value * other for value, other in zip(first, cross)) / 6.0
    return {
        "mesh_aabb_mm": {
            "x": round(maximum[0] - minimum[0], 6),
            "y": round(maximum[1] - minimum[1], 6),
            "z": round(maximum[2] - minimum[2], 6),
        },
        "mesh_volume_mm3": round(abs(signed_volume), 3),
        "triangle_count": len(triangles),
    }


def build_managed_names() -> set[str]:
    text = (ROOT / BUILD_SOURCE).read_text(encoding="utf-8")
    return {match.group(0) for match in re.finditer(r"bin-\d+x\d+x\d+h\.stl", text)}


def source_hashes() -> list[dict[str, str]]:
    return [
        {"path": str(path), "sha256": sha256(ROOT / path)}
        for path in (BUILD_SOURCE, CUP_SOURCE)
    ]


def build_catalog() -> dict[str, Any]:
    managed = build_managed_names()
    commit = source_commit()
    sources = source_hashes()
    records = []
    for path in sorted((ROOT / STL_DIR).glob("bin-*x*x*h.stl")):
        match = SKU_RE.fullmatch(path.name)
        if not match:
            continue
        cells_x, cells_y, height_units = map(int, match.groups())
        current = path.name in managed
        dimensions = source_dimensions(cells_x, cells_y, height_units) if current else {
            "external_bounds_mm": None,
            "verified_internal_bounds_mm": None,
            "wall_floor_lip_contract": None,
        }
        handling = {
            "compartment_count": 1,
            "visibility_supported": ["open", "labelled"],
            "retrieval_modes_supported": ["finger_grab", "pinch", "pour", "lift_bundle"],
        } if current else None
        relative = path.relative_to(ROOT)
        metrics = mesh_metrics(path)
        records.append({
            "schema": "hutchfinity-bin-sku/v1",
            "sku": path.stem,
            "cells_x": cells_x,
            "cells_y": cells_y,
            "height_units": height_units,
            "nominal_pitch_mm": PITCH_XY_MM,
            **dimensions,
            "handling_contract": handling,
            "base_interface": "gridfinity-half-pitch-21mm",
            "catalog_state": "build_managed" if current else "tracked_unmanaged",
            "source_output_link_state": "unverified",
            "source_commit": commit,
            "source_files_and_hashes": sources,
            "output_hashes": [{
                "path": str(relative),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                **metrics,
            }],
            "validation_state": "rendered" if current else "stale",
            "validated_printer_lanes": [],
        })
    return {
        "schema": "hutchfinity-bin-catalog/v1",
        "source_commit": commit,
        "source_files_and_hashes": sources,
        "inventory_summary": {
            "tracked_bin_outputs": len(records),
            "build_managed_outputs": sum(item["catalog_state"] == "build_managed" for item in records),
            "tracked_unmanaged_outputs": sum(item["catalog_state"] == "tracked_unmanaged" for item in records),
            "source_output_links_reproduced": 0,
        },
        "items": records,
    }


def verify_hash_reference(reference: dict[str, Any], *, require_size: bool = False) -> None:
    path = checked_repo_file(reference["path"])
    if sha256(path) != reference["sha256"]:
        raise ValueError(f"referenced file hash does not match actual bytes: {reference['path']}")
    if require_size and path.stat().st_size != reference["bytes"]:
        raise ValueError(f"referenced file size does not match actual bytes: {reference['path']}")


def validate_catalog_authority(catalog: dict[str, Any], required_skus: set[str] | None = None) -> None:
    """Bind catalog claims to current source and selected local artifact bytes."""
    validate_catalog_schema(catalog)
    actual_sources = source_hashes()
    if catalog["source_commit"] != source_commit():
        raise ValueError("bin catalog source_commit does not match the current source/artifact revision")
    if catalog["source_files_and_hashes"] != actual_sources:
        raise ValueError("bin catalog source hashes do not match authoritative source bytes")

    managed_names = build_managed_names()
    expected_counts = {
        "tracked_bin_outputs": len(catalog["items"]),
        "build_managed_outputs": sum(item["catalog_state"] == "build_managed" for item in catalog["items"]),
        "tracked_unmanaged_outputs": sum(item["catalog_state"] == "tracked_unmanaged" for item in catalog["items"]),
        "source_output_links_reproduced": sum(item["source_output_link_state"] == "reproduced" for item in catalog["items"]),
    }
    if catalog["inventory_summary"] != expected_counts:
        raise ValueError("bin catalog inventory summary does not match its records")

    by_sku = {item["sku"]: item for item in catalog["items"]}
    required = (
        {item["sku"] for item in catalog["items"] if item["catalog_state"] == "build_managed"}
        if required_skus is None else required_skus
    )
    missing = required - set(by_sku)
    if missing:
        raise ValueError(f"map references SKU values absent from the authoritative catalog: {sorted(missing)}")

    for sku, item in by_sku.items():
        match = SKU_RE.fullmatch(sku)
        if match is None:
            raise ValueError(f"catalog SKU cannot be parsed: {sku}")
        cells_x, cells_y, height_units = map(int, match.groups())
        if (item["cells_x"], item["cells_y"], item["height_units"]) != (cells_x, cells_y, height_units):
            raise ValueError(f"catalog cell dimensions do not match SKU: {sku}")
        expected_managed = f"{sku}.stl" in managed_names
        expected_state = "build_managed" if expected_managed else "tracked_unmanaged"
        if item["catalog_state"] != expected_state:
            raise ValueError(f"catalog state does not match the current build recipe: {sku}")
        if item["source_commit"] != catalog["source_commit"] or item["source_files_and_hashes"] != actual_sources:
            raise ValueError(f"catalog SKU source binding does not match authoritative source: {sku}")
        expected_dimensions = source_dimensions(cells_x, cells_y, height_units) if expected_managed else {
            "external_bounds_mm": None,
            "verified_internal_bounds_mm": None,
            "wall_floor_lip_contract": None,
        }
        for field, expected in expected_dimensions.items():
            if item[field] != expected:
                raise ValueError(f"catalog source-derived geometry does not match current formulas: {sku}.{field}")

        if sku in required:
            expected_output_path = str(STL_DIR / f"{sku}.stl")
            if len(item["output_hashes"]) != 1 or item["output_hashes"][0]["path"] != expected_output_path:
                raise ValueError(f"catalog output path is not authoritative for SKU: {sku}")
            verify_hash_reference(item["output_hashes"][0], require_size=True)

    for reference in actual_sources:
        verify_hash_reference(reference)


def orientations(item: dict[str, Any]) -> Iterable[tuple[str, tuple[int, int, int]]]:
    allowed = set(item["orientation_allowed"])
    rotation = item["allowed_rotation"]
    candidates: list[tuple[str, tuple[int, int, int]]] = []
    if "flat" in allowed:
        candidates.append(("flat", (0, 1, 2)))
        if rotation in {"xy_swap", "free"}:
            candidates.append(("flat_xy_swap", (1, 0, 2)))
    if "edge" in allowed:
        candidates.extend([("edge_x", (0, 2, 1)), ("edge_y", (2, 0, 1))])
    if "upright" in allowed:
        candidates.extend([("upright_x", (1, 2, 0)), ("upright_y", (2, 1, 0))])
    seen: set[tuple[int, int, int]] = set()
    for label, permutation in candidates:
        if permutation not in seen:
            seen.add(permutation)
            yield label, permutation


def permuted_axis_values(record: dict[str, Any], permutation: tuple[int, int, int]) -> list[float | None]:
    original = [record[axis] for axis in ("x", "y", "z")]
    return [original[index] for index in permutation]


def required_envelope(item: dict[str, Any], permutation: tuple[int, int, int]) -> list[float | None]:
    dimensions = permuted_axis_values(item["bounding_box_mm"], permutation)
    uncertainty = permuted_axis_values(item["uncertainty_mm"], permutation)
    clearance = permuted_axis_values(item["grab_clearance_mm"], permutation)
    result: list[float | None] = []
    for dimension, error, room in zip(dimensions, uncertainty, clearance):
        if dimension is None or error is None or room is None:
            result.append(None)
        else:
            result.append(round(dimension + error + room, 3))
    return result


def rounded_rectangle_fits(required_x: float, required_y: float, span_x: float, span_y: float, radius: float) -> bool:
    if required_x > span_x or required_y > span_y:
        return False
    dx = max(0.0, required_x / 2 - (span_x / 2 - radius))
    dy = max(0.0, required_y / 2 - (span_y / 2 - radius))
    return dx == 0 or dy == 0 or dx * dx + dy * dy <= radius * radius + 1e-9


def evaluate_orientation(item: dict[str, Any], sku: dict[str, Any], label: str, permutation: tuple[int, int, int]) -> dict[str, Any]:
    bounds = sku["verified_internal_bounds_mm"]
    required = required_envelope(item, permutation)
    wall = [bounds["wall_span_mm"][axis] for axis in ("x", "y", "z")]
    wall_margins = [None if value is None else round(limit - value, 3) for value, limit in zip(required, wall)]
    floor = bounds["conservative_flat_floor_span_mm"]
    floor_margins = {
        "x": None if required[0] is None else round(floor["x"] - required[0], 3),
        "y": None if required[1] is None else round(floor["y"] - required[1], 3),
    }
    reasons: list[str] = []
    unknown_axes = [axis for axis, value in zip(("x", "y", "z"), required) if value is None]
    if unknown_axes:
        reasons.append("unknown required envelope axes: " + ", ".join(unknown_axes))
    if any(value is not None and value < 0 for value in wall_margins):
        reasons.append("negative wall-span margin")
    if required[0] is not None and required[1] is not None and not rounded_rectangle_fits(
        required[0], required[1], wall[0], wall[1], bounds["interior_corner_radius_mm"]
    ):
        reasons.append("rounded interior corner conflict")
    constraints = item["special_constraints"]
    if constraints["minimum_internal_long_axis_mm"] is not None and max(wall[0], wall[1]) < constraints["minimum_internal_long_axis_mm"]:
        reasons.append("minimum internal long axis not met")
    if constraints["requires_unobstructed_top"] and not bounds["top_open"]:
        reasons.append("top retrieval obstructed")
    handling = sku["handling_contract"]
    if item["separator_or_compartment_need"] == "required" and handling["compartment_count"] < 2:
        reasons.append("required separator or compartments unavailable")
    if item["visibility_need"] != "either" and item["visibility_need"] not in handling["visibility_supported"]:
        reasons.append("visibility need not supported")
    if item["retrieval_mode"] != "other" and item["retrieval_mode"] not in handling["retrieval_modes_supported"]:
        reasons.append("retrieval mode not supported")
    if item["retrieval_mode"] == "other":
        reasons.append("other retrieval mode requires explicit physical evaluation")

    floor_conflict = constraints["flat_floor_contact_required"] and any(
        value is not None and value < 0 for value in floor_margins.values()
    )
    if floor_conflict:
        reasons.append("conservative flat-floor span is negative; wall span alone is not a fit oracle")

    non_failure_reasons = {
        "conservative flat-floor span is negative; wall span alone is not a fit oracle",
        "unknown required envelope axes: " + ", ".join(unknown_axes),
        "other retrieval mode requires explicit physical evaluation",
    }
    hard_failure = any(reason not in non_failure_reasons for reason in reasons)
    if hard_failure:
        outcome = "fail"
    elif floor_conflict or unknown_axes or item["retrieval_mode"] == "other":
        outcome = "inconclusive"
    else:
        outcome = "pass"

    capacity = None
    if outcome == "pass" and all(value is not None and value > 0 for value in required):
        capacity = math.prod(max(1, math.floor(limit / value)) for limit, value in zip(wall, required))
        if item["minimum_quantity_per_bin"] is not None and capacity < item["minimum_quantity_per_bin"]:
            outcome = "fail"
            reasons.append("minimum quantity not met")

    return {
        "sku": sku["sku"],
        "orientation": label,
        "outcome": outcome,
        "required_envelope_mm": dict(zip(("x", "y", "z"), required)),
        "wall_span_margins_mm": dict(zip(("x", "y", "z"), wall_margins)),
        "flat_floor_margins_mm": floor_margins,
        "quantity_capacity": capacity,
        "unknown_axes": unknown_axes,
        "reasons": reasons,
    }


def sku_rank(sku: dict[str, Any], evaluation: dict[str, Any]) -> tuple[Any, ...]:
    bounds = sku["verified_internal_bounds_mm"]["wall_span_mm"]
    required = evaluation["required_envelope_mm"]
    required_volume = math.prod(value for value in required.values() if value is not None)
    wasted = bounds["x"] * bounds["y"] * bounds["z"] - required_volume
    material_proxy = sku["output_hashes"][0]["mesh_volume_mm3"]
    return (sku["cells_x"] * sku["cells_y"], sku["height_units"], material_proxy, round(wasted, 3), sku["sku"])


def best_evaluation(item: dict[str, Any], sku: dict[str, Any]) -> dict[str, Any]:
    evaluations = [evaluate_orientation(item, sku, label, permutation) for label, permutation in orientations(item)]
    order = {"pass": 0, "inconclusive": 1, "fail": 2}
    return min(evaluations, key=lambda row: (order[row["outcome"]], min(
        (margin for margin in row["wall_span_margins_mm"].values() if margin is not None),
        default=-math.inf,
    ) * -1, row["orientation"]))


def artifact_hash_refs(sku: dict[str, Any]) -> list[dict[str, str]]:
    refs = list(sku["source_files_and_hashes"])
    refs.extend({"path": row["path"], "sha256": row["sha256"]} for row in sku["output_hashes"])
    return refs


def select_item(item: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    active = [sku for sku in catalog["items"] if sku["catalog_state"] == "build_managed"]
    evaluated = [(sku, best_evaluation(item, sku)) for sku in active]
    passing = sorted((pair for pair in evaluated if pair[1]["outcome"] == "pass"), key=lambda pair: sku_rank(*pair))
    targets = item.get("initial_evaluation_target_skus", [])
    by_name = {sku["sku"]: (sku, result) for sku, result in evaluated}

    if passing:
        preferred_pair = passing[0]
        fallback_pairs = passing[1:2]
    else:
        target_pairs = [by_name[name] for name in targets if name in by_name]
        preferred_pair = target_pairs[0] if target_pairs else None
        fallback_pairs = target_pairs[1:2]

    if preferred_pair is None:
        preferred_sku = None
        preferred = None
        hashes: list[dict[str, str]] = []
    else:
        selected_sku, preferred = preferred_pair
        preferred_sku = selected_sku["sku"]
        hashes = artifact_hash_refs(selected_sku)

    fallback_skus = [sku["sku"] for sku, _ in fallback_pairs]
    candidate_rows = []
    included = {preferred_sku, *fallback_skus, *targets}
    for sku, result in evaluated:
        if sku["sku"] in included:
            candidate_rows.append(result)

    if preferred is None:
        rationale = "No build-managed candidate passed or was named as an initial evaluation target."
    elif preferred["outcome"] == "pass":
        rationale = "Smallest build-managed candidate passing source-derived geometry, handling, quantity, and retrieval constraints; physical fit has not run."
    else:
        rationale = "Publicly named candidate retained as a physical-fit target, but source evidence is incomplete or conservative floor geometry is inconclusive; it is not a passing fit claim."

    status = "CUSTOM_SKU_REQUIRED" if preferred is None and all(
        value is not None for value in item["bounding_box_mm"].values()
    ) else "PROVISIONAL"

    return {
        "schema": "hutchfinity-item-class-map/v1",
        "item_class_id": item["item_class_id"],
        "item_class_hash": stable_hash(item),
        "preferred_sku": preferred_sku,
        "fallback_skus": fallback_skus,
        "selected_orientation": None if preferred is None else preferred["orientation"],
        "fit_margins_mm": None if preferred is None else preferred["wall_span_margins_mm"],
        "flat_floor_margins_mm": None if preferred is None else preferred["flat_floor_margins_mm"],
        "quantity_capacity": None if preferred is None else preferred["quantity_capacity"],
        "retrieval_clearance_mm": item["grab_clearance_mm"],
        "source_and_output_hashes": hashes,
        "validation_lane": None,
        "validation_receipt": None,
        "physical_fit_state": "not_run",
        "physical_fit_receipt": None,
        "selection_status": status,
        "rationale": rationale,
        "private_mapping_owner": "external/private",
        "candidate_evaluations": candidate_rows,
    }


def select_all(classes: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "hutchfinity-item-class-map-set/v1",
        "catalog_source_commit": catalog["source_commit"],
        "mappings": [select_item(item, catalog) for item in classes["items"]],
    }


def validate_sample_claim(receipt: dict[str, Any], item: dict[str, Any]) -> None:
    """Check only class-envelope consistency; this is not physical authentication."""
    for axis in ("x", "y", "z"):
        expected = item["bounding_box_mm"][axis]
        allowed_uncertainty = item["uncertainty_mm"][axis]
        if expected is None or allowed_uncertainty is None:
            raise ValueError(f"physical sample claim cannot bind unknown authoritative class axis: {axis}")
        observed = receipt["sample_dimensions_mm"][axis]
        observed_uncertainty = receipt["sample_uncertainty_mm"][axis]
        expected_low = expected - allowed_uncertainty
        expected_high = expected + allowed_uncertainty
        observed_low = observed - observed_uncertainty
        observed_high = observed + observed_uncertainty
        if observed_low < expected_low - 1e-9 or observed_high > expected_high + 1e-9:
            raise ValueError(f"physical sample claim falls outside the authoritative class envelope on axis {axis}")
    required_quantity = item["minimum_quantity_per_bin"] or 1
    if receipt["tested_quantity"] < required_quantity:
        raise ValueError("physical sample claim tested fewer than minimum_quantity_per_bin")


def lint_acceptance_claim(
    mapping: dict[str, Any],
    item: dict[str, Any],
    sku: dict[str, Any],
    receipts_dir: Path,
) -> None:
    """Lint caller assertions, then refuse to turn them into acceptance."""
    receipt_id = mapping["physical_fit_receipt"]
    receipt_path = receipts_dir / f"{receipt_id}.json"
    if not receipt_path.is_file():
        raise ValueError(f"physical-fit receipt does not exist: {receipt_path}")
    receipt = read_json(receipt_path)
    validate_schema(receipt, "physical-fit-receipt.schema.json", "physical-fit receipt")
    if receipt["receipt_id"] != receipt_id:
        raise ValueError("physical-fit receipt is not bound to its receipt ID")
    if receipt["item_class_id"] != item["item_class_id"] or receipt["item_class_hash"] != stable_hash(item):
        raise ValueError("physical-fit receipt is not bound to the authoritative item-class revision")
    if receipt["sku"] != sku["sku"] or receipt["result"] != "pass":
        raise ValueError("physical-fit receipt is not a passing claim for the authoritative selected SKU")
    if receipt["validation_lane"] != mapping["validation_lane"] or receipt["validation_receipt"] != mapping["validation_receipt"]:
        raise ValueError("physical-fit receipt is not consistent with the claimed validation lane receipt")
    artifact_hash = sku["output_hashes"][0]["sha256"]
    if receipt["artifact_sha256"] != artifact_hash:
        raise ValueError("physical-fit receipt is not bound to the authoritative artifact hash")
    if any(value != "pass" for value in receipt["checks"].values()):
        raise ValueError("physical-fit receipt must contain all passing physical checks")
    if receipt["workarounds"]:
        raise ValueError("a physical acceptance claim cannot depend on a workaround")
    validate_sample_claim(receipt, item)
    raise ValueError(
        "ACCEPTED is unavailable: local caller-controlled JSON is consistency evidence only; "
        "independently trusted physical and lane evidence is not configured"
    )


def validate_map_set(
    map_set: dict[str, Any],
    classes: dict[str, Any],
    catalog: dict[str, Any],
    receipts_dir: Path,
) -> None:
    validate_item_class_set(classes)
    validate_map_set_schema(map_set)
    validate_catalog_authority(catalog)

    authoritative_set = select_all(classes, catalog)
    if map_set["catalog_source_commit"] != catalog["source_commit"]:
        raise ValueError("item-class map set is not bound to the authoritative catalog commit")
    authoritative = {mapping["item_class_id"]: mapping for mapping in authoritative_set["mappings"]}
    supplied = {mapping["item_class_id"]: mapping for mapping in map_set["mappings"]}
    if set(supplied) != set(authoritative):
        raise ValueError("item-class map set does not exactly cover the authoritative item-class set")
    items = {item["item_class_id"]: item for item in classes["items"]}
    skus = {sku["sku"]: sku for sku in catalog["items"]}

    for item_class_id, mapping in supplied.items():
        expected = authoritative[item_class_id]
        if mapping["selection_status"] == "ACCEPTED":
            immutable_fields = set(expected) - ACCEPTANCE_FIELDS
            changed = sorted(field for field in immutable_fields if mapping[field] != expected[field])
            if changed:
                raise ValueError(f"acceptance claim changes authoritative mapping fields: {', '.join(changed)}")
            lint_acceptance_claim(mapping, items[item_class_id], skus[expected["preferred_sku"]], receipts_dir)
        elif mapping != expected:
            raise ValueError(f"mapping does not match authoritative generated selection: {item_class_id}")


def build_demand(
    map_set: dict[str, Any],
    requested: dict[str, Any],
    receipts_dir: Path,
    classes: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    validate_schema(requested, "demand-request.schema.json", "demand request")
    identifiers = [row["item_class_id"] for row in requested["artifact_demands"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("demand request contains duplicate item_class_id values")
    validate_map_set(map_set, classes, catalog, receipts_dir)
    mappings = {row["item_class_id"]: row for row in map_set["mappings"]}
    demands = []
    for request in requested["artifact_demands"]:
        if request["item_class_id"] not in mappings:
            raise ValueError(f"demand references an unknown item class: {request['item_class_id']}")
        mapping = mappings[request["item_class_id"]]
        if mapping["selection_status"] != "ACCEPTED":
            raise ValueError(f"demand requires an ACCEPTED mapping: {mapping['item_class_id']}")
        demands.append({
            "item_class_id": request["item_class_id"],
            "artifact_id_or_sku": mapping["preferred_sku"],
            "required_quantity": request["required_quantity"],
            "allowed_materials": request["allowed_materials"],
            "allowed_colors": request["allowed_colors"],
            "validation_lane": mapping["validation_lane"],
            "validation_receipt": mapping["validation_receipt"],
            "physical_fit_receipt": mapping["physical_fit_receipt"],
            "source_and_output_hashes": mapping["source_and_output_hashes"],
            "priority_class": request["priority_class"],
        })
    manifest = {
        "schema": "hutchfinity-demand-manifest/v1",
        "manifest_id": requested["manifest_id"],
        "as_of": requested["as_of"],
        "production_authorized": False,
        "artifact_demands": demands,
        "private_quantity_source_ref": "external/private; no content copied",
    }
    validate_schema(manifest, "demand-manifest.schema.json", "demand manifest")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build-catalog")
    build_parser.add_argument("--output", type=Path, required=True)
    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("--catalog", type=Path, required=True)
    select_parser.add_argument("--classes", type=Path, required=True)
    select_parser.add_argument("--output", type=Path, required=True)
    validate_parser = subparsers.add_parser("validate-maps")
    validate_parser.add_argument("--maps", type=Path, required=True)
    validate_parser.add_argument("--catalog", type=Path, required=True)
    validate_parser.add_argument("--classes", type=Path, required=True)
    validate_parser.add_argument("--receipts-dir", type=Path, required=True)
    demand_parser = subparsers.add_parser("build-demand")
    demand_parser.add_argument("--maps", type=Path, required=True)
    demand_parser.add_argument("--catalog", type=Path, required=True)
    demand_parser.add_argument("--classes", type=Path, required=True)
    demand_parser.add_argument("--request", type=Path, required=True)
    demand_parser.add_argument("--receipts-dir", type=Path, required=True)
    demand_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        if args.command == "build-catalog":
            result = build_catalog()
            validate_catalog_authority(result)
            write_json(args.output, result)
        elif args.command == "select":
            require_authoritative_path(args.catalog, AUTHORITATIVE_CATALOG, "catalog")
            require_authoritative_path(args.classes, AUTHORITATIVE_CLASSES, "item-class set")
            catalog = read_json(args.catalog)
            classes = read_json(args.classes)
            validate_item_class_set(classes)
            validate_catalog_authority(catalog)
            result = select_all(classes, catalog)
            validate_map_set_schema(result)
            write_json(args.output, result)
        elif args.command == "validate-maps":
            require_authoritative_path(args.catalog, AUTHORITATIVE_CATALOG, "catalog")
            require_authoritative_path(args.classes, AUTHORITATIVE_CLASSES, "item-class set")
            validate_map_set(
                read_json(args.maps), read_json(args.classes), read_json(args.catalog), args.receipts_dir,
            )
        elif args.command == "build-demand":
            require_authoritative_path(args.catalog, AUTHORITATIVE_CATALOG, "catalog")
            require_authoritative_path(args.classes, AUTHORITATIVE_CLASSES, "item-class set")
            result = build_demand(
                read_json(args.maps), read_json(args.request), args.receipts_dir,
                read_json(args.classes), read_json(args.catalog),
            )
            write_json(args.output, result)
    except (KeyError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
