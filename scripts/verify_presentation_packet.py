#!/usr/bin/env python3
"""Fail-closed verifier for the deterministic Hutchfinity presentation packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import zlib
from collections import Counter
from pathlib import Path


EXPECTED_SOURCE_COMMIT = "29273ab21605eba859088c18fd1bc50087d86709"
FORBIDDEN_CURRENT_INPUTS = (
    re.compile(r"(?:pull|pr)\s*#?31", re.IGNORECASE),
    re.compile(r"(?:issue\s*)?#29", re.IGNORECASE),
    re.compile(r"uncommitted.*(?:geometry|source)", re.IGNORECASE),
)


class VerificationFailure(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def fail(code: str, detail: str) -> None:
    raise VerificationFailure(code, detail)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob(repo_root: Path, commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", f"{commit}:{path}"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        fail("PROVENANCE_BLOB_UNRESOLVED", f"{path}: {result.stderr.strip()}")
    return result.stdout.strip()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        fail("OUTPUT_NOT_PNG", str(path))
    return struct.unpack(">II", header[16:24])


def png_content_bounds(
    path: Path, background: tuple[int, int, int], tolerance: int
) -> tuple[list[int], list[int]]:
    """Return inclusive foreground bounds and L/T/R/B margins for an RGB PNG."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail("OUTPUT_NOT_PNG", str(path))
    offset = 8
    width = height = 0
    compressed = bytearray()
    bit_depth = color_type = interlace = -1
    while offset < len(data):
        if offset + 12 > len(data):
            fail("OUTPUT_PNG_INVALID", f"truncated chunk in {path}")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break
    if bit_depth != 8 or color_type != 2 or interlace != 0:
        fail(
            "OUTPUT_PNG_UNSUPPORTED",
            f"{path}: expected non-interlaced 8-bit RGB, got depth={bit_depth}, "
            f"color_type={color_type}, interlace={interlace}",
        )
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error as exc:
        fail("OUTPUT_PNG_INVALID", f"{path}: {exc}")
    bytes_per_pixel = 3
    stride = width * bytes_per_pixel
    expected_size = height * (stride + 1)
    if len(raw) != expected_size:
        fail(
            "OUTPUT_PNG_INVALID",
            f"{path}: expected {expected_size} decoded bytes, got {len(raw)}",
        )
    previous = bytearray(stride)
    min_x, min_y, max_x, max_y = width, height, -1, -1
    cursor = 0
    for y in range(height):
        filter_type = raw[cursor]
        cursor += 1
        encoded = raw[cursor : cursor + stride]
        cursor += stride
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            up = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = (value + left) & 0xFF
            elif filter_type == 2:
                decoded = (value + up) & 0xFF
            elif filter_type == 3:
                decoded = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                predictor = left + up - upper_left
                pa = abs(predictor - left)
                pb = abs(predictor - up)
                pc = abs(predictor - upper_left)
                nearest = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                decoded = (value + nearest) & 0xFF
            else:
                fail("OUTPUT_PNG_INVALID", f"{path}: unknown filter {filter_type}")
            row[index] = decoded
        for x in range(width):
            start = x * bytes_per_pixel
            pixel = row[start : start + bytes_per_pixel]
            if any(abs(pixel[channel] - background[channel]) > tolerance for channel in range(3)):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        previous = row
    if max_x < 0:
        fail("OUTPUT_FOREGROUND_MISSING", str(path))
    bounds = [min_x, min_y, max_x, max_y]
    margins = [min_x, min_y, width - 1 - max_x, height - 1 - max_y]
    return bounds, margins


