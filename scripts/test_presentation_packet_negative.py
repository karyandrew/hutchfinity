#!/usr/bin/env python3
"""Negative fixtures proving the presentation packet fails closed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


SOURCE_COMMIT = "29273ab21605eba859088c18fd1bc50087d86709"


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, **kwargs)


def require_failure(result: subprocess.CompletedProcess[str], code: str) -> None:
    marker = f"FAIL {code}:"
    if result.returncode == 0 or marker not in result.stderr:
        raise RuntimeError(
            f"expected {marker}; rc={result.returncode}; "
            f"stdout={result.stdout!r}; stderr={result.stderr!r}"
        )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verifier_command(
    verifier: Path,
    manifest: Path,
    repo_root: Path,
    source_root: Path,
    packet_root: Path,
    output_root: Path,
) -> list[str]:
    return [
        "python3",
        str(verifier),
        "--manifest",
        str(manifest),
        "--repo-root",
        str(repo_root),
        "--source-root",
        str(source_root),
        "--packet-root",
        str(packet_root),
        "--output-root",
        str(output_root),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openscad", default=os.environ.get("OPENSCAD", "openscad"))
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    os.environ["GIT_WORK_TREE"] = str(repo_root)
    verifier = repo_root / "scripts/verify_presentation_packet.py"
    manifest = repo_root / "docs/presentation/hutchfinity-32-manifest.json"
    output_root = repo_root

    with tempfile.TemporaryDirectory(prefix="hutchfinity-32-negative-") as raw_temp:
        temp = Path(raw_temp)
        source_root = temp / "source"
        source_root.mkdir()
        archive = temp / "source.tar"
        subprocess.run(
            ["git", "-C", str(repo_root), "archive", "-o", str(archive), SOURCE_COMMIT],
            check=True,
        )
        subprocess.run(["tar", "-xf", str(archive), "-C", str(source_root)], check=True)
        presentation = source_root / "scad/presentation"
        presentation.mkdir(parents=True, exist_ok=True)
        for name in ("single-slot-hero.scad", "single-slot-exploded.scad"):
            shutil.copy2(repo_root / "scad/presentation" / name, presentation / name)

        base = verifier_command(
            verifier, manifest, repo_root, source_root, repo_root, output_root
        )

        # Fixture 1: a post-manifest mutation of a consumed pinned blob.
        casing = source_root / "scad/casing.scad"
        original_casing = casing.read_bytes()
        casing.write_bytes(original_casing + b"\n// negative fixture\n")
        result = run(base + ["--skip-packet-files", "--skip-outputs"])
        require_failure(result, "PINNED_SOURCE_SHA256_MISMATCH")
        casing.write_bytes(original_casing)

        # Fixture 2: execute the exploded caller with its knob omitted, then
        # prove the truth-ledger audit rejects the observed part inventory.
        missing_part_audit = temp / "missing-part.echo"
        result = run(
            [
                args.openscad,
                "--hardwarnings",
                "-D",
                "INCLUDE_KNOB=false",
                "-o",
                str(missing_part_audit),
                str(presentation / "single-slot-exploded.scad"),
            ]
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        audit_command = base + [
            "--audit-only",
            "--audit",
            f"single-slot-exploded={missing_part_audit}",
        ]
        require_failure(run(audit_command), "TRUTH_LEDGER_REQUIRED_PART_MISSING")

        # Fixture 3: each forbidden structure is a real solid appended to an
        # owned caller copy. Its changed mesh summary must fail the manifest
        # geometry audit even though all declared HF_PART echoes are unchanged.
        hero_source = presentation / "single-slot-hero.scad"
        forbidden_solids = {
            "front": "translate([0, -177, -95.24]) cube([308.4, 8, 95.24]);",
            "bottom": "translate([0, -169, -103.24]) cube([308.4, 534.9, 8]);",
            "rail": "translate([35, -160, -82]) cube([12, 500, 12]);",
        }
        pristine_hero = hero_source.read_text(encoding="utf-8")
        for forbidden, solid in forbidden_solids.items():
            changed_source = presentation / f"forbidden-{forbidden}.scad"
            changed_source.write_text(
                pristine_hero
                + f"\n// Owned negative fixture: actual forbidden {forbidden} solid.\n"
                + solid
                + "\n",
                encoding="utf-8",
            )
            changed_summary = temp / f"forbidden-{forbidden}.json"
            changed_mesh = temp / f"forbidden-{forbidden}.stl"
            result = run(
                [
                    args.openscad,
                    "--hardwarnings",
                    "--render",
                    "--backend",
                    "Manifold",
                    "--summary",
                    "all",
                    "--summary-file",
                    str(changed_summary),
                    "-o",
                    str(changed_mesh),
                    str(changed_source),
                ]
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
            require_failure(
                run(
                    base
                    + [
                        "--audit-only",
                        "--summary",
                        f"single-slot-hero={changed_summary}",
                    ]
                ),
                "GEOMETRY_SUMMARY_MISMATCH",
            )

        scale_audit = temp / "reject-scale.echo"
        run(
            [
                args.openscad,
                "--hardwarnings",
                "-D",
                "PRODUCT_SCALE=1.01",
                "-o",
                str(scale_audit),
                str(hero_source),
            ]
        )
        if "HF_HARD_REJECT:SCALE_CHANGED" not in scale_audit.read_text(
            encoding="utf-8", errors="replace"
        ):
            raise RuntimeError("non-unit scale was not rejected")

        # Fixture 4: an imported source outside the exact per-scene allowlist
        # is observed in OpenSCAD's dependency output and rejected.
        hero_source.write_text(pristine_hero + "\nuse <../peg.scad>;\n", encoding="utf-8")
        injected_audit = temp / "unmanifested-dependency.echo"
        injected_deps = temp / "unmanifested-dependency.deps"
        result = run(
            [
                args.openscad,
                "--hardwarnings",
                "-d",
                str(injected_deps),
                "-o",
                str(injected_audit),
                str(hero_source),
            ]
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        require_failure(
            run(
                base
                + [
                    "--audit-only",
                    "--dependencies",
                    f"single-slot-hero={injected_deps}",
                ]
            ),
            "DEPENDENCY_SET_MISMATCH",
        )
        hero_source.write_text(pristine_hero, encoding="utf-8")

        # Fixture 5: draft PR #31 and uncommitted #29 cannot enter the list of
        # current geometry inputs.
        base_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        for label in ("draft PR #31", "uncommitted #29 geometry"):
            changed_manifest = json.loads(json.dumps(base_manifest))
            changed_manifest["provenance"]["current_geometry_inputs"].append(label)
            changed_path = temp / (label.replace(" ", "-").replace("#", "") + ".json")
            changed_path.write_text(json.dumps(changed_manifest), encoding="utf-8")
            command = verifier_command(
                verifier, changed_path, repo_root, source_root, repo_root, output_root
            )
            require_failure(run(command + ["--skip-outputs"]), "PROVENANCE_FORBIDDEN_INPUT")

        # Fixture 6: a genuinely clipped camera render fails the minimum-margin
        # gate after its own dimensions, digest, and observed bounds are bound.
        clipped_outputs = temp / "clipped-outputs"
        shutil.copytree(repo_root / "preview", clipped_outputs / "preview")
        clipped_hero = clipped_outputs / "preview/issue-32/single-slot-hero.png"
        result = run(
            [
                args.openscad,
                "--hardwarnings",
                "--render",
                "--backend",
                "Manifold",
                "--projection",
                "p",
                "--camera",
                "850,-900,500,154,70,-50",
                "--imgsize",
                "2048,2048",
                "--colorscheme",
                "Tomorrow",
                "-o",
                str(clipped_hero),
                str(hero_source),
            ]
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        clipped_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        clipped_scene = next(
            scene for scene in clipped_manifest["scenes"] if scene["id"] == "single-slot-hero"
        )
        clipped_scene["output"]["sha256"] = sha256_file(clipped_hero)
        clipped_scene["image_margin"]["foreground_bounds_inclusive"] = [37, 431, 2047, 1699]
        clipped_scene["image_margin"]["margins_left_top_right_bottom"] = [37, 431, 0, 348]
        clipped_manifest_path = temp / "clipped-manifest.json"
        clipped_manifest_path.write_text(json.dumps(clipped_manifest), encoding="utf-8")
        clipped_command = verifier_command(
            verifier,
            clipped_manifest_path,
            repo_root,
            source_root,
            repo_root,
            clipped_outputs,
        )
        require_failure(
            run(clipped_command + ["--skip-packet-files"]),
            "OUTPUT_MARGIN_TOO_SMALL",
        )

        # Fixture 7a: missing output.
        fixture_outputs = temp / "outputs"
        shutil.copytree(repo_root / "preview", fixture_outputs / "preview")
        hero_output = fixture_outputs / "preview/issue-32/single-slot-hero.png"
        hero_original = hero_output.read_bytes()
        hero_output.unlink()
        command = verifier_command(
            verifier, manifest, repo_root, source_root, repo_root, fixture_outputs
        )
        require_failure(run(command), "OUTPUT_MISSING")

        # Fixture 7b: digest mismatch with a still-parseable PNG.
        hero_output.write_bytes(hero_original + b"negative-fixture")
        require_failure(run(command), "OUTPUT_SHA256_MISMATCH")

    print(
        "PASS 12 negative cases: blob, part, actual front/bottom/rail geometry, "
        "scale, dependency allowlist, provenance x2, clipped margin, missing output, "
        "digest mismatch"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
