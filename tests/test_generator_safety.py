"""Regression checks for output preservation, print settings and input handling."""
import contextlib
import errno
import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hutchfinity as generator
import print_settings

FIXTURE = ROOT / "tests" / "fixtures" / "process-export.json"


def tetrahedron():
    return {"points": [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)],
            "triangles": [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)],
            "low": [0, 0, 0], "size_mm": [1, 1, 1], "facets": 4,
            "closed": True, "pieces": 1, "notes": ["casing: example; 7 pegs"]}


class TemporaryOutput(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.out = Path(self.workspace.name)


class PrintSettings(TemporaryOutput):
    def test_export_without_type_and_only_explicit_allowed_settings(self):
        options = print_settings.load_print_options(FIXTURE)
        self.assertFalse(options.geometry_only)
        self.assertEqual(options.process["layer_height"], "0.2")
        self.assertEqual(options.inherits, "Example parent preset")
        self.assertNotIn("initial_layer_print_height", options.process)
        self.assertNotIn("initial_layer_line_width", options.process)
        self.assertNotIn("outer_wall_speed", options.process)
        self.assertNotIn("sparse_infill_line_width", options.process)

    def test_default_is_plain_geometry_with_recommendations(self):
        options = print_settings.print_options()
        self.assertTrue(options.geometry_only)
        record = print_settings.part_record("Peg", 7, options)
        self.assertEqual(record["applied_overrides"], {})
        self.assertEqual(record["recommended_overrides"]["sparse_infill_density"], "100%")
        with patch.object(generator, "render", return_value=tetrahedron()):
            result = generator.build_module(2, 2, 5, "integral-grid", self.out)
        folder = Path(result["path"])
        with zipfile.ZipFile(folder / "3-pegs-and-pull.3mf") as archive:
            self.assertNotIn("Metadata/model_settings.config", archive.namelist())
            xml = ET.fromstring(archive.read("3D/3dmodel.model"))
            self.assertEqual(len(xml.findall("{*}resources/{*}object")), 2)
            self.assertEqual(len(xml.findall("{*}build/{*}item")), 8)
        self.assertIn("Recommended, not embedded", (folder / "PRINTING.md").read_text())

    def test_rules_are_scoped_by_part(self):
        options = print_settings.load_print_options(FIXTURE, avoid_crossings=True)
        casing = print_settings.part_record("Casing", 1, options, 3.0)["applied_overrides"]
        tub = print_settings.part_record("Tub", 1, options, 1.3)["applied_overrides"]
        self.assertEqual(casing["sparse_infill_pattern"], "tpmsd")
        self.assertEqual(casing["bottom_shell_thickness"], "3")
        self.assertEqual(tub["sparse_infill_pattern"], "grid")
        self.assertEqual(tub["bottom_shell_thickness"], "1.3")
        self.assertEqual(casing["top_shell_layers"], "3")
        for part in ("Peg", "Pull"):
            applied = print_settings.part_record(part, 1, options)["applied_overrides"]
            self.assertEqual(applied["sparse_infill_density"], "100%")
            self.assertEqual(applied["sparse_infill_pattern"], "rectilinear")
            self.assertEqual(applied["fill_multiline"], "1")

    def test_each_physical_accessory_has_its_settings_and_name(self):
        options = print_settings.load_print_options(FIXTURE)
        with patch.object(generator, "render", return_value=tetrahedron()):
            result = generator.build_module(2, 2, 5, "integral-grid", self.out, printing=options)
        with zipfile.ZipFile(Path(result["path"]) / "3-pegs-and-pull.3mf") as archive:
            model = ET.fromstring(archive.read("3D/3dmodel.model"))
            settings = ET.fromstring(archive.read("Metadata/model_settings.config"))
            ids = {item.attrib["objectid"] for item in model.findall("{*}build/{*}item")}
            self.assertEqual(len(ids), 8)
            self.assertEqual(ids, {obj.attrib["id"] for obj in settings})
            names = []
            for obj in settings:
                values = {item.attrib["key"]: item.attrib["value"] for item in obj}
                names.append(values["name"])
                self.assertEqual(values["sparse_infill_density"], "100%")
                self.assertEqual(values["layer_height"], "0.2")
            self.assertEqual(names.count("Peg"), 7)
            self.assertEqual(names.count("Pull"), 1)

    def test_rejects_bundles_invalid_values_and_conflicting_modes(self):
        for profile in ({"type": "machine"}, {"type": "filament"},
                        {"type": "process", "printer_settings_id": "example"},
                        {"layer_height": "0.2"},
                        {"type": "process", "layer_height": "nan"},
                        {"type": "process", "sparse_infill_density": "101%"},
                        {"type": "process", "wall_loops": 1.5},
                        {"type": "process", "line_width": ["0.4"]}):
            with self.subTest(profile=profile), self.assertRaises(print_settings.PrintSettingsError):
                print_settings.print_options(profile)
        with self.assertRaises(print_settings.PrintSettingsError):
            print_settings.load_print_options(FIXTURE, geometry_only=True)
        with self.assertRaises(print_settings.PrintSettingsError):
            print_settings.print_options(avoid_crossings=True, geometry_only=True)


class OutputPreservation(TemporaryOutput):
    def previous(self):
        folder = self.out / "hutchfinity-2x2x5h-separate-grid"
        folder.mkdir()
        (folder / "1-tub.3mf").write_bytes(b"previous verified output")
        (folder / "manifest.json").write_text('{"previous": true}')
        return folder

    def test_late_grid_failure_preserves_previous_complete_job(self):
        folder = self.previous()
        def render(part, *args):
            if part == "grid-insert":
                raise generator.BuildError("grid failed")
            return tetrahedron()
        with patch.object(generator, "render", side_effect=render):
            with self.assertRaisesRegex(generator.BuildError, "grid failed"):
                generator.build_module(2, 2, 5, "separate-grid", self.out)
        self.assertEqual((folder / "1-tub.3mf").read_bytes(), b"previous verified output")
        self.assertEqual(json.loads((folder / "manifest.json").read_text()), {"previous": True})

    def test_write_failure_preserves_previous_job(self):
        folder = self.previous()
        with patch.object(generator, "render", return_value=tetrahedron()), \
                patch.object(generator, "write_3mf", side_effect=OSError("disk write failed")):
            with self.assertRaisesRegex(generator.BuildError, "disk write failed"):
                generator.build_module(2, 2, 5, "separate-grid", self.out)
        self.assertEqual((folder / "1-tub.3mf").read_bytes(), b"previous verified output")

    def test_failed_directory_promotion_restores_previous_job(self):
        folder = self.previous()
        original = Path.rename
        def rename(path, target):
            if path.name == "result" and target == folder:
                raise OSError("promotion failed")
            return original(path, target)
        with patch.object(generator, "render", return_value=tetrahedron()), patch.object(Path, "rename", rename):
            with self.assertRaisesRegex(generator.BuildError, "promotion failed"):
                generator.build_module(2, 2, 5, "separate-grid", self.out)
        self.assertEqual((folder / "1-tub.3mf").read_bytes(), b"previous verified output")

    def test_failed_rollback_retains_recoverable_previous_files(self):
        folder = self.previous()
        original = Path.rename
        def rename(path, target):
            if path.name in {"result", "previous"} and target == folder:
                raise OSError("destination unavailable")
            return original(path, target)
        with patch.object(generator, "render", return_value=tetrahedron()), patch.object(Path, "rename", rename):
            with self.assertRaisesRegex(generator.BuildError, "preserved for recovery"):
                generator.build_module(2, 2, 5, "separate-grid", self.out)
        recovery = list(self.out.glob(".hutchfinity-building-*/previous/1-tub.3mf"))
        self.assertEqual(len(recovery), 1)
        self.assertEqual(recovery[0].read_bytes(), b"previous verified output")

    def test_success_preserves_user_notes_and_emits_exact_file_hashes(self):
        folder = self.previous()
        (folder / "notes.txt").write_text("Keep this note")
        with patch.object(generator, "render", return_value=tetrahedron()):
            generator.build_module(2, 2, 5, "separate-grid", self.out)
        self.assertEqual((folder / "notes.txt").read_text(), "Keep this note")
        manifest = json.loads((folder / "manifest.json").read_text())
        self.assertIn("source_dirty", manifest)
        self.assertEqual(len(manifest["source_inputs_sha256"]), 64)
        for record in manifest["files"]:
            actual = generator.file_record(folder / record["file"])
            self.assertEqual(actual["sha256"], record["sha256"])

    def test_concurrent_writer_is_refused_without_changing_output(self):
        folder = self.previous()
        with generator.output_workspace(self.out), self.assertRaisesRegex(generator.BuildError, "Another build"):
            generator.build_module(2, 2, 5, "separate-grid", self.out)
        self.assertEqual((folder / "1-tub.3mf").read_bytes(), b"previous verified output")
        with generator.output_workspace(self.out):
            pass  # The failed writer did not leave a stale lock.

    def test_disconnected_part_is_not_published(self):
        mesh = tetrahedron()
        mesh["pieces"] = 2
        with patch.object(generator, "render", return_value=mesh), self.assertRaisesRegex(generator.BuildError, "2 pieces"):
            generator.build_module(2, 2, 5, "integral-grid", self.out)
        self.assertFalse((self.out / "hutchfinity-2x2x5h-integral-grid").exists())


class InputsAndMeshes(TemporaryOutput):
    def test_form_types_are_not_silently_coerced(self):
        base = {"x": "2", "y": "2", "h": "5"}
        size, _, design = generator.parse_form({**base, "pull_guide": True})
        self.assertEqual(size, [2, 2, 5])
        self.assertNotIn("pull_guide", design)
        for value in (True, 1.5, "1.5", [], None):
            with self.subTest(value=value), self.assertRaises(generator.BuildError):
                generator.parse_form({**base, "x": value})
        for value in ("nan", "inf", True, []):
            with self.subTest(value=value), self.assertRaises(generator.BuildError):
                generator.parse_form({**base, "riding_slab": value})

    def test_cli_options_without_dimensions_fail_instead_of_disappearing(self):
        for option in ("--avoid-crossings", "--plain-3mf", "--riding-slab=4", "module"):
            with self.subTest(option=option), patch.object(sys, "argv", ["hutchfinity.py", option]), \
                    patch.object(generator, "serve") as serve, contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as stopped:
                generator.main()
            self.assertEqual(stopped.exception.code, 2)
            serve.assert_not_called()

    def test_module_alias_calls_the_same_builder(self):
        with patch.object(sys, "argv", ["hutchfinity.py", "module", "2", "2", "5"]), \
                patch.object(generator, "build_module", return_value={}) as build, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(generator.main(), 0)
        self.assertEqual(build.call_args.args[:4], (2, 2, 5, "integral-grid"))

    def stl(self, faces):
        points = tetrahedron()["points"]
        data = bytearray(80) + struct.pack("<I", len(faces))
        for face in faces:
            coordinates = [value for index in face for value in points[index]]
            data.extend(struct.pack("<12fH", 0, 0, 0, *coordinates, 0))
        path = self.out / "mesh.stl"
        path.write_bytes(data)
        return path

    def test_rejects_truncated_empty_and_nonmanifold_meshes(self):
        for data in (b"", bytes(84)):
            path = self.out / "broken.stl"
            path.write_bytes(data)
            with self.assertRaises(generator.BuildError):
                generator.read_stl(path)
        faces = tetrahedron()["triangles"]
        self.assertTrue(generator.read_stl(self.stl(faces))["closed"])
        self.assertFalse(generator.read_stl(self.stl(faces * 2))["closed"])
        self.assertFalse(generator.read_stl(self.stl([(0, 1, 2), (0, 2, 1)]))["closed"])

    def test_small_real_triangles_survive_3mf_precision(self):
        mesh = tetrahedron()
        mesh["points"][1] = (0.00005, 0, 0)
        data = bytearray(80) + struct.pack("<I", 4)
        for face in mesh["triangles"]:
            coordinates = [value for index in face for value in mesh["points"][index]]
            data.extend(struct.pack("<12fH", 0, 0, 0, *coordinates, 0))
        stl = self.out / "thin.stl"
        stl.write_bytes(data)
        readback = generator.read_stl(stl)
        self.assertTrue(readback["closed"])
        self.assertEqual(readback["facets"], 4)
        target = self.out / "thin.3mf"
        generator.write_3mf(target, [("Thin triangle", readback, 1)])
        with zipfile.ZipFile(target) as archive:
            model = ET.fromstring(archive.read("3D/3dmodel.model"))
        vertices = model.findall("{*}resources/{*}object/{*}mesh/{*}vertices/{*}vertex")
        self.assertEqual(len({tuple(point.attrib.values()) for point in vertices}), 4)

    def test_indexed_3mf_retains_a_collinear_boundary_triangle(self):
        points = tetrahedron()["points"] + [(0.5, 0, 0)]
        # One side uses a split edge; the collinear face connects that split to
        # its neighbor. Deleting it produces three unpaired boundary edges.
        faces = [(0, 2, 1), (0, 4, 3), (4, 1, 3), (1, 2, 3), (2, 0, 3), (0, 1, 4)]
        mesh = generator.checked_mesh(points, faces)
        target = self.out / "indexed.3mf"
        generator.write_3mf(target, [("Indexed mesh", mesh, 1)])
        # Generated jobs carry a placement translation; native OpenSCAD output
        # has an identity placement. Remove only the fixture placement.
        with zipfile.ZipFile(target) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        model = ET.fromstring(files["3D/3dmodel.model"])
        model.find("{*}build/{*}item").attrib.pop("transform")
        files["3D/3dmodel.model"] = ET.tostring(model)
        with zipfile.ZipFile(target, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        restored = generator.read_3mf(target)
        self.assertEqual(restored["triangles"], faces)
        self.assertEqual(restored["facets"], 6)
        self.assertTrue(restored["closed"])
        self.assertEqual(restored["pieces"], 1)
        self.assertFalse(generator.checked_mesh(points, faces[:-1])["closed"])

    def test_indexed_mesh_rejects_bad_indices_open_and_zero_volume_surfaces(self):
        points = tetrahedron()["points"]
        with self.assertRaisesRegex(generator.BuildError, "triangle indices"):
            generator.checked_mesh(points, [(0, 1, 99)])
        with self.assertRaisesRegex(generator.BuildError, "non-finite"):
            generator.checked_mesh([(float("nan"), 0, 0), *points[1:]], tetrahedron()["triangles"])
        self.assertFalse(generator.checked_mesh(points, tetrahedron()["triangles"][:-1])["closed"])
        self.assertFalse(generator.checked_mesh(points[:3], [(0, 1, 2), (0, 2, 1)])["closed"])

    def test_auto_update_leaves_feature_branches_and_dirty_main_alone(self):
        for branch, dirty in (("feature\n", ""), ("main\n", " M hutchfinity.py\n")):
            answers = [generator.subprocess.CompletedProcess([], 0, branch, ""),
                       generator.subprocess.CompletedProcess([], 0, dirty, "")]
            with patch.object(generator.subprocess, "run", side_effect=answers) as run:
                generator.self_update()
            self.assertEqual(run.call_count, 2)

    def test_missing_git_has_truthful_source_provenance(self):
        with patch.object(generator.subprocess, "run", side_effect=FileNotFoundError):
            result = generator.source_provenance()
        self.assertEqual(result["source_commit"], "unknown")
        self.assertIsNone(result["source_dirty"])

    def test_reuses_only_a_matching_listener(self):
        occupied = OSError(errno.EADDRINUSE, "address in use")
        with patch.object(generator, "ThreadingHTTPServer", side_effect=occupied), \
                patch.object(generator, "matching_listener", return_value=True) as probe, \
                patch.object(generator.webbrowser, "open") as browser:
            self.assertEqual(generator.serve(self.out, 8421, True, False), 0)
        probe.assert_called_once_with(8421, self.out)
        browser.assert_called_once_with("http://127.0.0.1:8421/")
        with patch.object(generator, "ThreadingHTTPServer", side_effect=occupied), \
                patch.object(generator, "matching_listener", return_value=False), \
                patch.object(generator.webbrowser, "open") as browser, \
                self.assertRaisesRegex(generator.BuildError, "another --port"):
            generator.serve(self.out, 8421, True, False)
        browser.assert_not_called()

    def test_bind_permission_failure_is_not_reported_as_a_running_app(self):
        with patch.object(generator, "ThreadingHTTPServer", side_effect=OSError(errno.EACCES, "permission denied")), \
                patch.object(generator, "matching_listener") as probe, \
                self.assertRaisesRegex(generator.BuildError, "permission denied"):
            generator.serve(self.out, 8421, True, False)
        probe.assert_not_called()

    def test_listener_probe_checks_version_and_output_root(self):
        good = {"application": "hutchfinity", "version": generator.VERSION, "output": str(self.out.resolve())}
        for state, expected in ((good, True), ({**good, "version": "older"}, False),
                                ({**good, "output": "another-output"}, False), ({"application": "unrelated"}, False)):
            with self.subTest(state=state), patch.object(generator, "HTTPConnection") as connection:
                response = connection.return_value.getresponse.return_value
                response.status = 200
                response.read.return_value = json.dumps(state).encode()
                self.assertEqual(generator.matching_listener(8421, self.out), expected)
                connection.assert_called_once_with("127.0.0.1", 8421, timeout=1)
                connection.return_value.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
