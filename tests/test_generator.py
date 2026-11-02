"""Live tests for hutchfinity.py. These run the real OpenSCAD."""
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hutchfinity  # noqa: E402

try:
    hutchfinity.find_openscad()
    OPENSCAD_MISSING = None
except hutchfinity.BuildError as error:
    OPENSCAD_MISSING = str(error)
if OPENSCAD_MISSING:
    print(f"SKIPPED live generator tests: {OPENSCAD_MISSING}", file=sys.stderr)


@unittest.skipIf(OPENSCAD_MISSING, OPENSCAD_MISSING)
class LiveBuild(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out)

    def mesh(self, part, x, y, h, floor="integral-grid", **design):
        return hutchfinity.render(part, x, y, h, floor, design)

    def files(self, result):
        return sorted(p.name for p in Path(result["path"]).iterdir())

    def test_tub_heights_follow_the_bin(self):
        small = self.mesh("tub", 10, 10, 10)
        self.assertEqual(small["size_mm"][0], 214.4)
        self.assertEqual(small["size_mm"][2], 44.84)
        self.assertEqual(small["pieces"], 1)
        self.assertEqual(self.mesh("tub", 12, 16, 20)["size_mm"][2], 79.84)

    def test_both_floors_give_the_same_tub_height(self):
        self.assertEqual(self.mesh("tub", 10, 10, 10, "separate-grid")["size_mm"][2], 44.84)

    def test_options_reach_the_model(self):
        self.assertEqual(self.mesh("tub", 10, 10, 10, stack_gap=1.5)["size_mm"][2], 45.84)
        self.assertEqual(self.mesh("casing", 10, 10, 10, side_wall=20.0)["size_mm"][0], 256.4)
        self.assertLess(
            self.mesh("tub", 2, 2, 5, pull_guide=False)["facets"], self.mesh("tub", 2, 2, 5)["facets"])

    def test_one_pull_scales_down_on_small_tubs(self):
        for size in ((10, 10, 10), (12, 16, 20)):
            self.assertEqual(self.mesh("pull", *size)["size_mm"][:2], [90.0, 32.9])
        tiny = self.mesh("pull", 2, 2, 5)["size_mm"]
        self.assertLess(tiny[0], 40)
        self.assertAlmostEqual(tiny[0] / tiny[1], 90 / 32.9, delta=0.2)

    def test_regular_tub_mesh_stays_light(self):
        self.assertLess(self.mesh("tub", 12, 16, 20)["facets"], 60000)

    def test_module_is_always_complete(self):
        result = hutchfinity.build_module(10, 10, 10, "integral-grid", self.out)
        self.assertEqual(self.files(result), [
            "1-tub.3mf", "2-casing.3mf", "3-pegs-and-pull.3mf", "manifest.json"])
        folder = Path(result["path"])
        manifest = json.loads((folder / "manifest.json").read_text())
        self.assertEqual(manifest["peg_total"], 7)
        self.assertEqual(manifest["generator_version"], hutchfinity.VERSION)
        with zipfile.ZipFile(folder / "3-pegs-and-pull.3mf") as archive:
            model = archive.read("3D/3dmodel.model").decode()
        self.assertEqual(model.count("<object "), 2)
        self.assertEqual(model.count("<item "), 8)  # seven pegs and one pull

    def test_separate_grid_adds_the_grid(self):
        result = hutchfinity.build_module(2, 2, 5, "separate-grid", self.out)
        self.assertEqual(self.files(result), [
            "1-tub.3mf", "2-casing.3mf", "3-pegs-and-pull.3mf", "4-grid.3mf", "manifest.json"])

    def test_smallest_modules(self):
        hutchfinity.build_module(1, 1, 5, "integral-grid", self.out)
        with self.assertRaisesRegex(hutchfinity.BuildError, "at least 2 x 2"):
            hutchfinity.build_module(1, 1, 5, "separate-grid", self.out)

    def test_every_option_builds_at_both_ends_of_its_range(self):
        for name, _, _, _, low, high in hutchfinity.DESIGN_OPTIONS:
            for value in () if low is None else (low, high):
                with self.subTest(option=name, value=value):
                    design = {name: value}
                    for part, floor in (("tub", "integral-grid"), ("tub", "separate-grid"),
                                        ("grid-insert", "separate-grid"), ("casing", "integral-grid"),
                                        ("peg", "integral-grid"), ("pull", "integral-grid")):
                        self.mesh(part, 4, 4, 5, floor, **design)

    def test_narrowest_peg_spacing_adds_pegs(self):
        casing = self.mesh("casing", 10, 10, 10, peg_spacing=15.0)
        self.assertGreater(int(hutchfinity.re.search(r"(\d+) pegs", casing["notes"][0]).group(1)), 7)
        self.assertEqual(casing["pieces"], 1)

    def test_written_3mf_has_no_collapsed_triangles(self):
        result = hutchfinity.build_module(3, 3, 10, "separate-grid", self.out)
        for path in Path(result["path"]).glob("*.3mf"):
            with self.subTest(file=path.name), zipfile.ZipFile(path) as archive:
                model = archive.read("3D/3dmodel.model").decode()
                vertices = hutchfinity.re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', model)
                for a, b, c in hutchfinity.re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', model):
                    self.assertEqual(len({vertices[int(a)], vertices[int(b)], vertices[int(c)]}), 3)

    def test_cups_match_their_formula(self):
        for x, y, h in ((1, 1, 2), (1, 1, 5), (2, 4, 10), (5, 9, 5), (2, 2, 40)):
            with self.subTest(size=(x, y, h)):
                size = hutchfinity.render_cup(x, y, h)["size_mm"]
                for got, want in zip(size, (x * 21 - 0.5, y * 21 - 0.5, h * 3.5 + 3.74)):
                    self.assertAlmostEqual(got, want, delta=0.05)

    def test_cup_compartments_and_wall(self):
        plain = hutchfinity.render_cup(3, 3, 10)
        self.assertGreater(hutchfinity.render_cup(3, 3, 10, across=2, along=3)["facets"], plain["facets"])
        for wall in hutchfinity.CUP_WALL_RANGE:
            hutchfinity.render_cup(3, 3, 10, wall=wall)
        hutchfinity.render_cup(5, 5, 5, across=10, along=10)

    def test_cup_file(self):
        result = hutchfinity.build_cup(2, 4, 10, self.out, across=2)
        self.assertEqual(Path(result["path"]).name, "cup-2x4x10h-2x1-compartments.3mf")
        self.assertTrue(Path(result["path"]).is_file())

    def test_cups_fit_the_tub_grid_they_are_sized_for(self):
        tub = self.mesh("tub", 4, 4, 10)["size_mm"][2]
        cup = hutchfinity.render_cup(4, 4, 10)["size_mm"]
        self.assertLess(cup[2], tub)
        self.assertLess(cup[0], 4 * 21)


