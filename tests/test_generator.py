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

    def test_tub_heights_follow_the_bin(self):
        small = self.mesh("tub", 10, 10, 10)
        self.assertEqual(small["size_mm"][0], 214.4)
        self.assertEqual(small["size_mm"][2], 44.84)
        self.assertEqual(small["pieces"], 1)
        self.assertEqual(self.mesh("tub", 12, 16, 20)["size_mm"][2], 79.84)
        self.assertEqual(self.mesh("tub", 10, 10, 10, "plain")["size_mm"][2], 44.74)

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

    def test_module_is_a_set_of_3mf_files(self):
        result = hutchfinity.build("module", 10, 10, 10, "integral-grid", self.out)
        folder = Path(result["path"])
        self.assertEqual(
            sorted(p.name for p in folder.iterdir()),
            ["1-tub.3mf", "2-casing.3mf", "3-pegs-and-pulls.3mf", "manifest.json"])
        manifest = json.loads((folder / "manifest.json").read_text())
        self.assertEqual(manifest["peg_total"], 7)
        self.assertEqual(manifest["generator_version"], hutchfinity.VERSION)
        with zipfile.ZipFile(folder / "3-pegs-and-pulls.3mf") as archive:
            model = archive.read("3D/3dmodel.model").decode()
        self.assertEqual(model.count("<object "), 2)
        self.assertEqual(model.count("<item "), 8)  # seven pegs and one pull

    def test_smallest_module_builds(self):
        hutchfinity.build("module", 1, 1, 5, "plain", self.out)
        hutchfinity.build("module", 2, 2, 5, "plain", self.out, counts={"insert": 1})
        with self.assertRaisesRegex(hutchfinity.BuildError, "at least 2 x 2"):
            hutchfinity.build("module", 1, 1, 5, "plain", self.out, counts={"insert": 1})

    def test_every_option_builds_at_both_ends_of_its_range(self):
        for name, _, _, _, low, high in hutchfinity.DESIGN_OPTIONS:
            for value in () if low is None else (low, high):
                with self.subTest(option=name, value=value):
                    design = {name: value}
                    for part in ("tub", "grid-insert", "casing", "peg", "pull"):
                        self.mesh(part, 4, 4, 5, "plain", **design)
                        if part == "tub":
                            self.mesh(part, 4, 4, 5, **design)

    def test_every_catalog_bin_builds_at_its_catalog_size(self):
        catalog = json.loads((ROOT / "catalog/bin-skus.json").read_text())
        for row in catalog["items"]:
            with self.subTest(sku=row["sku"]):
                size = self.mesh("bin", row["cells_x"], row["cells_y"], row["height_units"])["size_mm"]
                outer = row["external_bounds_mm"]
                for got, want in zip(size, (outer["x"], outer["y"], outer["z"])):
                    self.assertAlmostEqual(got, want, delta=0.05)

    def test_module_must_fit_the_bed(self):
        with self.assertRaisesRegex(hutchfinity.BuildError, "too big"):
            hutchfinity.build("module", 12, 16, 20, "integral-grid", self.out, bed=200.0)

    def test_bin_and_baseplate_build(self):
        self.assertEqual(self.mesh("bin", 1, 1, 5)["pieces"], 1)
        self.assertEqual(self.mesh("baseplate", 2, 2, 1)["size_mm"][:2], [42.0, 42.0])


class Validation(unittest.TestCase):
    def test_rejects_bad_requests(self):
        for args in (
            ("nope", 5, 5, 5, "plain", {}),
            ("tub", 0, 5, 5, "plain", {}),
            ("tub", 5, 5, 4, "plain", {}),
            ("tub", 5, 5, 41, "plain", {}),
            ("tub", 5, 5, 5, "plain", {"wall": 0.1}),
            ("casing", 5, 5, 5, "plain", {"side_wall": 12.0}),
            ("tub", 5, 5, 5, 'x";system("', {}),
            ("tub", 5, 5, 5, "plain", {"not_an_option": 1}),
        ):
            with self.assertRaises(hutchfinity.BuildError):
                hutchfinity.scad_source(*args)


if __name__ == "__main__":
    unittest.main()
