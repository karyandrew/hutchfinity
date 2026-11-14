"""Geometric regressions for the casing slab and continuous peg stop.

These invoke the installed OpenSCAD directly (CGAL is sufficient) so the tests
do not replace a missing Manifold backend with a simulated geometry result.
"""
import ast
import itertools
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hutchfinity  # noqa: E402

OPENSCAD = os.environ.get("OPENSCAD_BIN") or shutil.which("openscad")
BACKEND = []
if OPENSCAD:
    help_result = subprocess.run([OPENSCAD, "--help"], text=True, capture_output=True)
    if "--backend" in help_result.stdout + help_result.stderr:
        BACKEND = ["--backend=Manifold"]
CASING = ROOT / "scad" / "casing.scad"
PEG = ROOT / "scad" / "peg.scad"
ENTRY = ROOT / "scad" / "hutchfinity.scad"


class Defaults(unittest.TestCase):
    def test_casing_and_tub_floor_defaults_are_independent(self):
        options = {row[0]: row for row in hutchfinity.DESIGN_OPTIONS}
        self.assertEqual(options["riding_slab"][2], 3.0)
        self.assertEqual(options["floor_thickness"][2], 1.3)
        # The old casing thickness remains an intentional, explicit override.
        self.assertEqual(hutchfinity.design_overrides({"riding_slab": 1.3}), ["riding_slab=1.3"])
        self.assertIn("name=riding_slab type=number min=1.0 max=10.0 step=any value=3.0", hutchfinity.page())
        _, _, saved = hutchfinity.parse_form({"x": "10", "y": "10", "h": "10", "riding_slab": "1.3"})
        self.assertEqual(saved, {"riding_slab": 1.3})


