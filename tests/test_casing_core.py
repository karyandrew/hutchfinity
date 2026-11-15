"""Webbed casing walls and the exclusive casing_core control (issue 62, chunk A).

Same harness as test_casing_geometry.py: direct OpenSCAD renders, the layout read
back with echo over a case product, meshes read with read_stl. File and text checks
need no OpenSCAD. Chunk A offers solid and webbed; open-infill is a named value
that is refused until a later chunk builds it, so it is never silently solid.
"""
import ast
import itertools
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hutchfinity  # noqa: E402
import print_settings  # noqa: E402

OPENSCAD = os.environ.get("OPENSCAD_BIN") or shutil.which("openscad")
BACKEND = []
if OPENSCAD:
    help_result = subprocess.run([OPENSCAD, "--help"], text=True, capture_output=True)
    if "--backend" in help_result.stdout + help_result.stderr:
        BACKEND = ["--backend=Manifold"]
CASING = ROOT / "scad" / "casing.scad"
CORE = ROOT / "scad" / "casing_core.scad"
PEG = ROOT / "scad" / "peg.scad"
ENTRY = ROOT / "scad" / "hutchfinity.scad"

SLAB = 3.0
TOL = 2e-3          # echo prints six significant digits
SOLID = 'sized_casing(core="solid")'
WEBBED = 'sized_casing(core="webbed")'


def rounded(value):
    return round(value, 6)


class Case:
    """One casing size. Dimensions follow the generator's own formulas."""

    def __init__(self, x=1, y=1, h=5, side=18, back=18, bore=8.45, chamfer=0.5, spacing=190, road=1.4,
                 land=1.2):
        self.x, self.y, self.h, self.side, self.back = x, y, h, side, back
        self.bore, self.chamfer, self.spacing, self.road, self.land = bore, chamfer, spacing, road, land
        self.width = rounded(21 * x + 6.4 + 2 * side)
        self.depth = rounded(21 * y + 4.9 + back)
        self.height = rounded(h * 3.5 + 10.84 + SLAB)
        self.skin = self.web = self.collar = 2 * road
        self.min_pocket = 3 * road
        self.pitch = 24
        self.radius = bore / 2 + chamfer + self.collar

    def overrides(self, **extra):
        values = {"cells_x": self.x, "cells_y": self.y, "bin_h": self.h, "side_wall": self.side,
                  "back_wall": self.back, "peg_bore": self.bore, "peg_chamfer": self.chamfer,
                  "peg_spacing": self.spacing, "peg_edge_land": self.land, "core_road": self.road}
        values.update(extra)
        return [f"{key}={value}" for key, value in values.items()]

    def positions_expr(self):
        return (f"casing_peg_positions({self.width},{self.depth},{self.side},{self.back},"
                f"{self.spacing},{self.bore},{self.chamfer},{self.land})")

    def pockets_expr(self, web=None, skin=None):
        return (f"casing_core_pockets({self.width},{self.depth},{self.side},{self.back},"
                f"{self.positions_expr()},casing_core_zone_radius({self.bore},{self.chamfer},{self.collar}),"
                f"{self.skin if skin is None else skin},{self.web if web is None else web},"
                f"{self.pitch},{self.min_pocket})")

    @property
    def footprint(self):
        return self.width * self.depth - (self.width - 2 * self.side) * (self.depth - self.back)


def rect_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def point_gap(rect, point):
    return rect_gap(rect, (point[0], point[1], point[0], point[1]))


def layout_violations(case, positions, pockets):
    """Every way a layout breaks the stated member, pocket and collar rules."""
    problems = []
    columns = [(0, 0, case.side, case.depth), (case.width - case.side, 0, case.width, case.depth),
               (0, case.depth - case.back, case.width, case.depth)]
    for rect in pockets:
        if min(rect[2] - rect[0], rect[3] - rect[1]) < case.min_pocket - TOL:
            problems.append(("pocket too small", rect))
        grown = (rect[0] - case.skin + TOL, rect[1] - case.skin + TOL,
                 rect[2] + case.skin - TOL, rect[3] + case.skin - TOL)
        if not any(c[0] <= grown[0] and c[1] <= grown[1] and grown[2] <= c[2] and grown[3] <= c[3]
                   for c in columns):
            problems.append(("skin thinner than two roads or pocket outside the walls", rect))
        for position in positions:
            if point_gap(rect, position) < case.radius - TOL:
                problems.append(("pocket inside a collar", rect, position))
    for a, b in itertools.combinations(pockets, 2):
        if rect_gap(a, b) < case.web - TOL:
            problems.append(("member thinner than two roads", a, b))
    return problems


