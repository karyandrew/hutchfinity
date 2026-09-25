#!/usr/bin/env python3
import json
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
AUDIT = HERE / "mesh_audit.py"
SPEC = importlib.util.spec_from_file_location("mesh_audit", AUDIT)
MESH_AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MESH_AUDIT)

MANIFEST_SPEC = importlib.util.spec_from_file_location("run_manifest", HERE / "run_manifest.py")
RUN_MANIFEST = importlib.util.module_from_spec(MANIFEST_SPEC)
MANIFEST_SPEC.loader.exec_module(RUN_MANIFEST)

TETRA = """solid tetra
facet normal 0 0 -1
 outer loop
  vertex 0 0 0
  vertex 0 1 0
  vertex 1 0 0
 endloop
endfacet
facet normal 0 -1 0
 outer loop
  vertex 0 0 0
  vertex 1 0 0
  vertex 0 0 1
 endloop
endfacet
facet normal 1 1 1
 outer loop
  vertex 1 0 0
  vertex 0 1 0
  vertex 0 0 1
 endloop
endfacet
facet normal -1 0 0
 outer loop
  vertex 0 1 0
  vertex 0 0 0
  vertex 0 0 1
 endloop
endfacet
endsolid tetra
"""


def box_triangles(lo, hi, inward=False):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    p = {
        "000": (x0, y0, z0), "100": (x1, y0, z0),
        "010": (x0, y1, z0), "110": (x1, y1, z0),
        "001": (x0, y0, z1), "101": (x1, y0, z1),
        "011": (x0, y1, z1), "111": (x1, y1, z1),
    }
    faces = [
        ("000", "010", "110"), ("000", "110", "100"),
        ("001", "101", "111"), ("001", "111", "011"),
        ("000", "100", "101"), ("000", "101", "001"),
        ("010", "011", "111"), ("010", "111", "110"),
        ("000", "001", "011"), ("000", "011", "010"),
        ("100", "110", "111"), ("100", "111", "101"),
    ]
    result = [tuple(p[key] for key in face) for face in faces]
    return [tuple(reversed(tri)) for tri in result] if inward else result


def write_ascii_stl(path, triangles):
    lines = ["solid fixture"]
    for tri in triangles:
        lines.extend(["facet normal 0 0 0", " outer loop"])
        lines.extend(f"  vertex {x} {y} {z}" for x, y, z in tri)
        lines.extend([" endloop", "endfacet"])
    lines.append("endsolid fixture")
    path.write_text("\n".join(lines) + "\n")


def interface_fixture(path, inset=2.5):
    triangles = box_triangles((0, 0, 0), (21, 21, 4))
    triangles += box_triangles((inset, inset, 0), (21-inset, 21-inset, 4), inward=True)
    write_ascii_stl(path, triangles)