def parse_audit(path: Path, scene_id: str) -> Counter[str]:
    if not path.is_file():
        fail("SCENE_AUDIT_MISSING", f"{scene_id}: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if "ERROR:" in text or "WARNING:" in text:
        fail("SCENE_AUDIT_OPENSCAD_ERROR", f"{scene_id}: {path}")
    if f'HF_SCENE|{scene_id}' not in text:
        fail("SCENE_AUDIT_ID_MISMATCH", f"expected {scene_id} in {path}")
    if "HF_META|product_scale|1" not in text:
        fail("HARD_REJECT_SCALE_CHANGED", scene_id)
    parts: Counter[str] = Counter()
    for name, amount in re.findall(r"HF_PART\|([a-z-]+)\|([0-9]+)", text):
        parts[name] += int(amount)
    return parts


def read_manifest(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail("MANIFEST_UNREADABLE", str(exc))
    if not isinstance(value, dict):
        fail("MANIFEST_INVALID", "root must be an object")
    return value


def parse_scene_path_args(values: list[str], label: str) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            fail("ARGUMENT_INVALID", f"{label} must be SCENE=PATH: {value}")
        scene, raw_path = value.split("=", 1)
        paths[scene] = Path(raw_path).resolve()
    return paths


def parse_geometry_summary(path: Path, scene_id: str) -> dict:
    if not path.is_file():
        fail("GEOMETRY_SUMMARY_MISSING", f"{scene_id}: {path}")
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
        geometry = summary["geometry"]
        bounds = geometry["bounding_box"]
        return {
            "simple": geometry["simple"],
            "vertices": geometry["vertices"],
            "facets": geometry["facets"],
            "bounding_box_min": bounds["min"],
            "bounding_box_max": bounds["max"],
        }
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        fail("GEOMETRY_SUMMARY_INVALID", f"{scene_id}: {exc}")


def geometry_matches(observed: dict, expected: dict) -> bool:
    if observed["simple"] != expected["simple"]:
        return False
    if observed["vertices"] != expected["vertices"] or observed["facets"] != expected["facets"]:
        return False
    for key in ("bounding_box_min", "bounding_box_max"):
        if len(observed[key]) != len(expected[key]):
            return False
        if any(abs(float(a) - float(b)) > 1e-6 for a, b in zip(observed[key], expected[key])):
            return False
    return True


def parse_dependencies(path: Path, source_root: Path, scene_id: str) -> set[str]:
    if not path.is_file():
        fail("DEPENDENCY_FILE_MISSING", f"{scene_id}: {path}")
    text = path.read_text(encoding="utf-8", errors="strict").replace("\\\n", " ")
    if ":" not in text:
        fail("DEPENDENCY_FILE_INVALID", f"{scene_id}: {path}")
    dependencies: set[str] = set()
    for raw_path in text.split(":", 1)[1].split():
        dependency = Path(raw_path.replace("\\ ", " ")).resolve()
        try:
            relative = dependency.relative_to(source_root)
        except ValueError:
            fail("DEPENDENCY_OUTSIDE_SOURCE_ROOT", f"{scene_id}: {dependency}")
        dependencies.add(relative.as_posix())
    return dependencies


def verify(args: argparse.Namespace) -> None:
    manifest = read_manifest(args.manifest.resolve())
    source_commit = manifest.get("source_commit")
    if source_commit != EXPECTED_SOURCE_COMMIT:
        fail(
            "PROVENANCE_SOURCE_COMMIT_MISMATCH",
            f"expected {EXPECTED_SOURCE_COMMIT}, got {source_commit}",
        )

    current_inputs = manifest.get("provenance", {}).get("current_geometry_inputs", [])
    if not isinstance(current_inputs, list):
        fail("MANIFEST_INVALID", "provenance.current_geometry_inputs must be a list")
    for current_input in current_inputs:
        value = str(current_input)
        if any(pattern.search(value) for pattern in FORBIDDEN_CURRENT_INPUTS):
            fail("PROVENANCE_FORBIDDEN_INPUT", value)

    repo_root = args.repo_root.resolve()
    source_root = args.source_root.resolve()
    packet_root = args.packet_root.resolve()
    output_root = args.output_root.resolve()

    if not args.audit_only:
        resolved_commit = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", f"{source_commit}^{{commit}}"],
            check=False,
            text=True,
            capture_output=True,
        )
        if resolved_commit.returncode != 0 or resolved_commit.stdout.strip() != source_commit:
            fail("PROVENANCE_PIN_UNAVAILABLE", source_commit)

        for entry in manifest.get("consumed_blobs", []):
            path = entry["path"]
            actual_blob = git_blob(repo_root, source_commit, path)
            if actual_blob != entry["git_blob"]:
                fail("PINNED_GIT_BLOB_MISMATCH", path)
            source_path = source_root / path
            if not source_path.is_file():
                fail("PINNED_SOURCE_MISSING", path)
            if sha256_file(source_path) != entry["sha256"]:
                fail("PINNED_SOURCE_SHA256_MISMATCH", path)

        if not args.skip_packet_files:
            for entry in manifest.get("packet_files", []):
                path = packet_root / entry["path"]
                if not path.is_file():
                    fail("PACKET_FILE_MISSING", entry["path"])
                if sha256_file(path) != entry["sha256"]:
                    fail("PACKET_FILE_SHA256_MISMATCH", entry["path"])

        if not args.skip_outputs:
            for scene in manifest.get("scenes", []):
                output = scene["output"]
                path = output_root / output["path"]
                if not path.is_file():
                    fail("OUTPUT_MISSING", output["path"])
                actual_dimensions = png_dimensions(path)
                expected_dimensions = tuple(output["dimensions"])
                if actual_dimensions != expected_dimensions:
                    fail(
                        "OUTPUT_DIMENSIONS_MISMATCH",
                        f"{output['path']}: expected {expected_dimensions}, got {actual_dimensions}",
                    )
                if sha256_file(path) != output["sha256"]:
                    fail("OUTPUT_SHA256_MISMATCH", output["path"])

                margin = scene.get("image_margin")
                if not isinstance(margin, dict):
                    fail("MANIFEST_INVALID", f"{scene['id']}: image_margin missing")
                background = tuple(margin.get("background_rgb", []))
                if len(background) != 3:
                    fail("MANIFEST_INVALID", f"{scene['id']}: background_rgb")
                bounds, margins = png_content_bounds(
                    path,
                    tuple(int(value) for value in background),
                    int(margin["background_tolerance"]),
                )
                if bounds != margin.get("foreground_bounds_inclusive") or margins != margin.get(
                    "margins_left_top_right_bottom"
                ):
                    fail(
                        "OUTPUT_CONTENT_BOUNDS_MISMATCH",
                        f"{scene['id']}: bounds={bounds}, margins={margins}",
                    )
                minimum_fraction = float(margin["minimum_margin_fraction"])
                minimum_x = math.ceil(actual_dimensions[0] * minimum_fraction)
                minimum_y = math.ceil(actual_dimensions[1] * minimum_fraction)
                if margins[0] < minimum_x or margins[2] < minimum_x or margins[1] < minimum_y or margins[3] < minimum_y:
                    fail(
                        "OUTPUT_MARGIN_TOO_SMALL",
                        f"{scene['id']}: required x>={minimum_x}, y>={minimum_y}; "
                        f"observed L/T/R/B={margins}",
                    )

    scene_by_id = {scene["id"]: scene for scene in manifest.get("scenes", [])}
    audits = parse_scene_path_args(args.audit, "audit")
    for scene_id, audit_path in audits.items():
        if scene_id not in scene_by_id:
            fail("SCENE_UNKNOWN", scene_id)
        observed = parse_audit(audit_path, scene_id)
        required = Counter(scene_by_id[scene_id]["required_parts"])
        if observed != required:
            fail(
                "TRUTH_LEDGER_REQUIRED_PART_MISSING",
                f"{scene_id}: expected {dict(required)}, observed {dict(observed)}",
            )

    summaries = parse_scene_path_args(args.summary, "summary")
    for scene_id, summary_path in summaries.items():
        if scene_id not in scene_by_id:
            fail("SCENE_UNKNOWN", scene_id)
        observed = parse_geometry_summary(summary_path, scene_id)
        expected = scene_by_id[scene_id]["geometry_summary"]
        if not geometry_matches(observed, expected):
            fail(
                "GEOMETRY_SUMMARY_MISMATCH",
                f"{scene_id}: expected {expected}, observed {observed}",
            )

    dependencies = parse_scene_path_args(args.dependencies, "dependencies")
    for scene_id, dependency_path in dependencies.items():
        if scene_id not in scene_by_id:
            fail("SCENE_UNKNOWN", scene_id)
        observed = parse_dependencies(dependency_path, source_root, scene_id)
        expected = set(scene_by_id[scene_id]["render_dependencies"])
        if observed != expected:
            fail(
                "DEPENDENCY_SET_MISMATCH",
                f"{scene_id}: expected {sorted(expected)}, observed {sorted(observed)}",
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--audit", action="append", default=[])
    parser.add_argument("--summary", action="append", default=[])
    parser.add_argument("--dependencies", action="append", default=[])
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--skip-packet-files", action="store_true")
    parser.add_argument("--skip-outputs", action="store_true")
    args = parser.parse_args()
    try:
        verify(args)
    except VerificationFailure as exc:
        print(f"FAIL {exc.code}: {exc.detail}", file=sys.stderr)
        return 1
    print("PASS presentation packet verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
