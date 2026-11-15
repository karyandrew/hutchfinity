"""Open-infill casing core (issue 62, chunk B).

The casing body is the solid mesh. The casing job carries setting regions that print
solid at the slab and at every peg bore, with top shells off for the casing only. The
regions are never printed material: the 3MF writes one object made of parts, the body
as a normal part and each region as a modifier part. Same harness as test_casing_core.py:
direct OpenSCAD renders, layouts read back with echo, structure read from the 3MF zip.
Tests that need no OpenSCAD (the control, the writer, the texts) run everywhere; the
geometry and generator tests need it and run under ./ci with zero skips.
"""
import hashlib
import itertools
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hutchfinity  # noqa: E402
import print_settings  # noqa: E402
from test_casing_core import (  # noqa: E402
    CORE, ENTRY, OPENSCAD, SLAB, SOLID, WEBBED, Case, Harness,
)

OPEN = 'sized_casing(core="open-infill")'
REGIONS = 'sized_casing(core="open-infill", output="regions")'
NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
SOLID_REGION_SETTINGS = {"sparse_infill_density": "100%", "sparse_infill_pattern": "rectilinear"}
PROCESS = {"type": "process", "name": "trial", "layer_height": "0.2", "sparse_infill_density": "20%",
           "top_shell_layers": "4", "top_shell_thickness": "0.8"}


def region(index):
    return f'sized_casing(core="open-infill", output="regions", region={index})'


def regions_expr(case):
    return (f"casing_core_regions({case.width},{case.depth},{case.side},{case.back},{SLAB},{case.height},"
            f"{case.positions_expr()},casing_core_zone_radius({case.bore},{case.chamfer},{case.collar}))")


def zones_expr(case):
    return (f"casing_core_pillar_zones({case.positions_expr()},{case.width},{case.side},{case.back},"
            f"casing_core_zone_radius({case.bore},{case.chamfer},{case.collar}))")


def union_of(indexes, shift=None):
    shift = shift or {}
    parts = "".join(
        (f"translate({shift[i]}) " if i in shift else "") + region(i) + ";" for i in indexes)
    return "union() {" + parts + "}"


def box_mesh(low, size):
    """An axis-aligned box in the shape hutchfinity.checked_mesh returns."""
    x, y, z = low
    dx, dy, dz = size
    points = [(x + i * dx, y + j * dy, z + k * dz) for k in (0, 1) for j in (0, 1) for i in (0, 1)]
    triangles = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4),
                 (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)]
    return {"points": points, "triangles": triangles, "low": [x, y, z], "size_mm": [dx, dy, dz]}


def read_project(path):
    """The 3MF as the slicer sees it: objects, build items and the settings config."""
    with zipfile.ZipFile(path) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        names = archive.namelist()
        config = ET.fromstring(archive.read("Metadata/model_settings.config")) \
            if "Metadata/model_settings.config" in names else None
    objects = {o.attrib["id"]: o for o in model.findall(f"{NS}resources/{NS}object")}
    items = model.findall(f"{NS}build/{NS}item")
    return objects, items, config


def vertices(obj):
    return [tuple(float(v.attrib[a]) for a in "xyz") for v in obj.findall(f"{NS}mesh/{NS}vertices/{NS}vertex")]


def extent(obj):
    points = vertices(obj)
    low = [min(p[i] for p in points) for i in range(3)]
    high = [max(p[i] for p in points) for i in range(3)]
    return low, [round(high[i] - low[i], 4) for i in range(3)]


def config_object(config, object_id):
    """(object metadata, [(part id, subtype, part metadata)]) for one object of the config."""
    for obj in config.findall("object"):
        if obj.attrib["id"] == object_id:
            meta = {m.attrib["key"]: m.attrib["value"] for m in obj.findall("metadata")}
            parts = [(p.attrib["id"], p.attrib.get("subtype"),
                      {m.attrib["key"]: m.attrib["value"] for m in p.findall("metadata")})
                     for p in obj.findall("part")]
            return meta, parts
    raise AssertionError(f"object {object_id} is not in the settings config")


def member_hashes(path):
    with zipfile.ZipFile(path) as archive:
        return {n: hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist()}