class Validation(unittest.TestCase):
    def test_rejects_bad_requests(self):
        out = Path(tempfile.gettempdir())
        for args, kwargs in (
            ((0, 5, 5, "integral-grid"), {}),
            ((41, 5, 5, "integral-grid"), {}),
            ((5, 5, 4, "integral-grid"), {}),
            ((5, 5, 41, "integral-grid"), {}),
            ((5, 5, 5, "plain"), {}),
            ((5, 5, 5, 'x";system("'), {}),
            ((5, 5, 5, "integral-grid"), {"design": {"wall": 0.1}}),
            ((5, 5, 5, "integral-grid"), {"design": {"peg_spacing": 14.0}}),
            ((5, 5, 5, "integral-grid"), {"design": {"not_an_option": 1}}),
        ):
            with self.subTest(args=args, kwargs=kwargs), self.assertRaises(hutchfinity.BuildError):
                hutchfinity.build_module(*args, out, **kwargs)

    def test_rejects_bad_cups(self):
        out = Path(tempfile.gettempdir())
        for args, kwargs, message in (
            ((0, 2, 5), {}, "cells wide"),
            ((2, 41, 5), {}, "cells deep"),
            ((2, 2, 1), {}, "height"),
            ((2, 2, 5), {"across": 11}, "across"),
            ((2, 2, 5), {"along": 0}, "along"),
            ((1, 1, 5), {"across": 3}, "at least 10"),
            ((2, 2, 5), {"wall": 0.1}, "wall"),
        ):
            with self.subTest(args=args, kwargs=kwargs), self.assertRaisesRegex(hutchfinity.BuildError, message):
                hutchfinity.build_cup(*args, out, **kwargs)


if __name__ == "__main__":
    unittest.main()