class MeshAuditTest(unittest.TestCase):
    def test_point_triangle_distance(self):
        tri=((0,0,0),(1,0,0),(0,1,0))
        self.assertAlmostEqual(MESH_AUDIT.point_triangle_distance((0.25,0.25,1),tri),1)
        self.assertAlmostEqual(MESH_AUDIT.point_triangle_distance((0.25,0.25,0),tri),0)
        degenerate=((0,0,0),(1,0,0),(1,0,0))
        self.assertAlmostEqual(MESH_AUDIT.point_triangle_distance((0.5,1,0),degenerate),1)

    def test_ascii_audit(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"tetra.stl"; path.write_text(TETRA)
            out=subprocess.check_output(["python3",str(AUDIT),"analyze",str(path)],text=True)
            result=json.loads(out)
            self.assertEqual(result["facets"],4)
            self.assertEqual(result["components"],1)
            self.assertTrue(result["manifold_or_watertight"])
            self.assertTrue(result["consistently_oriented"])
            self.assertEqual(result["euler_characteristic"], 2)
            self.assertEqual(result["genus"], 0)
            self.assertEqual(result["bounds_mm"],[[0.0,0.0,0.0],[1.0,1.0,1.0]])

    def test_contact_partition_and_horizontal_sampling(self):
        tris = box_triangles((2.5, 2.5, 0), (18.5, 18.5, 4), inward=True)
        bounds = [[0, 0, 0], [21, 21, 4]]
        cells = MESH_AUDIT.contact_cells(tris, bounds)
        self.assertEqual(list(cells), [(0, 0)])
        self.assertEqual(len(cells[(0, 0)]), 8)
        horizontal = MESH_AUDIT.horizontal_interface_triangles(tris, (10.5, 10.5))
        samples = MESH_AUDIT.horizontal_interface_samples(horizontal, (10.5, 10.5))
        self.assertTrue(samples)
        self.assertTrue(all(
            MESH_AUDIT.CONTACT_EXTENT_MIN_MM <= max(abs(x-10.5), abs(y-10.5)) <= MESH_AUDIT.CONTACT_EXTENT_MAX_MM
            for x, y, _ in samples
        ))

    def test_repeated_pockets_are_sampled_without_claiming_identity(self):
        first = box_triangles((2.5, 2.5, 0), (18.5, 18.5, 4), inward=True)
        second = box_triangles((23.5, 2.5, 0), (39.5, 18.5, 4), inward=True)
        bounds = [[0, 0, 0], [42, 21, 4]]
        cells = MESH_AUDIT.contact_cells(first + second, bounds)
        result = MESH_AUDIT.repetition(cells, bounds)
        self.assertEqual(result["cells"], 2)
        self.assertTrue(result["repeated_vertex_centroids_within_tolerance"])
        self.assertAlmostEqual(result["max_repeated_vertex_centroid_delta_mm"], 0)
        self.assertFalse(result["identity_proved"])

    def test_orientation_is_part_of_topology_audit(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad-orientation.stl"
            tris = box_triangles((0, 0, 0), (1, 1, 1))
            tris[0] = tuple(reversed(tris[0]))
            write_ascii_stl(path, tris)
            result = MESH_AUDIT.audit(path)
            self.assertTrue(result["manifold_or_watertight"])
            self.assertFalse(result["consistently_oriented"])
            self.assertIsNone(result["genus"])

    def test_all_z_sampling_covers_each_slab_without_claiming_a_bound(self):
        baseline = box_triangles((2.5, 2.5, 0), (18.5, 18.5, 4), inward=True)
        candidate = box_triangles((2.52, 2.52, 0), (18.48, 18.48, 4), inward=True)
        result = MESH_AUDIT.all_z_section_comparison(baseline, candidate)
        self.assertGreater(result["sampled_sections"], 4)
        self.assertLessEqual(result["max_section_spacing_mm"], MESH_AUDIT.ALL_Z_MAX_STEP_MM + 1e-9)
        self.assertAlmostEqual(result["max_sampled_section_datum_delta_mm"], 0.04)
        self.assertFalse(result["continuous_all_z_bound_proved"])

    def test_compare_known_pass_and_fail_fixtures(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = Path(d) / "baseline.stl"
            same = Path(d) / "same.stl"
            changed = Path(d) / "changed.stl"
            interface_fixture(baseline)
            interface_fixture(same)
            interface_fixture(changed, inset=2.6)
            passing = MESH_AUDIT.compare(baseline, same)
            failing = MESH_AUDIT.compare(baseline, changed)
            self.assertTrue(passing["narrow_sampled_contact_and_datum_check_pass"])
            self.assertTrue(passing["enhanced_sampled_diagnostics_pass"])
            self.assertFalse(failing["narrow_sampled_contact_and_datum_check_pass"])
            self.assertFalse(failing["enhanced_sampled_diagnostics_pass"])
            for result in (passing, failing):
                self.assertFalse(result["bounded_surface_check_pass"])
                self.assertNotIn("contact_contour_upper_bound_mm", result)
                self.assertFalse(result["baseline_repetition"]["identity_proved"])

    def test_manifest_assembles_all_classes_and_candidate_comparisons(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            matrix = root / "matrix.tsv"
            matrix.write_text("id\tfn\tfa\tfs\ncurrent\t0\t6\t0.1\nfine\t0\t8\t0.15\n")
            for row in ("current", "fine"):
                directory = root / row
                directory.mkdir()
                for artifact in RUN_MANIFEST.DIMENSIONS:
                    audit = {
                        "sha256": f"{row}-{artifact}", "bytes": 10, "facets": 4,
                        "components": 1, "manifold_or_watertight": True,
                        "consistently_oriented": True, "euler_characteristic": 2, "genus": 0,
                        "bounds_mm": [[0, 0, 0], [1, 1, 1]],
                    }
                    (directory / f"baseplate-{artifact}.audit.json").write_text(json.dumps(audit))
                    (directory / f"baseplate-{artifact}.time").write_text("real 1.0\nuser 0.8\nsys 0.2\n")
                    (directory / f"baseplate-{artifact}.stderr").write_text("Total rendering time: 0:00:00.500\n")
                    if row == "fine":
                        (directory / f"baseplate-{artifact}.compare.json").write_text('{"bounded_surface_check_pass": false}')
            command = [
                "python3", str(HERE / "run_manifest.py"), "--output", str(root),
                "--commit", "abc", "--version", "OpenSCAD fixture", "--arch", "fixture",
                "--backend", "Manifold", "--canonical-vendor-hash", "vendor",
                "--render-source-hash", "vendor", "--build-script-hash", "build",
                "--matrix-hash", "matrix", "--openscad-command-hash", "openscad",
                "--runner-hash", "runner", "--audit-hash", "audit",
                "--manifest-hash", "manifest", "--matrix", str(matrix),
            ]
            manifest = json.loads(subprocess.check_output(command, text=True))
            self.assertTrue(manifest["render_source_matches_vendor"])
            self.assertEqual(len(manifest["variants"]), 3)
            self.assertEqual(set(manifest["candidates"][0]["comparisons"]), set(RUN_MANIFEST.DIMENSIONS))
            self.assertFalse(manifest["production_fit"])

    def test_renderer_timing_rejects_negative_wall_clock(self):
        with tempfile.TemporaryDirectory() as d:
            time_path = Path(d) / "render.time"
            stderr_path = Path(d) / "render.stderr"
            time_path.write_text("real -1.73\nuser 1.54\nsys 0.77\n")
            stderr_path.write_text("Total rendering time: 0:00:00.673\n")
            result = RUN_MANIFEST.timing(time_path, stderr_path)
            self.assertEqual(result["render_seconds"], 0.673)
            self.assertIsNone(result["process_wall_seconds"])

if __name__ == "__main__": unittest.main()