class Control(unittest.TestCase):
    """B1 and B10, the parts that need no OpenSCAD."""

    def test_the_full_set_is_exactly_three_values_and_default_stays_solid(self):
        """B1: solid, webbed and open-infill, in that order; the default is still solid."""
        self.assertEqual(hutchfinity.CHOICE_OPTIONS["casing_core"], ("solid", "webbed", "open-infill"))
        options = {row[0]: row for row in hutchfinity.DESIGN_OPTIONS}
        self.assertEqual(options["casing_core"][2], "solid")
        self.assertEqual(hutchfinity.design_overrides({"casing_core": "open-infill"}),
                         ['casing_core="open-infill"'])
        _, defines = hutchfinity.scad_source("casing", 1, 1, 5, "integral-grid", {"casing_core": "open-infill"})
        self.assertIn('casing_core="open-infill"', defines)
        self.assertEqual(hutchfinity.design_overrides({}), [])
        # Nothing is "named but not built" any more.
        self.assertFalse(getattr(hutchfinity, "CHOICES_NOT_YET", {}))

    def test_combined_unknown_and_non_text_values_are_rejected_at_form_and_cli(self):
        for value in ("combined", "webbed,open-infill", "open-infill,webbed", "Open-infill", "open_infill",
                      "", 1, True, None, ["open-infill"]):
            with self.subTest(value=value), self.assertRaises(hutchfinity.BuildError):
                hutchfinity.design_overrides({"casing_core": value})
        for value in ("combined", "webbed+open-infill"):
            cli = subprocess.run([sys.executable, str(ROOT / "hutchfinity.py"), "1", "1", "5", "--casing-core",
                                  value, "--out", tempfile.gettempdir()], text=True, capture_output=True)
            self.assertEqual(cli.returncode, 2, value)
        helped = subprocess.run([sys.executable, str(ROOT / "hutchfinity.py"), "--help"], text=True,
                                capture_output=True)
        self.assertIn("open-infill", helped.stdout)
        self.assertNotIn("not available yet", helped.stdout)

    def test_form_offers_open_infill_with_its_own_note_and_round_trips(self):
        """B10: the page shows the table's note for each value; the value survives the form."""
        import re
        page = hutchfinity.page()
        self.assertRegex(page, r"<option value=open-infill>")
        self.assertNotIn("disabled", re.search(r"<select name=casing_core>.*?</select>", page, re.S).group(0))
        self.assertIn("Open infill (slicer infill exposed, top surfaces off)", page)
        self.assertIn("value=solid selected", page)
        self.assertEqual(set(print_settings.CASING_CORE_ASSUMPTIONS), {"solid", "webbed", "open-infill"})
        for value, text in print_settings.CASING_CORE_ASSUMPTIONS.items():
            with self.subTest(value=value):
                self.assertEqual(print_settings.casing_core_assumption(value), text)
                note = re.search(rf"<p class=note data-casing-core={value}( hidden)?>(.*?)</p>", page, re.S)
                self.assertTrue(note, value)
                self.assertEqual(bool(note.group(1)), value != "solid")  # only the selected value shows
                self.assertIn(text.split(".")[0], note.group(2))
        _, _, saved = hutchfinity.parse_form({"x": "10", "y": "10", "h": "10", "casing_core": "open-infill"})
        self.assertEqual(saved, {"casing_core": "open-infill"})
        for value in ("combined", "webbed,open-infill"):
            with self.assertRaises(hutchfinity.BuildError):
                hutchfinity.design_overrides(hutchfinity.parse_form(
                    {"x": "10", "y": "10", "h": "10", "casing_core": value})[2])

    def test_assumption_text_states_every_required_item(self):
        """B8, the static part: the one table entry carries the whole print context."""
        text = print_settings.CASING_CORE_ASSUMPTIONS["open-infill"]
        for required in ("top_shell_layers=0", "top_shell_thickness=0", "casing job only",
                         "never to the tub, pegs or pull", "recommended, not embedded",
                         "slab plate", "bore block", "sparse_infill_density=100%",
                         "avoid-crossings", "only makes sense with top surfaces off",
                         "drops per-object settings or region bodies", "prints as the solid model",
                         "no failure", "preview", "qualified"):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_open_infill_guidance_is_per_object_named_and_never_leaks(self):
        """B6/B7 at the record level: only a chosen open-infill casing gets zero top shells."""
        geometry = print_settings.print_options(geometry_only=True)
        record = print_settings.part_record("Casing", 1, geometry, 3.0, casing_core="open-infill")
        self.assertEqual(record["recommended_overrides"]["top_shell_layers"], "0")
        self.assertEqual(record["recommended_overrides"]["top_shell_thickness"], "0")
        self.assertEqual(record["applied_overrides"], {})  # geometry only: recommended, not embedded
        self.assertEqual(record["recommended_overrides"]["bottom_shell_layers"], "1")
        self.assertEqual(record["regions"]["settings"], SOLID_REGION_SETTINGS)
        self.assertFalse(record["regions"]["embedded"])
        process = print_settings.print_options(PROCESS)
        applied = print_settings.part_record("Casing", 1, process, 3.0, casing_core="open-infill")
        self.assertEqual(applied["applied_overrides"]["top_shell_layers"], "0")
        self.assertEqual(applied["applied_overrides"]["top_shell_thickness"], "0")
        self.assertEqual(applied["applied_overrides"]["layer_height"], "0.2")
        self.assertTrue(applied["regions"]["embedded"])
        crossing = print_settings.print_options(avoid_crossings=True)
        self.assertEqual(print_settings.part_record("Casing", 1, crossing, 3.0, casing_core="open-infill")
                         ["applied_overrides"]["sparse_infill_pattern"], "tpmsd")
        for core in ("solid", "webbed"):
            for name in ("Casing", "Tub", "Peg", "Pull"):
                floor = {"Casing": 3.0, "Tub": 1.3}.get(name)
                other = print_settings.part_record(name, 1, process, floor, casing_core=core)
                self.assertEqual(other["applied_overrides"].get("top_shell_layers"), "4", (core, name))
                self.assertNotIn("regions", other)
        for name in ("Tub", "Peg", "Pull"):
            self.assertEqual(print_settings.part_record(name, 1, process, None, casing_core="open-infill"),
                             print_settings.part_record(name, 1, process, None))