@unittest.skipUnless(OPENSCAD, "OpenSCAD is required for geometric evidence")
class Harness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)

    def run_scad(self, text, overrides=()):
        source, output = self.work / "test.scad", self.work / "test.stl"
        source.write_text(text)
        output.unlink(missing_ok=True)
        command = [OPENSCAD, *BACKEND, "--export-format=binstl", "-o", str(output)]
        for override in overrides:
            command += ["-D", override]
        result = subprocess.run(command + [str(source)], text=True, capture_output=True, timeout=180)
        return result, result.stdout + result.stderr, output

    def render(self, text, overrides=(), *, empty=False, assertion=None):
        result, log, output = self.run_scad(text, overrides)
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
        mesh["log"] = log
        return mesh

    def is_empty(self, text, overrides=()):
        result, log, output = self.run_scad(text, overrides)
        self.assertNotIn("ERROR:", log)
        self.assertEqual(result.returncode, 0, log)
        return "Current top level object is empty" in log and not output.exists()

    def mesh_or_none(self, text, overrides=()):
        result, log, output = self.run_scad(text, overrides)
        self.assertNotIn("ERROR:", log)
        if "Current top level object is empty" in log:
            return None
        self.assertTrue(output.exists(), log)
        return hutchfinity.read_stl(output)

    def echoes(self, expressions):
        source, output = self.work / "echoes.scad", self.work / "echoes.csg"
        source.write_text(f"use <{CASING}>;\nuse <{CORE}>;\n"
                          + "\n".join(f"echo({expression});" for expression in expressions))
        result = subprocess.run([OPENSCAD, "-o", str(output), str(source)], text=True,
                                capture_output=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("WARNING", result.stderr)
        self.assertNotIn("ERROR", result.stderr)
        values = [ast.literal_eval(line.removeprefix("ECHO: ")) for line in result.stderr.splitlines()
                  if line.startswith("ECHO: ")]
        self.assertEqual(len(values), len(expressions))
        return values

    def layout(self, case):
        positions, pockets, area = self.echoes(
            [f"[{case.positions_expr()},{case.pockets_expr()},casing_core_pocket_area({case.pockets_expr()})]"])[0]
        return [tuple(p) for p in positions], [tuple(r) for r in pockets], area


def prisms(pockets, z0, z1, grow=-0.01):
    parts = [f"translate([{r[0] - grow},{r[1] - grow},{z0 - grow}]) "
             f"cube([{r[2] - r[0] + 2 * grow},{r[3] - r[1] + 2 * grow},{z1 - z0 + 2 * grow}]);"
             for r in pockets]
    return "union() {" + "".join(parts) + "}"


class Control(unittest.TestCase):
    """Test 1: the control exists, defaults to solid and reaches the model."""

    def test_option_default_choices_and_define(self):
        options = {row[0]: row for row in hutchfinity.DESIGN_OPTIONS}
        self.assertEqual(options["casing_core"][2], "solid")
        choices = hutchfinity.CHOICE_OPTIONS["casing_core"]
        self.assertIn("solid", choices)
        self.assertIn("webbed", choices)
        self.assertEqual(hutchfinity.design_overrides({"casing_core": "solid"}), [])
        self.assertEqual(hutchfinity.design_overrides({"casing_core": "webbed"}), ['casing_core="webbed"'])
        _, defines = hutchfinity.scad_source("casing", 1, 1, 5, "integral-grid", {"casing_core": "webbed"})
        self.assertIn('casing_core="webbed"', defines)
        _, _, saved = hutchfinity.parse_form({"x": "10", "y": "10", "h": "10", "casing_core": "webbed"})
        self.assertEqual(saved, {"casing_core": "webbed"})
        _, _, saved = hutchfinity.parse_form({"x": "10", "y": "10", "h": "10", "casing_core": "solid"})
        self.assertEqual(saved, {})
        page = hutchfinity.page()
        self.assertIn("name=casing_core", page)
        self.assertIn("value=solid selected", page)
        self.assertIn("value=webbed", page)

    def test_open_infill_is_named_but_refused_never_silently_solid(self):
        self.assertIn("open-infill", hutchfinity.CHOICE_OPTIONS["casing_core"])
        with self.assertRaisesRegex(hutchfinity.BuildError, "not available yet"):
            hutchfinity.design_overrides({"casing_core": "open-infill"})
        with self.assertRaisesRegex(hutchfinity.BuildError, "not available yet"):
            hutchfinity.build_module(1, 1, 5, "integral-grid", Path(tempfile.gettempdir()),
                                     {"casing_core": "open-infill"})
        # The form still shows the value so the control keeps its final shape, but it cannot be chosen.
        self.assertRegex(hutchfinity.page(), r"<option value=open-infill disabled")
        cli = subprocess.run([sys.executable, str(ROOT / "hutchfinity.py"), "1", "1", "5", "--casing-core",
                              "open-infill", "--out", tempfile.gettempdir()], text=True, capture_output=True)
        self.assertEqual(cli.returncode, 1)
        self.assertIn("not available yet", cli.stderr)

    def test_unknown_and_non_text_values_are_rejected(self):
        for value in ("combined", "Webbed", "webbed,open-infill", "", 1, True, None, ["webbed"]):
            with self.subTest(value=value), self.assertRaises(hutchfinity.BuildError):
                hutchfinity.design_overrides({"casing_core": value})
        cli = subprocess.run([sys.executable, str(ROOT / "hutchfinity.py"), "1", "1", "5", "--casing-core",
                              "combined", "--out", tempfile.gettempdir()], text=True, capture_output=True)
        self.assertEqual(cli.returncode, 2)

    def test_assumptions_table_is_the_single_source(self):
        """Test 15, text part: page, PRINTING.md and print-settings.json read one table."""
        table = print_settings.CASING_CORE_ASSUMPTIONS
        self.assertEqual(set(table), {"solid", "webbed"})
        page = hutchfinity.page()
        for value, text in table.items():
            with self.subTest(value=value):
                self.assertTrue(text.strip())
                self.assertIn(text, page)
                self.assertEqual(print_settings.casing_core_assumption(value), text)
        for value in ("combined", "open-infill", "", None, 3):
            with self.subTest(rejected=value), self.assertRaises(print_settings.PrintSettingsError):
                print_settings.casing_core_assumption(value)
        with tempfile.TemporaryDirectory() as folder:
            for value, text in table.items():
                jobs = [{"file": "2-casing.3mf", "parts": {"Casing": print_settings.part_record(
                    "Casing", 1, print_settings.print_options(geometry_only=True), 3.0, casing_core=value)}}]
                paths = print_settings.write_printing_files(Path(folder), jobs, print_settings.print_options(
                    geometry_only=True), stem=value, casing_core=value)
                recorded = json.loads(paths[0].read_text())
                self.assertEqual(recorded["casing_core"], {"mode": value, "assumptions": text})
                self.assertIn(text, paths[1].read_text())

    def test_webbed_guidance_is_solid_compatible_and_never_zero_top(self):
        """Test 13, guidance part. Solid guidance is unchanged."""
        geometry = print_settings.print_options(geometry_only=True)
        solid = print_settings.part_record("Casing", 1, geometry, 3.0)
        self.assertEqual(solid["recommended_overrides"], {"bottom_shell_layers": "1", "bottom_shell_thickness": "3"})
        self.assertEqual(print_settings.part_record("Casing", 1, geometry, 3.0, casing_core="solid"), solid)
        webbed = print_settings.part_record("Casing", 1, geometry, 3.0, casing_core="webbed")
        recommended = webbed["recommended_overrides"]
        self.assertEqual(recommended["sparse_infill_density"], "100%")
        self.assertEqual(recommended["sparse_infill_pattern"], "rectilinear")
        self.assertEqual(webbed["applied_overrides"], {})
        for avoid in (False, True):
            options = print_settings.print_options(profile={"type": "process", "name": "p", "top_shell_layers": 4},
                                                   avoid_crossings=avoid)
            applied = print_settings.part_record("Casing", 1, options, 3.0, casing_core="webbed")["applied_overrides"]
            self.assertEqual(applied["sparse_infill_pattern"], "rectilinear")
            self.assertEqual(applied["sparse_infill_density"], "100%")
            self.assertEqual(applied["top_shell_layers"], "4")  # the user's own value, never forced to zero
        self.assertNotIn("top_shell_thickness", recommended)
        self.assertNotIn("top_shell_layers", recommended)
        # Tub and the accessories never see a casing core.
        for name in ("Tub", "Peg", "Pull"):
            self.assertEqual(print_settings.part_record(name, 1, geometry, None, casing_core="webbed"),
                             print_settings.part_record(name, 1, geometry, None))

    def test_road_comes_from_the_process_wall_width_else_default(self):
        self.assertEqual(print_settings.core_road(print_settings.print_options(geometry_only=True)),
                         (1.4, "default"))
        for profile, expected in (
            ({"type": "process", "name": "p", "outer_wall_line_width": "1.2"}, (1.2, "outer_wall_line_width")),
            ({"type": "process", "name": "p", "line_width": "1.1"}, (1.1, "line_width")),
            ({"type": "process", "name": "p", "outer_wall_line_width": "1.2", "line_width": "1.1"},
             (1.2, "outer_wall_line_width")),
            ({"type": "process", "name": "p", "outer_wall_line_width": "120%"}, (1.4, "default")),
            ({"type": "process", "name": "p", "layer_height": "0.2"}, (1.4, "default")),
        ):
            with self.subTest(profile=profile):
                self.assertEqual(print_settings.core_road(print_settings.print_options(profile)), expected)


@unittest.skipUnless(OPENSCAD, "OpenSCAD is required for geometric evidence")
class Layout(Harness):
    """Tests 3 and 4: the pocket layout is a pure XY function with fixed member rules."""

    def cases(self):
        sizes = ((1, 1), (2, 3), (10, 10), (12, 16))
        walls = ((18, 18), (18, 40), (40, 18), (25, 25))
        return [Case(x, y, 5, side, back, bore, chamfer, spacing, road)
                for (x, y), (side, back), bore, chamfer, spacing, road in itertools.product(
                    sizes, walls, (6, 8.45, 9), (0, 0.75), (190, 40), (1.4, 1.0))]

    def test_layout_invariants_over_a_size_wall_spacing_and_bore_product(self):
        cases = self.cases()
        results = self.echoes([f"[{c.positions_expr()},{c.pockets_expr()}]" for c in cases])
        counted = 0
        for case, (positions, pockets) in zip(cases, results):
            with self.subTest(x=case.x, y=case.y, side=case.side, back=case.back, bore=case.bore,
                              chamfer=case.chamfer, spacing=case.spacing, road=case.road):
                self.assertEqual(layout_violations(case, positions, [tuple(r) for r in pockets]), [])
                counted += len(pockets)
        self.assertGreater(counted, 1000)  # the product really produced pockets

    def test_layout_does_not_depend_on_height_or_slab(self):
        # The function has no height input, and the generated casings agree at 5h and 20h.
        low, high = Case(3, 4, 5), Case(3, 4, 20)
        notes = []
        for case in (low, high):
            mesh = self.render(f"use <{ENTRY}>; {WEBBED};", case.overrides())
            notes.append(re.search(r"casing core: webbed; pockets=(\d+); foot_bearing=([0-9.]+)", mesh["log"]).groups())
        self.assertEqual(notes[0], notes[1])
        self.assertEqual(self.layout(low)[1], self.layout(high)[1])

    def test_default_sizes_have_the_planned_pocket_counts(self):
        # Plain-arithmetic layouts of the default dimensions: counts and a bearing floor.
        for (x, y, h), count, floor in (((12, 16, 20), 42, 0.40), ((10, 10, 10), 28, 0.40), ((1, 1, 5), 4, 0.50)):
            case = Case(x, y, h)
            with self.subTest(size=(x, y, h)):
                _, pockets, area = self.layout(case)
                self.assertEqual(len(pockets), count)
                self.assertGreater(1 - area / case.footprint, floor)

    def test_thin_walls_and_shallow_casings_fall_back_to_solid(self):
        for side, back in ((9, 9), (9.7, 9.7)):
            with self.subTest(side=side, back=back):
                self.assertEqual(self.layout(Case(2, 2, 5, side, back))[1], [])
        # Only the thin walls fall back: a thick back wall still gets pockets.
        mixed = self.layout(Case(2, 2, 5, 9, 25))[1]
        self.assertTrue(mixed)
        self.assertTrue(all(r[1] >= Case(2, 2, 5, 9, 25).depth - 25 for r in mixed))
        call = ("hutchfinity_casing(slot_width=60, slot_depth=60, slot_height={h}, side_thickness=25, "
                "back_thickness=25, enable_peg_holes=false, casing_core=\"{core}\");")
        shallow = self.render(f"use <{CASING}>; " + call.format(h=7.9, core="webbed"))
        solid = self.render(f"use <{CASING}>; " + call.format(h=7.9, core="solid"))
        self.assertAlmostEqual(shallow["volume_mm3"], solid["volume_mm3"], delta=0.01)
        deeper = self.render(f"use <{CASING}>; " + call.format(h=8.1, core="webbed"))
        self.assertLess(deeper["volume_mm3"], solid["volume_mm3"] - 100)

    def test_non_positive_core_dimensions_and_unknown_modes_are_rejected(self):
        call = "hutchfinity_casing(slot_width=60, slot_depth=60, slot_height=30, casing_core=\"webbed\", {});"
        for name in ("core_road", "core_skin", "core_web", "core_collar"):
            for bad in (0, -1):
                with self.subTest(name=name, value=bad):
                    self.render(f"use <{CASING}>; " + call.format(f"{name}={bad}"), assertion="must be positive")
        self.render(f"use <{CASING}>; " + call.format("web_pitch=5"), assertion="web_pitch")
        self.render(f"use <{CASING}>; hutchfinity_casing(casing_core=\"mesh\");", assertion="unknown casing_core")
        self.render(f"use <{CASING}>; hutchfinity_casing(casing_core=\"open-infill\");",
                    assertion="not yet available")
        self.render(f"use <{ENTRY}>; sized_casing(core=\"open-infill\");", assertion="not yet available")

    def test_layout_checks_can_fail(self):
        """Test 14, layout part: a broken layout is flagged by the same checks."""
        case = Case(2, 3, 5)
        positions, pockets, _ = self.layout(case)
        self.assertEqual(layout_violations(case, positions, pockets), [])
        first = pockets[0]
        shifted = [(first[0], first[1], first[2], first[3] + 10)] + pockets[1:]
        self.assertTrue(layout_violations(case, positions, shifted))
        thin_web = [tuple(r) for r in self.echoes([case.pockets_expr(web=1.0)])[0]]
        self.assertTrue(layout_violations(case, positions, thin_web))
        toward_peg = [(first[0], positions[0][1] - 2, first[2], positions[0][1] + 2)] + pockets[1:]
        self.assertTrue(layout_violations(case, positions, toward_peg))


@unittest.skipUnless(OPENSCAD, "OpenSCAD is required for geometric evidence")
class Geometry(Harness):
    """Tests 2 and 5 to 12, run on generated casings."""

    def sizes(self):
        return (Case(1, 1, 5), Case(3, 4, 5, 25, 18), Case(10, 10, 10))

    def test_solid_default_is_identical_to_main(self):
        # Recorded from main before the core existed, on this OpenSCAD.
        for case, size, volume in ((Case(1, 1, 5), [63.4, 43.9, 31.34], 64003.0),
                                   (Case(10, 10, 10), [252.4, 232.9, 48.84], 723048.9),
                                   (Case(12, 16, 20), [294.4, 358.9, 83.84], 1710657.3)):
            with self.subTest(size=(case.x, case.y, case.h)):
                default = self.render(f"use <{ENTRY}>; sized_casing();", case.overrides())
                explicit = self.render(f"use <{ENTRY}>; sized_casing(core=\"solid\");", case.overrides())
                for mesh in (default, explicit):
                    self.assertEqual(mesh["size_mm"], size)
                    self.assertEqual(mesh["pieces"], 1)
                    self.assertAlmostEqual(mesh["volume_mm3"], volume, delta=5)
                self.assertEqual(default["facets"], explicit["facets"])
                self.assertEqual(default["points"], explicit["points"])
                self.assertNotIn("casing core", default["log"])

    def test_webbed_is_one_closed_piece_with_the_solid_bounding_size(self):
        for case in self.sizes() + (Case(12, 16, 20),):
            with self.subTest(size=(case.x, case.y, case.h)):
                solid = self.render(f"use <{ENTRY}>; {SOLID};", case.overrides())
                webbed = self.render(f"use <{ENTRY}>; {WEBBED};", case.overrides())
                self.assertEqual(webbed["pieces"], 1)
                self.assertEqual(webbed["size_mm"], solid["size_mm"])
                self.assertEqual(webbed["low"], solid["low"])
                self.assertLess(webbed["volume_mm3"], solid["volume_mm3"])

    def removed_failures(self, case, variant, pockets, area):
        """Test 6: what solid minus a webbed variant is, against the pockets' extruded outlines."""
        removed = f"difference() {{ {SOLID}; {variant}; }}"
        mesh = self.mesh_or_none(f"use <{ENTRY}>; {removed}", case.overrides())
        problems = []
        if mesh is None:
            return ["nothing removed"]
        if not mesh["closed"]:
            problems.append("removed region is not closed")
        floor, roof = mesh["low"][2], mesh["low"][2] + mesh["size_mm"][2]
        if floor < SLAB - 0.002:
            problems.append(f"cut below the slab: {floor}")
        if abs(roof - case.height) > 0.02:
            problems.append(f"cut does not reach the feet: {roof}")
        if mesh["pieces"] != len(pockets):
            problems.append(f"{mesh['pieces']} removed pieces for {len(pockets)} pockets")
        expected = area * (case.height - SLAB)
        if abs(mesh["volume_mm3"] - expected) > 1e-3 * expected:
            problems.append(f"removed volume {mesh['volume_mm3']} differs from {expected}")
        covered = self.is_empty(f"use <{ENTRY}>; difference() {{ {prisms(pockets, SLAB, case.height)}; {removed}; }}",
                                case.overrides())
        if not covered:
            problems.append("a pocket outline is not fully removed")
        inside = self.is_empty(
            f"use <{ENTRY}>; difference() {{ {removed}; {prisms(pockets, SLAB, case.height + 0.1, 0.01)}; }}",
            case.overrides())
        if not inside:
            problems.append("material was removed outside the pocket outlines")
        return problems

    def test_removed_volume_is_exactly_the_extruded_pockets_from_slab_to_feet(self):
        for case in self.sizes():
            with self.subTest(size=(case.x, case.y, case.h)):
                _, pockets, area = self.layout(case)
                self.assertTrue(pockets)
                self.assertEqual(self.removed_failures(case, WEBBED, pockets, area), [])

    def test_exterior_slot_faces_and_front_ends_equal_solid(self):
        for case in self.sizes():
            with self.subTest(size=(case.x, case.y, case.h)):
                s, w, d, back, side, h = case.skin - 0.01, case.width, case.depth, case.back, case.side, case.height
                slot = d - back
                zones = [(0, 0, 0, s, d), (w - s, 0, 0, s, d), (0, 0, 0, w, s), (0, d - s, 0, w, s),
                         (side - s - 0.01, 0, 0, s, slot), (w - side + 0.02, 0, 0, s, slot),
                         (side, slot + 0.01, 0, w - 2 * side, s)]
                cubes = "".join(f"translate([{x},{y},{SLAB}]) cube([{dx},{dy},{h}]);" for x, y, _, dx, dy in zones)
                removed = f"difference() {{ {SOLID}; {WEBBED}; }}"
                self.render(f"use <{ENTRY}>; intersection() {{ {removed}; union() {{ {cubes} }} }}",
                            case.overrides(), empty=True)

    def collar_failures(self, case, variant, positions):
        removed = f"difference() {{ {SOLID}; {variant}; }}"
        radius = case.radius - 0.01
        cylinders = "".join(f"translate([{p[0]},{p[1]},-1]) cylinder(r={radius},h={case.height + 2},$fn=64);"
                            for p in positions)
        problems = []
        # Nothing is removed inside a collar, so bores and chamfers there are exactly solid's.
        if not self.is_empty(f"use <{ENTRY}>; intersection() {{ {removed}; union() {{ {cylinders} }} }}",
                             case.overrides()):
            problems.append("material removed inside a collar")
        return problems

    def test_collars_keep_bores_and_chamfers_exactly_as_solid(self):
        for case in self.sizes():
            with self.subTest(size=(case.x, case.y, case.h)):
                positions, pockets, _ = self.layout(case)
                self.assertEqual(self.collar_failures(case, WEBBED, positions), [])

    def test_negative_controls_make_the_geometry_checks_fail(self):
        """Test 14: a pocket with its floor below the slab, or reaching a collar, is caught."""
        case = Case(3, 4, 5, 25, 18)
        positions, pockets, area = self.layout(case)
        r = pockets[0]
        below = (f"difference() {{ {WEBBED}; translate([{r[0]},{r[1]},{SLAB - 0.5}]) "
                 f"cube([{r[2] - r[0]},{r[3] - r[1]},1]); }}")
        self.assertTrue(self.removed_failures(case, below, pockets, area))
        p = positions[0]
        into_collar = (f"difference() {{ {WEBBED}; translate([{p[0] + 5.5},{p[1] - 1},{SLAB + 1}]) "
                       f"cube([2,2,5]); }}")
        self.assertTrue(self.collar_failures(case, into_collar, positions))

    def test_void_topology_is_slot_plus_bores_plus_pockets(self):
        for case in self.sizes():
            with self.subTest(size=(case.x, case.y, case.h)):
                positions, pockets, _ = self.layout(case)
                void = self.render(
                    f"use <{ENTRY}>; difference() {{ cube([{case.width},{case.depth},{case.height}]); {WEBBED}; }}",
                    case.overrides())
                self.assertEqual(void["pieces"], 1 + len(positions) + len(pockets))

    def section_area(self, case, variant, opened=0.0):
        z = case.height - 1.0
        section = f"projection(cut=true) translate([0,0,{-z}]) {variant};"
        if opened:
            section = f"offset(delta={opened}) offset(delta={-opened}) {{ {section} }}"
        mesh = self.render(f"use <{ENTRY}>; linear_extrude(height=1) {{ {section} }}", case.overrides())
        return mesh["volume_mm3"]

    def test_foot_bearing_area_matches_the_layout_and_the_floor(self):
        for case in (Case(1, 1, 5), Case(10, 10, 10), Case(12, 16, 20)):
            with self.subTest(size=(case.x, case.y, case.h)):
                positions, pockets, area = self.layout(case)
                z = case.height - 1.0
                slice_mesh = self.render(
                    f"use <{ENTRY}>; intersection() {{ {WEBBED}; translate([-1,-1,{z}]) "
                    f"cube([{case.width + 2},{case.depth + 2},0.1]); }}", case.overrides())
                bores = len(positions) * 16 * (case.bore / 2) ** 2 * math.sin(math.pi / 16)  # 32-sided receivers
                expected = case.footprint - area - bores
                self.assertAlmostEqual(slice_mesh["volume_mm3"] / 0.1, expected, delta=2e-3 * expected)
                ratio = 1 - area / case.footprint
                self.assertGreater(ratio, 0.40)
                mesh = self.render(f"use <{ENTRY}>; {WEBBED};", case.overrides())
                noted = float(re.search(r"foot_bearing=([0-9.]+)", mesh["log"]).group(1))
                self.assertAlmostEqual(noted, ratio, delta=1e-3)
                self.assertEqual(int(re.search(r"pockets=(\d+)", mesh["log"]).group(1)), len(pockets))

    def test_no_member_is_thinner_than_two_roads(self):
        # A morphological opening just under one road removes any member under two roads.
        opening = 0.99 * 1.4
        for case in (Case(1, 1, 5), Case(3, 4, 5, 25, 18)):
            with self.subTest(size=(case.x, case.y, case.h)):
                whole = self.section_area(case, WEBBED)
                self.assertAlmostEqual(self.section_area(case, WEBBED, opening), whole, delta=0.5)
        # The same check must fail for a layout whose webs are one road thick.
        case = Case(3, 4, 5, 25, 18)
        thin = [tuple(r) for r in self.echoes([case.pockets_expr(web=1.0)])[0]]
        _, good, _ = self.layout(case)
        self.assertNotEqual(thin, good)

        def synthetic(pockets, opened=0.0):
            walls = (f"difference() {{ square([{case.width},{case.depth}]); translate([{case.side},0]) "
                     f"square([{case.width - 2 * case.side},{case.depth - case.back}]); }}")
            cuts = "".join(f"translate([{r[0]},{r[1]}]) square([{r[2] - r[0]},{r[3] - r[1]}]);" for r in pockets)
            body = f"difference() {{ {walls}; {cuts} }}"
            if opened:
                body = f"offset(delta={opened}) offset(delta={-opened}) {{ {body} }}"
            return self.render(f"linear_extrude(height=1) {{ {body} }}")["volume_mm3"]

        self.assertAlmostEqual(synthetic(good, opening), synthetic(good), delta=0.5)
        self.assertGreater(synthetic(thin) - synthetic(thin, opening), 5.0)

    def test_real_peg_fits_before_the_stop_and_collides_after_it_in_a_webbed_casing(self):
        for end_chamfer in (2.5, 0):
            case = Case(1, 1, 5)
            for extra in (-0.1, 0.1):
                with self.subTest(end_chamfer=end_chamfer, extra=extra):
                    self.render(f"""
use <{ENTRY}>;
use <{CASING}>;
use <{PEG}>;
$fn=96;
p = {case.positions_expr()}[0];
intersection() {{
    {WEBBED};
    translate([p[0], p[1], {10 + extra - 19.6}])
        hutchfinity_peg(diameter=8.45, length=19.6, end_chamfer={end_chamfer});
}}
""", case.overrides(casing_fn=96, peg_end_chamfer=end_chamfer), empty=extra < 0)

    def test_joined_webbed_receivers_keep_the_point_four_mm_allowance(self):
        case = Case(1, 1, 5)
        for offset in (-0.21, -0.19, 0.19, 0.21):
            with self.subTest(offset=offset):
                self.render(f"""
use <{ENTRY}>;
use <{CASING}>;
use <{PEG}>;
$fn=96;
p = {case.positions_expr()}[0];
intersection() {{
    union() {{ {WEBBED}; translate([0,0,{-case.height}]) {WEBBED}; }}
    translate([p[0], p[1], {-9.8 + offset}])
        hutchfinity_peg(diameter=8.45, length=19.6, end_chamfer=2.5);
}}
""", case.overrides(casing_fn=96), empty=abs(offset) < 0.2)


@unittest.skipUnless(OPENSCAD, "OpenSCAD is required for geometric evidence")
class Generator(unittest.TestCase):
    """Tests 13 and 15, generator part."""

    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out)

    def build(self, core=None, printing=None):
        design = {} if core is None else {"casing_core": core}
        result = hutchfinity.build_module(1, 1, 5, "integral-grid", self.out / (core or "default"), design,
                                          printing)
        folder = Path(result["path"])
        return folder, json.loads((folder / "manifest.json").read_text())

    def test_manifest_records_mode_pockets_and_bearing(self):
        folder, manifest = self.build("webbed")
        record = manifest["casing_core"]
        self.assertEqual(record["mode"], "webbed")
        self.assertEqual(record["pockets"], 4)  # the 1 x 1 casing's planned layout
        self.assertGreater(record["foot_bearing_ratio"], 0.5)
        self.assertEqual(record["road_mm"], 1.4)
        self.assertEqual(record["road_source"], "default")
        self.assertEqual(manifest["design_overrides"], {"casing_core": "webbed"})
        self.assertEqual(manifest["sizes_mm"]["casing"], [63.4, 43.9, 31.34])
        self.assertEqual(manifest["peg_total"], 2)
        _, solid = self.build("solid")
        self.assertEqual(solid["casing_core"], {"mode": "solid"})
        self.assertEqual(solid["design_overrides"], {})
        self.assertEqual(solid["facets"]["casing"], self.build()[1]["facets"]["casing"])
        self.assertLess(solid["facets"]["casing"], manifest["facets"]["casing"])

    def test_road_follows_the_selected_process_wall_width(self):
        profile = {"type": "process", "name": "wide", "outer_wall_line_width": "1.2"}
        _, manifest = self.build("webbed", print_settings.print_options(profile))
        self.assertEqual((manifest["casing_core"]["road_mm"], manifest["casing_core"]["road_source"]),
                         (1.2, "outer_wall_line_width"))

    def test_printed_texts_carry_the_table_for_each_selected_value(self):
        for value, text in print_settings.CASING_CORE_ASSUMPTIONS.items():
            with self.subTest(value=value):
                folder, manifest = self.build(value)
                self.assertIn(text, (folder / "PRINTING.md").read_text())
                recorded = json.loads((folder / "print-settings.json").read_text())
                self.assertEqual(recorded["casing_core"], {"mode": value, "assumptions": text})
        folder, _ = self.build("webbed")
        recorded = json.loads((folder / "print-settings.json").read_text())
        casing = next(job for job in recorded["jobs"] if job["file"] == "2-casing.3mf")["parts"]["Casing"]
        self.assertEqual(casing["recommended_overrides"]["sparse_infill_density"], "100%")
        self.assertNotIn("top_shell_layers", json.dumps(recorded))
        self.assertNotIn("top_shell_thickness", json.dumps(recorded))

    def test_each_part_is_one_closed_solid_in_both_modes(self):
        for core in ("solid", "webbed"):
            with self.subTest(core=core):
                folder, _ = self.build(core)
                for name in ("1-tub.3mf", "2-casing.3mf", "3-pegs-and-pull.3mf"):
                    self.assertTrue((folder / name).is_file())
                mesh = hutchfinity.render("casing", 1, 1, 5, "integral-grid", {"casing_core": core})
                self.assertTrue(mesh["closed"])
                self.assertEqual(mesh["pieces"], 1)


if __name__ == "__main__":
    unittest.main()
