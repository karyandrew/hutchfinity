"""Live tests for hutchfinity.py. These run the real OpenSCAD."""
import os
import shutil
import sys
import tempfile
import unittest
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

    def build(self, part, x, y, h, floor="integral-grid"):
        result = hutchfinity.build(part, x, y, h, floor, self.out)
        self.assertTrue(Path(result["path"]).exists())
        self.assertTrue(result["closed"])
        return result

    def test_tub_heights_follow_the_bin(self):
        small = self.build("tub", 10, 10, 10)
        self.assertEqual(small["size_mm"][0], 214.4)
        self.assertEqual(small["size_mm"][2], 44.84)
        self.assertEqual(small["pieces"], 1)
        self.assertEqual(self.build("tub", 12, 16, 20)["size_mm"][2], 79.84)
        self.assertEqual(self.build("tub", 10, 10, 10, "plain")["size_mm"][2], 44.74)

    def test_grid_insert_is_one_piece(self):
        insert = self.build("grid-insert", 4, 3, 1)
        self.assertEqual(insert["pieces"], 1)

    def test_casing_matches_the_tub(self):
        casing = self.build("casing", 10, 10, 10)
        self.assertEqual(casing["size_mm"], [252.4, 232.9, 47.14])
        self.assertIn("7 pegs", casing["notes"][0])
        self.assertEqual(self.build("pegs", 10, 10, 10)["pieces"], 7)

    def test_pull_shrinks_to_fit_the_guide(self):
        self.assertEqual(self.build("pull", 10, 10, 10)["size_mm"][:2], [90.0, 32.94])

    def test_bin_and_baseplate_build(self):
        self.assertEqual(self.build("bin", 1, 1, 5)["pieces"], 1)
        self.assertEqual(self.build("baseplate", 2, 2, 1)["size_mm"][:2], [42.0, 42.0])


class Validation(unittest.TestCase):
    def test_rejects_bad_requests(self):
        for args in (("nope", 1, 1, 1, "plain"), ("tub", 0, 1, 1, "plain"), ("tub", 1, 1, 1, 'x";system("')):
            with self.assertRaises(hutchfinity.BuildError):
                hutchfinity.scad_args(*args)


if __name__ == "__main__":
    unittest.main()