class Writer(unittest.TestCase):
    """B6, the writer alone: one object made of parts. No OpenSCAD needed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "job.3mf"
        self.body = box_mesh((3, 2, 1), (6, 3, 5))
        self.plate = box_mesh((3, 2, 1), (6, 3, 1))
        self.block = box_mesh((4, 2, 1), (2, 3, 5))
        self.peg = box_mesh((0, 0, 0), (1, 1, 4))
        self.settings = {"Casing": {"top_shell_layers": "0", "top_shell_thickness": "0"}, "Peg": {}}
        self.regions = {"Casing": [("slab-plate", self.plate, SOLID_REGION_SETTINGS),
                                   ("bore-block-1", self.block, SOLID_REGION_SETTINGS)]}

    def write(self, regions="default", settings="default"):
        hutchfinity.write_3mf(
            self.path, [("Casing", self.body, 1), ("Peg", self.peg, 2)], 500.0,
            self.settings if settings == "default" else settings,
            self.regions if regions == "default" else regions)

    def test_casing_is_one_object_of_components_and_other_objects_stay_flat(self):
        self.write()
        objects, items, config = read_project(self.path)
        self.assertEqual(len(items), 3)  # one casing and two pegs: regions are not build items
        casing = objects[items[0].attrib["objectid"]]
        components = casing.findall(f"{NS}components/{NS}component")
        self.assertEqual(len(components), 3)  # body, slab plate, one bore block
        self.assertIsNone(casing.find(f"{NS}mesh"))
        for component in components:
            self.assertIsNotNone(objects[component.attrib["objectid"]].find(f"{NS}mesh"))
        for item in items[1:]:
            peg = objects[item.attrib["objectid"]]
            self.assertIsNotNone(peg.find(f"{NS}mesh"))
            self.assertIsNone(peg.find(f"{NS}components"))
        self.assertEqual(len({i.attrib["objectid"] for i in items[1:]}), 2)  # a resource per copy, as before

    def test_part_subtypes_and_per_part_keys_are_read_from_the_config(self):
        self.write()
        objects, items, config = read_project(self.path)
        object_id = items[0].attrib["objectid"]
        meta, parts = config_object(config, object_id)
        self.assertEqual(meta["name"], "Casing")
        self.assertEqual((meta["top_shell_layers"], meta["top_shell_thickness"]), ("0", "0"))
        components = [c.attrib["objectid"] for c in objects[object_id].findall(f"{NS}components/{NS}component")]
        self.assertEqual([p[0] for p in parts], components)  # a part per component, in order
        self.assertEqual([p[1] for p in parts], ["normal_part", "modifier_part", "modifier_part"])
        body_meta = parts[0][2]
        self.assertNotIn("sparse_infill_density", body_meta)
        self.assertNotIn("top_shell_layers", body_meta)
        for _, _, part_meta in parts[1:]:
            self.assertEqual(part_meta["sparse_infill_density"], "100%")
            self.assertEqual(part_meta["sparse_infill_pattern"], "rectilinear")
            self.assertNotIn("top_shell_layers", part_meta)  # the zero-top setting sits on the object
        self.assertEqual([p[2]["name"] for p in parts[1:]], ["slab-plate", "bore-block-1"])

    def test_every_sub_object_shares_the_body_origin(self):
        self.write()
        objects, items, _ = read_project(self.path)
        components = objects[items[0].attrib["objectid"]].findall(f"{NS}components/{NS}component")
        lows = [extent(objects[c.attrib["objectid"]]) for c in components]
        self.assertEqual(lows[0], ([0, 0, 0], [6, 3, 5]))
        self.assertEqual(lows[1], ([0, 0, 0], [6, 3, 1]))   # plate: same low as the body
        self.assertEqual(lows[2], ([1, 0, 0], [2, 3, 5]))   # block: one mm in from the body low

    def test_regions_never_reach_a_plain_file_or_an_unknown_object(self):
        with self.assertRaises(hutchfinity.BuildError):
            self.write(settings=None)  # a plain 3MF has no way to mark a region, and would print it
        with self.assertRaises(hutchfinity.BuildError):
            self.write(regions={"Cup": self.regions["Casing"]})
        self.assertFalse(self.path.exists() and zipfile.is_zipfile(self.path))

    def test_files_without_regions_are_byte_for_byte_the_old_structure(self):
        """Solid and webbed output must not change: the members hash as they did before this change."""
        mesh = {"points": [(x, y, z) for z in (1.0, 6.0) for y in (2.0, 5.0) for x in (3.0, 9.0)],
                "triangles": [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4),
                              (2, 6, 3), (3, 6, 7), (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)],
                "low": [3.0, 2.0, 1.0], "size_mm": [6.0, 3.0, 5.0]}
        objects = [("Casing", mesh, 1), ("Peg", mesh, 2)]
        plain, with_settings = self.path.with_name("plain.3mf"), self.path.with_name("settings.3mf")
        hutchfinity.write_3mf(plain, objects, 500.0, None)
        hutchfinity.write_3mf(with_settings, objects, 500.0, {"Casing": {"sparse_infill_density": "100%"}, "Peg": {}})
        self.assertEqual(member_hashes(plain), {
            "[Content_Types].xml": "6db89f2d2a0bc1c47ff57cead7ce9382b9251576aa57538927781ba66f5d0e38",
            "_rels/.rels": "3a48d9b7bb9f8a6d32810d91792abf721a31c6bfc6df292acb88f1d8542034a1",
            "3D/3dmodel.model": "47db6d8aabae5ffa080472dbee783c7f4d317c1c2071c1633bc3edfe76d93c51"})
        self.assertEqual(member_hashes(with_settings), {
            "[Content_Types].xml": "dc316e456379eac3581c6aed7a2d609769d6b2945b03e0f1db15a92ae50d1e45",
            "_rels/.rels": "3a48d9b7bb9f8a6d32810d91792abf721a31c6bfc6df292acb88f1d8542034a1",
            "3D/3dmodel.model": "a4b01e42c009a2926f79539f1f6440b3b99f77d9dd0db71639e91e27cc1c5392",
            "Metadata/model_settings.config": "0cc301ce20015813c47b84caa79829dcd66d12391f60fefabc52230a8726d9db"})


@unittest.skipUnless(OPENSCAD, "OpenSCAD is required for geometric evidence")
class Zones(Harness):
    """B3: the layout functions, over a size, wall, spacing and bore product."""

    def test_regions_are_the_slab_plate_plus_the_one_pillar_zone_function(self):
        sizes = ((1, 1), (2, 3), (10, 10), (12, 16))
        walls = ((18, 18), (18, 40), (40, 18), (25, 25))
        cases = [Case(x, y, h, side, back, bore, chamfer, spacing, road)
                 for (x, y), (side, back), bore, chamfer, spacing, road, h in itertools.product(
                     sizes, walls, (6, 8.45, 9), (0, 0.75), (190, 40), (1.4, 1.0), (5, 20))]
        results = self.echoes([f"[{regions_expr(c)},{zones_expr(c)},{c.pockets_expr()}]" for c in cases])
        counted = 0
        for case, (regions, zones, pockets) in zip(cases, results):
            with self.subTest(x=case.x, y=case.y, h=case.h, side=case.side, back=case.back, bore=case.bore,
                              chamfer=case.chamfer, spacing=case.spacing, road=case.road):
                self.assertEqual(len(regions), 1 + len(zones))
                self.assertEqual(regions[0], [0, 0, 0, case.width, case.depth, SLAB])
                for block, zone in zip(regions[1:], zones):
                    self.assertEqual(block, [zone[0], zone[1], 0, zone[2], zone[3], case.height])
                # The webbed layout keeps its pockets out of exactly these zones.
                for pocket in pockets:
                    for zone in zones:
                        overlap = (min(pocket[2], zone[2]) - max(pocket[0], zone[0]) > 2e-3
                                   and min(pocket[3], zone[3]) - max(pocket[1], zone[1]) > 2e-3)
                        self.assertFalse(overlap, (pocket, zone))
                counted += len(zones)
        self.assertGreater(counted, 200)

    def test_one_function_feeds_both_modes(self):
        """The source names one zone function, used by the webbed pockets and the regions alike."""
        source = CORE.read_text()
        self.assertEqual(source.count("function casing_core_pillar_zones("), 1)
        self.assertEqual(source.count("function casing_core_pillar_zone("), 1)
        for needle in ("function casing_core_pockets(", "function casing_core_regions("):
            body = source.split(needle, 1)[1].split("\nfunction ", 1)[0]
            self.assertIn("casing_core_pillar_zones(", body, needle)
        self.assertNotIn("peg_wall", source.split("function casing_core_regions(", 1)[1].split("\nfunction ", 1)[0])


@unittest.skipUnless(OPENSCAD, "OpenSCAD is required for geometric evidence")
class Geometry(Harness):
    """B2, B4, B5 and B11: the body is solid; the regions cover what they should and no more."""

    def sizes(self):
        return (Case(1, 1, 5), Case(3, 4, 5, 25, 18), Case(10, 10, 10))

    def layout(self, case):
        positions, regions = self.echoes([f"[{case.positions_expr()},{regions_expr(case)}]"])[0]
        return [tuple(p) for p in positions], [tuple(r) for r in regions]

    def test_body_is_identical_to_solid(self):
        """B2: same mesh, not just the same size."""
        for case in self.sizes():
            with self.subTest(size=(case.x, case.y, case.h)):
                solid = self.render(f"use <{ENTRY}>; {SOLID};", case.overrides())
                body = self.render(f"use <{ENTRY}>; {OPEN};", case.overrides())
                for key in ("points", "triangles", "facets", "size_mm", "low", "pieces", "closed"):
                    self.assertEqual(body[key], solid[key], key)
                self.assertAlmostEqual(body["volume_mm3"], solid["volume_mm3"], delta=1e-6 * solid["volume_mm3"])
                self.assertTrue(self.is_empty(f"use <{ENTRY}>; difference() {{ {SOLID}; {OPEN}; }}", case.overrides()))
                self.assertTrue(self.is_empty(f"use <{ENTRY}>; difference() {{ {OPEN}; {SOLID}; }}", case.overrides()))
                positions, regions = self.layout(case)
                self.assertIn(f"casing core: open-infill; regions={len(regions)}", body["log"])
                self.assertEqual(len(regions), 1 + len(positions))
                self.assertNotIn("casing core", solid["log"])

    def test_default_casing_and_webbed_are_unchanged_by_the_new_option(self):
        case = Case(1, 1, 5)
        default = self.render(f"use <{ENTRY}>; sized_casing();", case.overrides())
        solid = self.render(f"use <{ENTRY}>; {SOLID};", case.overrides())
        self.assertEqual(default["points"], solid["points"])
        self.assertEqual(default["triangles"], solid["triangles"])
        self.assertAlmostEqual(solid["volume_mm3"], 64003.0, delta=5)
        webbed = self.render(f"use <{ENTRY}>; {WEBBED};", case.overrides())
        self.assertIn("casing core: webbed", webbed["log"])
        self.assertNotIn("regions=", webbed["log"])

    def test_scad_entry_rejects_unknown_values_and_misplaced_regions(self):
        case = Case(1, 1, 5)
        for value in ("combined", "webbed,open-infill", "open_infill"):
            with self.subTest(value=value):
                self.render(f'use <{ENTRY}>; sized_casing(core="{value}");', case.overrides(),
                            assertion="unknown casing_core")
        for core in ("solid", "webbed"):
            with self.subTest(core=core):
                self.render(f'use <{ENTRY}>; sized_casing(core="{core}", output="regions");', case.overrides(),
                            assertion="regions exist only for open-infill")
        self.render(f"use <{ENTRY}>; {region(99)};", case.overrides(), assertion="casing region index out of range")
        self.render(f'use <{ENTRY}>; sized_casing(core="open-infill", output="slab");', case.overrides(),
                    assertion="unknown casing output")

    def test_each_region_is_one_exact_box_and_the_union_is_one_piece(self):
        for case in self.sizes():
            with self.subTest(size=(case.x, case.y, case.h)):
                positions, regions = self.layout(case)
                for index, (x0, y0, z0, x1, y1, z1) in enumerate(regions):
                    mesh = self.render(f"use <{ENTRY}>; {region(index)};", case.overrides())
                    self.assertEqual(mesh["pieces"], 1)
                    for got, want in zip(mesh["low"], (x0, y0, z0)):
                        self.assertAlmostEqual(got, want, delta=2e-3)
                    for got, want in zip(mesh["size_mm"], (x1 - x0, y1 - y0, z1 - z0)):
                        self.assertAlmostEqual(got, want, delta=2e-2)
                    self.assertAlmostEqual(mesh["volume_mm3"], (x1 - x0) * (y1 - y0) * (z1 - z0),
                                           delta=1e-4 * (x1 - x0) * (y1 - y0) * (z1 - z0))
                union = self.render(f"use <{ENTRY}>; {REGIONS};", case.overrides())
                self.assertEqual(union["pieces"], 1)  # every block stands on the slab plate

    def coverage_failures(self, case, text, positions, regions):
        """B4 and B5 against one region expression: what it leaves uncovered, and what it overreaches."""
        w, d, h, side, back = case.width, case.depth, case.height, case.side, case.back
        problems = []
        slab = f"intersection() {{ {SOLID}; cube([{w},{d},{SLAB}]); }}"
        if not self.is_empty(f"use <{ENTRY}>; difference() {{ {slab}; {text}; }}", case.overrides()):
            problems.append("slab not covered")
        plate = f"intersection() {{ {text}; cube([{w},{d},{SLAB}]); }}"
        if not self.is_empty(f"use <{ENTRY}>; difference() {{ cube([{w},{d},{SLAB}]); {plate}; }}", case.overrides()):
            problems.append("plate does not span the footprint")
        radius = case.radius - 0.01
        cylinders = "".join(f"translate([{p[0]},{p[1]},-1]) cylinder(r={radius},h={h + 2},$fn=64);" for p in positions)
        covered = f"intersection() {{ union() {{ {cylinders} }} cube([{w},{d},{h}]); }}"
        if not self.is_empty(f"use <{ENTRY}>; difference() {{ {covered}; {text}; }}", case.overrides()):
            problems.append("a bore block does not cover its collar cylinder")
        mesh = self.mesh_or_none(f"use <{ENTRY}>; {text};", case.overrides())
        if mesh is None:
            return problems + ["nothing"]
        if any(mesh["low"][i] < -1e-3 for i in range(3)) or any(
                mesh["low"][i] + mesh["size_mm"][i] > bound + 1e-3 for i, bound in enumerate((w, d, h))):
            problems.append("a region extends past the casing's outer planes")
        slot = (f"translate([{side + 0.01},-1,{SLAB + 0.01}]) cube([{w - 2 * side - 0.02},{d - back + 1},{h}]);")
        if not self.is_empty(f"use <{ENTRY}>; intersection() {{ {text}; {slot} }}", case.overrides()):
            problems.append("a region fills the slot")
        above = self.mesh_or_none(
            f"use <{ENTRY}>; intersection() {{ {text}; translate([-1,-1,{SLAB}]) cube([{w + 2},{d + 2},{h}]); }}",
            case.overrides())
        expected = sum((r[3] - r[0]) * (r[4] - r[1]) * (r[5] - SLAB) for r in regions[1:])
        # The zones do not overlap in these cases, so the volume above the slab is exactly the blocks'.
        if above is None or abs(above["volume_mm3"] - expected) > 1e-4 * expected:
            problems.append(f"volume above the slab {None if above is None else above['volume_mm3']} != {expected}")
        return problems

    def test_regions_cover_slab_and_bores_and_reach_no_further(self):
        for case in self.sizes():
            with self.subTest(size=(case.x, case.y, case.h)):
                positions, regions = self.layout(case)
                blocks = regions[1:]
                for a, b in itertools.combinations(blocks, 2):
                    self.assertTrue(min(a[3], b[3]) - max(a[0], b[0]) <= 0 or min(a[4], b[4]) - max(a[1], b[1]) <= 0)
                self.assertEqual(self.coverage_failures(case, REGIONS, positions, regions), [])

    def test_negative_controls_make_the_region_checks_fail(self):
        """B11: no plate, one block fewer, or a block off its zone is each caught."""
        case = Case(3, 4, 5, 25, 18)
        positions, regions = self.layout(case)
        count = len(regions)
        self.assertGreaterEqual(count, 4)
        everything = list(range(count))
        without_plate = union_of(everything[1:])
        self.assertIn("slab not covered", self.coverage_failures(case, without_plate, positions, regions))
        for dropped in (1, count - 1):
            with self.subTest(dropped=dropped):
                variant = union_of([i for i in everything if i != dropped])
                self.assertIn("a bore block does not cover its collar cylinder",
                              self.coverage_failures(case, variant, positions, regions))
        moved = union_of(everything, shift={1: [0, 3, 0]})
        self.assertTrue(self.coverage_failures(case, moved, positions, regions))
        bulged = f"union() {{ {REGIONS}; translate([{case.side},5,{SLAB + 1}]) cube([5,5,5]); }}"
        self.assertTrue(self.coverage_failures(case, bulged, positions, regions))


@unittest.skipUnless(OPENSCAD, "OpenSCAD is required for geometric evidence")
class Generator(unittest.TestCase):
    """B6 to B10 on real builds: structure, no silent enabling, texts, manifest, round trips."""

    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.out)
        cls.builds = {}

    @classmethod
    def build(cls, core, mode):
        """One module build per (core, print mode), kept for every test that reads it."""
        key = (core, mode)
        if key not in cls.builds:
            printing = {"geometry": lambda: print_settings.print_options(geometry_only=True),
                        "process": lambda: print_settings.print_options(PROCESS),
                        "avoid": lambda: print_settings.print_options(avoid_crossings=True)}[mode]()
            result = hutchfinity.build_module(1, 1, 5, "integral-grid", cls.out / f"{core}-{mode}",
                                              {"casing_core": core}, printing)
            folder = Path(result["path"])
            cls.builds[key] = (folder, json.loads((folder / "manifest.json").read_text()),
                               json.loads((folder / "print-settings.json").read_text()))
        return cls.builds[key]

    def casing_parts(self, folder):
        objects, items, config = read_project(folder / "2-casing.3mf")
        return objects, items, config

    def test_open_infill_casing_job_is_one_object_of_parts(self):
        """B6: body plus regions as parts of one object, with the zero-top keys on the object."""
        folder, manifest, _ = self.build("open-infill", "process")
        objects, items, config = self.casing_parts(folder)
        self.assertEqual(len(items), 1)
        object_id = items[0].attrib["objectid"]
        components = objects[object_id].findall(f"{NS}components/{NS}component")
        regions = manifest["casing_core"]["regions"]
        self.assertEqual(len(components), 1 + len(regions))
        meta, parts = config_object(config, object_id)
        self.assertEqual((meta["top_shell_layers"], meta["top_shell_thickness"]), ("0", "0"))
        self.assertEqual(meta["layer_height"], "0.2")  # the process's own values stay
        self.assertEqual([p[1] for p in parts], ["normal_part"] + ["modifier_part"] * len(regions))
        for _, _, part_meta in parts[1:]:
            self.assertEqual({k: part_meta[k] for k in SOLID_REGION_SETTINGS}, SOLID_REGION_SETTINGS)
        body = objects[components[0].attrib["objectid"]]
        solid_folder, _, _ = self.build("solid", "process")
        solid_objects, solid_items, _ = read_project(solid_folder / "2-casing.3mf")
        solid_body = solid_objects[solid_items[0].attrib["objectid"]]
        self.assertEqual(vertices(body), vertices(solid_body))  # the body part is the solid mesh
        for component, record in zip(components[1:], regions):
            low, size = extent(objects[component.attrib["objectid"]])
            for got, want in zip(size, record["size_mm"]):
                self.assertAlmostEqual(got, want, delta=0.02)
            self.assertAlmostEqual(low[2], record["low_mm"][2], delta=2e-2)
        plate, blocks = regions[0], regions[1:]
        self.assertEqual(plate["kind"], "slab-plate")
        self.assertEqual(plate["z_range_mm"], [0, SLAB])
        self.assertEqual(plate["size_mm"][:2], manifest["sizes_mm"]["casing"][:2])
        self.assertTrue(all(b["kind"] == "bore-block" and b["z_range_mm"][0] == 0 and
                            abs(b["z_range_mm"][1] - manifest["sizes_mm"]["casing"][2]) < 0.02 for b in blocks))
        self.assertEqual(len(blocks), manifest["peg_total"])
        # The other jobs are plain objects: no components, no modifier parts, no zero top shells.
        for name in ("1-tub.3mf", "3-pegs-and-pull.3mf"):
            objects, items, config = read_project(folder / name)
            self.assertFalse(any(o.find(f"{NS}components") is not None for o in objects.values()), name)
            self.assertNotIn("modifier_part", ET.tostring(config, encoding="unicode"), name)
            for obj in config.findall("object"):
                self.assertEqual(
                    {m.attrib["value"] for m in obj.findall("metadata") if m.attrib["key"] == "top_shell_layers"},
                    {"4"}, name)

    def test_solid_and_webbed_casing_jobs_have_no_regions_and_no_forced_zero_top(self):
        """B6 and B7: other values, with or without a process, never carry region parts or zero top shells."""
        for core in ("solid", "webbed"):
            for mode in ("geometry", "process", "avoid"):
                with self.subTest(core=core, mode=mode):
                    folder, manifest, recorded = self.build(core, mode)
                    objects, items, config = self.casing_parts(folder)
                    self.assertFalse(any(o.find(f"{NS}components") is not None for o in objects.values()))
                    self.assertEqual(len(objects), 1)
                    if mode == "geometry":
                        self.assertIsNone(config)
                    else:
                        self.assertNotIn("modifier_part", ET.tostring(config, encoding="unicode"))
                        meta, parts = config_object(config, items[0].attrib["objectid"])
                        self.assertEqual(parts, [])
                        self.assertNotEqual(meta.get("top_shell_layers"), "0")
                        self.assertNotEqual(meta.get("top_shell_thickness"), "0")
                    text = json.dumps(recorded)
                    self.assertNotIn('"top_shell_layers": "0"', text)
                    self.assertNotIn('"top_shell_thickness": "0"', text)
                    self.assertNotIn("regions", manifest["casing_core"])
                    self.assertNotIn('"regions"', text)
                    if core == "solid":
                        self.assertEqual(manifest["casing_core"], {"mode": "solid"})

    def test_geometry_only_open_infill_lists_settings_and_embeds_nothing(self):
        """B7: geometry-only output is plain; the settings are recommended, not embedded, and no region is exported."""
        folder, manifest, recorded = self.build("open-infill", "geometry")
        for name in ("1-tub.3mf", "2-casing.3mf", "3-pegs-and-pull.3mf"):
            objects, items, config = read_project(folder / name)
            self.assertIsNone(config, name)
            self.assertFalse(any(o.find(f"{NS}components") is not None for o in objects.values()), name)
        casing = next(j for j in recorded["jobs"] if j["file"] == "2-casing.3mf")["parts"]["Casing"]
        self.assertEqual(casing["applied_overrides"], {})
        self.assertEqual(casing["recommended_overrides"]["top_shell_layers"], "0")
        self.assertEqual(casing["recommended_overrides"]["top_shell_thickness"], "0")
        self.assertFalse(casing["regions"]["embedded"])
        self.assertFalse(manifest["casing_core"]["regions_embedded"])
        guide = (folder / "PRINTING.md").read_text()
        self.assertIn("Recommended, not embedded", guide)
        self.assertIn("top_shell_layers=0", guide)
        self.assertIn("not embedded", guide.split("Regions", 1)[1])
        # The casing 3MF is the plain solid file: nothing a slicer could print as extra material.
        solid_folder, _, _ = self.build("solid", "geometry")
        self.assertEqual(vertices(read_project(folder / "2-casing.3mf")[0]["1"]),
                         vertices(read_project(solid_folder / "2-casing.3mf")[0]["1"]))

    def test_print_context_is_in_the_guide_and_the_structured_record(self):
        """B8: PRINTING.md and print-settings.json state every item, for a process and an avoid-crossings run."""
        text = print_settings.CASING_CORE_ASSUMPTIONS["open-infill"]
        for mode in ("geometry", "process", "avoid"):
            with self.subTest(mode=mode):
                folder, manifest, recorded = self.build("open-infill", mode)
                guide = (folder / "PRINTING.md").read_text()
                self.assertIn(text, guide)
                self.assertEqual(recorded["casing_core"], {"mode": "open-infill", "assumptions": text})
                casing = next(j for j in recorded["jobs"] if j["file"] == "2-casing.3mf")["parts"]["Casing"]
                regions = casing["regions"]
                self.assertEqual(regions["settings"], SOLID_REGION_SETTINGS)
                self.assertEqual(regions["count"], len(regions["items"]))
                self.assertEqual(regions["count"], 1 + manifest["peg_total"])
                self.assertEqual(regions["embedded"], mode != "geometry")
                self.assertEqual(guide.count("| slab-plate |"), 1)
                self.assertEqual(guide.count("| bore-block |"), manifest["peg_total"])
                for item in regions["items"]:
                    self.assertEqual(set(item), {"kind", "low_mm", "size_mm", "z_range_mm"})
                if mode == "geometry":
                    self.assertIn("not embedded in this file", guide)
                else:
                    self.assertIn("embedded in this file", guide)
                    self.assertNotIn("not embedded in this file", guide)
                if mode == "avoid":
                    self.assertEqual(casing["applied_overrides"]["sparse_infill_pattern"], "tpmsd")
                if mode != "geometry":
                    self.assertEqual(casing["applied_overrides"]["top_shell_layers"], "0")
                    self.assertEqual(casing["applied_overrides"]["top_shell_thickness"], "0")
                for name in ("Tub", "Peg", "Pull"):
                    for job in recorded["jobs"]:
                        if name in job["parts"]:
                            self.assertNotEqual(job["parts"][name]["applied_overrides"].get("top_shell_layers"), "0")
                            self.assertNotIn("regions", job["parts"][name])

    def test_manifest_records_regions_and_counts_one_printed_solid(self):
        """B9."""
        folder, manifest, _ = self.build("open-infill", "process")
        record = manifest["casing_core"]
        self.assertEqual(record["mode"], "open-infill")
        self.assertEqual(record["region_count"], len(record["regions"]))
        self.assertEqual(record["region_count"], 1 + manifest["peg_total"])
        self.assertTrue(record["regions_embedded"])
        self.assertEqual(manifest["design_overrides"], {"casing_core": "open-infill"})
        casing_file = next(f for f in manifest["files"] if f["file"] == "2-casing.3mf")
        self.assertEqual(casing_file["parts"], {"Casing": 1})  # regions are not printed solids
        solid_manifest = self.build("solid", "process")[1]
        self.assertEqual(manifest["sizes_mm"], solid_manifest["sizes_mm"])
        self.assertEqual(manifest["facets"], solid_manifest["facets"])
        mesh = hutchfinity.render("casing", 1, 1, 5, "integral-grid", {"casing_core": "open-infill"})
        self.assertTrue(mesh["closed"])
        self.assertEqual(mesh["pieces"], 1)
        self.assertEqual(mesh["facets"], solid_manifest["facets"]["casing"])

    def test_cli_and_form_round_trip_the_value_into_the_manifest(self):
        """B10: the CLI builds it, and the form's value reaches the same manifest."""
        out = self.out / "cli"
        run = subprocess.run([sys.executable, str(ROOT / "hutchfinity.py"), "1", "1", "5",
                              "--casing-core", "open-infill", "--out", str(out)], text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        folder = Path(json.loads(run.stdout)["path"])
        manifest = json.loads((folder / "manifest.json").read_text())
        self.assertEqual(manifest["design_overrides"], {"casing_core": "open-infill"})
        self.assertEqual(manifest["casing_core"]["mode"], "open-infill")
        _, _, design = hutchfinity.parse_form({"x": "1", "y": "1", "h": "5", "casing_core": "open-infill"})
        self.assertEqual(design, manifest["design_overrides"])


if __name__ == "__main__":
    unittest.main()