@unittest.skipUnless(OPENSCAD, "OpenSCAD is required for geometric evidence")
class CasingGeometry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)

    def render(self, text, *, empty=False, assertion=None, overrides=()):
        source, output = self.work / "test.scad", self.work / "test.stl"
        source.write_text(text)
        output.unlink(missing_ok=True)
        command = [OPENSCAD, *BACKEND, "--export-format=binstl", "-o", str(output)]
        for override in overrides:
            command += ["-D", override]
        result = subprocess.run(command + [str(source)], text=True, capture_output=True, timeout=60)
        log = result.stdout + result.stderr
        if assertion is not None:
            self.assertIn("Assertion", log)
            self.assertIn(assertion, log)
            self.assertFalse(output.exists(), log)
            return None
        self.assertNotIn("ERROR:", log)
        self.assertNotIn("WARNING:", log)
        if empty:
            self.assertIn("Current top level object is empty", log)
            self.assertFalse(output.exists(), log)
            return None
        self.assertEqual(result.returncode, 0, log)
        self.assertTrue(output.exists(), log)
        mesh = hutchfinity.read_stl(output)
        self.assertTrue(mesh["closed"], log)
        return mesh

    def cut(self, height=30, depth=10, chamfer=2.5, bore=8.45, reduction=1):
        return (f"through_peg_socket_cut([0,0], {bore}, {height}, {depth}, "
                f"0.5, {chamfer}, {reduction}, $fn=96);")

    def test_active_entry_uses_three_mm_slab(self):
        source, defines = hutchfinity.scad_source("casing", 1, 1, 5, "integral-grid", {})
        mesh = self.render(f"include <{source}>;", overrides=defines)
        self.assertEqual(mesh["size_mm"], [63.4, 43.9, 31.34])
        self.assertEqual(mesh["pieces"], 1)

    def test_socket_positions_leave_material_at_size_and_option_boundaries(self):
        # Exercise combinations, including deep walls around a one-cell drawer.
        # Measure the returned centers against independent circle/web bounds.
        cases = list(itertools.product((1, 2, 40), (1, 2, 40), (18, 40), (18, 40),
                                       (15, 400), (6, 9), (0, 0.75)))
        expressions = []
        for x, y, side, back, spacing, bore, chamfer in cases:
            width, depth = 21 * x + 6.4 + 2 * side, 21 * y + 4.9 + back
            expressions.append(f"echo(casing_peg_positions({width},{depth},{side},{back},"
                               f"{spacing},{bore},{chamfer},1.2));")
        source, output = self.work / "positions.scad", self.work / "positions.csg"
        source.write_text(f"use <{CASING}>;\n" + "\n".join(expressions))
        result = subprocess.run([OPENSCAD, "-o", str(output), str(source)],
                                text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("WARNING", result.stderr)
        centers = [ast.literal_eval(line.removeprefix("ECHO: ")) for line in result.stderr.splitlines()
                   if line.startswith("ECHO: ")]
        self.assertEqual(len(centers), len(cases))
        for case, positions in zip(cases, centers):
            x, y, side, back, _, bore, chamfer = case
            width, depth = 21 * x + 6.4 + 2 * side, 21 * y + 4.9 + back
            radius, land = bore / 2 + chamfer, 1.2
            with self.subTest(case=case):
                self.assertGreaterEqual(len(positions), 2)
                for px, py in positions:
                    self.assertGreaterEqual(min(px, width - px, py, depth - py) + 0.001, radius + land)
                    self.assertTrue(px + radius + land <= side + 0.001
                                    or px - radius - land >= width - side - 0.001
                                    or py - radius - land >= depth - back - 0.001)
                for a, b in itertools.combinations(positions, 2):
                    self.assertGreaterEqual(math.dist(a, b) + 0.001, 2 * (radius + land))

    def test_smallest_drawer_sockets_are_separate_open_passages(self):
        for side, back, bore, chamfer in ((18, 18, 8.45, 0.5), (40, 18, 9, 0.75), (18, 40, 9, 0.75)):
            width, depth, height = 27.4 + 2 * side, 25.9 + back, 31.34
            overrides = ["cells_x=1", "cells_y=1", "bin_h=5", f"side_wall={side}",
                         f"back_wall={back}", f"peg_bore={bore}", f"peg_chamfer={chamfer}"]
            with self.subTest(side=side, back=back):
                body = self.render(f"use <{ENTRY}>; sized_casing();", overrides=overrides)
                self.assertEqual(body["pieces"], 1)
                self.assertEqual(body["size_mm"], [width, depth, height])
                void = self.render(f"use <{ENTRY}>; difference() {{ cube([{width},{depth},{height}]); sized_casing(); }}",
                                   overrides=overrides)
                # Two independent through-bores plus the open drawer slot.
                self.assertEqual(void["pieces"], 3)

    def test_current_fit_callers_share_generator_dimensions(self):
        for x, y, h, slab in ((1, 1, 5, 3), (12, 16, 20, 4)):
            defines = [f"cells_x={x}", f"cells_y={y}", f"bin_h={h}", f"riding_slab={slab}"]
            expected = [21 * x + 42.4, 21 * y + 22.9, round(h * 3.5 + 10.84 + slab, 2)]
            with self.subTest(size=(x, y, h), slab=slab):
                fit = self.render(f"include <{ROOT / 'scad/casing-fit-test.scad'}>;", overrides=defines)
                self.assertEqual(fit["size_mm"], expected)
                gauge = self.render(f"include <{ROOT / 'scad/testbed/casing_mouth_fit_gauge.scad'}>;", overrides=defines)
                self.assertEqual(gauge["size_mm"], [expected[0], 48, expected[2]])
                assembly = self.render(f"include <{ROOT / 'scad/hutchfinity-assembly.scad'}>;",
                                       overrides=[*defines, "SHOW_OPTIONAL_PARTS=false"])
                self.assertEqual(assembly["size_mm"], expected)

    def test_default_standalone_slab_has_no_legacy_blind_magnet_wells(self):
        # The middle slab is solid down to the bed; optional prototype magnet
        # pockets are intentionally absent from the default printable shell.
        self.render(f"""
use <{CASING}>;
difference() {{
    translate([30,0,0]) cube([40,70,1.5]);
    hutchfinity_casing(slot_width=60, slot_depth=70, slot_height=30);
}}
""", empty=True)

    def test_preview_parts_stay_separate_and_standalone_peg_matches(self):
        preview = self.render(f"include <{ROOT / 'scad/hutchfinity-assembly.scad'}>;",
                              overrides=["cells_x=2", "cells_y=2", "bin_h=5"])
        self.assertEqual(preview["pieces"], 4)  # casing, tub, one peg, pull
        peg = self.render(f"include <{PEG}>;")
        self.assertEqual(peg["pieces"], 1)
        self.assertEqual(peg["size_mm"][0], 19.6)
        self.assertAlmostEqual(peg["low"][2], 0, delta=0.001)

    def test_grid_insert_boundary_options_keep_one_five_mm_solid(self):
        # These combinations previously folded the loft above/below its bounds
        # or left eight detached caps near the corner pockets.
        for design, expected_width in (
            ({"wall": 4.0}, 81.6),
            ({"floor_thickness": 3.0}, 82.0),
            ({"wall": 4.0, "floor_thickness": 3.0}, 82.0),
            ({"wall": 1.2, "floor_thickness": 3.0, "grid_clearance": 0.2}, 83.6),
            ({"wall": 4.0, "floor_thickness": 0.8, "grid_clearance": 2.0}, 78.6),
        ):
            with self.subTest(design=design):
                source, defines = hutchfinity.scad_source("grid-insert", 4, 4, 5, "separate-grid", design)
                mesh = self.render(f"include <{source}>;", overrides=defines)
                self.assertEqual(mesh["pieces"], 1)
                self.assertEqual(mesh["size_mm"], [expected_width, expected_width, 5.0])
                self.assertEqual(mesh["low"][2], 0)

    def test_thick_tub_floor_is_not_cut_below_its_requested_height(self):
        self.render(f"""
use <{ROOT / 'scad/tub.scad'}>;
difference() {{
    translate([-1,-1,0]) cube([2,2,2.999]);
    hutchfinity_tub(4,4,5,"plain",false);
}}
""", empty=True, overrides=["FLOOR_THICKNESS=3"])
        self.render(f"""
use <{ROOT / 'scad/tub.scad'}>;
intersection() {{
    translate([-1,-1,3.001]) cube([2,2,1]);
    hutchfinity_tub(4,4,5,"plain",false);
}}
""", empty=True, overrides=["FLOOR_THICKNESS=3"])

    def test_tall_grid_pockets_remain_open_for_bins(self):
        for part, floor_z in (("grid-insert", 0), ("tub", 1.3)):
            with self.subTest(part=part):
                source, defines = hutchfinity.scad_source(part, 4, 4, 5, "integral-grid", {"grid_height": 8.0})
                mesh = self.render(f"include <{source}>;", overrides=defines)
                self.assertEqual(mesh["pieces"], 1)
                if part == "grid-insert":
                    self.assertEqual(mesh["size_mm"][2], 8)
                # Every pocket must contain a clear vertical insertion path,
                # including the 5-8 mm band that the old cutters left capped.
                self.render(f"""
use <{ROOT / 'scad/tub.scad'}>;
intersection() {{
    for (x=[-31.5,-10.5,10.5,31.5], y=[-31.5,-10.5,10.5,31.5])
        translate([x-3,y-3,{floor_z + 0.01}]) cube([6,6,9]);
    {('hutchfinity_grid_insert(4,4)' if part == 'grid-insert' else 'hutchfinity_tub(4,4,5,"integral-grid",false)')};
}}
""", empty=True, overrides=["GRID_Z=8"])

    def test_generated_socket_is_one_open_passage(self):
        # Isolate the void inside one actual generator wall, well away from
        # other sockets. A blind end or a central membrane splits this volume.
        mesh = self.render(f"""
use <{ENTRY}>;
difference() {{
    translate([2, 11, 0]) cube([14, 14, 48.84]);
    sized_casing();
}}
""", overrides=["cells_x=10", "cells_y=10", "bin_h=10"])
        self.assertEqual(mesh["pieces"], 1)
        self.assertEqual(mesh["low"][2], 0)
        self.assertEqual(mesh["size_mm"][2], 48.84)
        self.assertLess(mesh["size_mm"][0], 10)

    def test_standalone_casing_has_same_slab_and_open_passage(self):
        call = "hutchfinity_casing(slot_width=60, slot_depth=60, slot_height=30, enable_magnet_holes=false);"
        body = self.render(f"use <{CASING}>; {call}")
        self.assertEqual(body["size_mm"], [110, 85, 33])
        void = self.render(f"use <{CASING}>; difference() {{ translate([5.5,18,0]) cube([14,14,33]); {call} }}")
        self.assertEqual(void["pieces"], 1)
        self.assertEqual(void["size_mm"][2], 33)

    def test_physical_coupon_uses_production_bore_tessellation(self):
        # Inspect the actual mesh at the end of its straight receiving zone.
        # Its 32-sided bore must match production; a smoother circle could give
        # misleading fit. The loose peg lies outside this 18 mm coupon block.
        mesh = self.render(f"include <{ROOT / 'scad/testbed/through_peg_socket_testbed.scad'}>;")
        receiver_ring = {(p[0], p[1]) for p in mesh["points"]
                         if abs(p[2] - 7.5) < 0.00001 and 4 < p[0] < 14 and 4 < p[1] < 14}
        self.assertEqual(len(receiver_ring), 32)
        self.assertEqual(mesh["pieces"], 2)

    def test_receivers_transition_and_throat_have_the_expected_sections(self):
        # Dimensions are an independent design oracle, not values copied out of
        # the implementation's depth functions. Check both halves of the hole.
        for z, expected in ((1, 8.45), (7.75, 7.95), (8.5, 7.45),
                            (15, 7.45), (22.25, 7.95), (29, 8.45)):
            with self.subTest(z=z):
                mesh = self.render(f"""
use <{CASING}>;
$fn=96;
intersection() {{
    {self.cut()}
    translate([-8,-8,{z}-0.001]) cube([16,16,0.002]);
}}
""")
                self.assertAlmostEqual(mesh["size_mm"][0], expected, delta=0.02)
                self.assertEqual(mesh["pieces"], 1)

    def test_real_peg_fits_before_stop_and_collides_after_it(self):
        # Includes a blunt peg, a tip clamped by peg.scad's 0.8 mm floor, and
        # the shortened peg used when available casing height is small.
        # 96 facets align with the six peg vertices, isolating insertion-stop
        # geometry from the existing coarse-circle press-fit approximation.
        for height, depth, length, chamfer, bore in (
            (30, 10, 19.6, 2.5, 8.45),
            (30, 10, 19.6, 0, 8.45),
            (30, 10, 19.6, 4, 6),
            (12, 5, 9.6, 2.4, 8.45),
        ):
            for extra in (-0.1, 0.1):
                with self.subTest(height=height, chamfer=chamfer, bore=bore, extra=extra):
                    self.render(f"""
use <{CASING}>;
use <{PEG}>;
$fn=96;
intersection() {{
    difference() {{
        translate([-9,-9,0]) cube([18,18,{height}]);
        {self.cut(height, depth, chamfer, bore)}
    }}
    translate([0,0,{depth + extra - length}])
        hutchfinity_peg(diameter={bore},length={length},end_chamfer={chamfer});
}}
""", empty=extra < 0)

    def test_joined_receivers_keep_point_four_mm_axial_allowance(self):
        # Two flush casing faces provide 20 mm total tip travel for the same
        # 19.6 mm peg: it can translate 0.4 mm, not fall through either stop.
        for offset in (-0.21, -0.19, 0.19, 0.21):
            with self.subTest(offset=offset):
                self.render(f"""
use <{CASING}>;
use <{PEG}>;
module wall() {{ difference() {{
    translate([-9,-9,0]) cube([18,18,30]);
    {self.cut()}
}} }}
intersection() {{
    union() {{ wall(); translate([0,0,-30]) wall(); }}
    translate([0,0,{-9.8 + offset}])
        hutchfinity_peg(diameter=8.45,length=19.6,end_chamfer=2.5);
}}
""", empty=abs(offset) < 0.2)

    def test_rejects_geometry_without_an_open_stop_throat(self):
        self.render(f"use <{CASING}>; {self.cut(height=16)}", assertion="too short")
        self.render(f"use <{CASING}>; {self.cut(reduction=0)}", assertion="smaller than")


if __name__ == "__main__":
    unittest.main()
