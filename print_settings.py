"""Small, explicit Orca process overrides for generated print jobs.

These are per-object settings, not resolved printer/filament/process bundles.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path


class PrintSettingsError(ValueError):
    pass


PROCESS_KEYS = {
    "layer_height", "line_width", "outer_wall_line_width", "inner_wall_line_width",
    "sparse_infill_line_width", "internal_solid_infill_line_width", "top_surface_line_width",
    "sparse_infill_density", "sparse_infill_pattern", "fill_multiline", "wall_loops",
    "top_shell_layers", "bottom_shell_layers", "top_shell_thickness", "bottom_shell_thickness",
}
INTEGER_KEYS = {"fill_multiline", "wall_loops", "top_shell_layers", "bottom_shell_layers"}
PATTERNS = {
    "rectilinear", "alignedrectilinear", "zigzag", "crosszag", "lockedzag", "line", "grid",
    "triangles", "tri-hexagon", "cubic", "adaptivecubic", "quartercubic", "supportcubic",
    "lightning", "honeycomb", "3dhoneycomb", "lateral-honeycomb", "lateral-lattice",
    "crosshatch", "tpmsd", "tpmsfk", "gyroid", "concentric", "hilbertcurve",
    "archimedeanchords", "octagramspiral",
}
ORIENTATIONS = {
    "Tub": "floor on the bed; opening upward",
    "Casing": "riding slab on the bed; side/back walls upward; invert for installation",
    "Peg": "laid on a flat face, as generated",
    "Pull": "glue face on the bed, as generated",
    "Grid": "flat on the bed, as generated",
    "Cup": "base on the bed; opening upward",
}
INHERITANCE_NOTE = (
    "Only the listed object overrides are included. All other settings come from the receiving "
    "slicer, including its printer, filament, first-layer settings, speeds, temperatures, flow, "
    "solid-infill path pattern, and G-code. A process JSON's inherits reference is not resolved. Select the intended "
    "receiver profiles and inspect the slice before printing."
)
IMPORT_NOTE = (
    "Representative tub, casing and accessory jobs retained these per-object settings through "
    "OrcaSlicer 2.5.0 CLI project import/export, including every peg copy. GUI import, slicing and "
    "physical printing remain untested. Settings target Orca, including for Bambu printers used "
    "through Orca. Bambu Studio compatibility is unqualified; apply compatible settings manually "
    "from this guide and inspect the slice."
)


# One table feeds the app note, PRINTING.md and print-settings.json, so they cannot disagree.
CASING_CORE_ASSUMPTIONS = {
    "solid": "Solid casing walls: no assumption beyond the settings of the receiving slicer.",
    "webbed": (
        "Webbed casing walls: the model replaces the infill. Casing infill is recommended at 100% with a "
        "solid-compatible pattern, so any gap residue prints solid. One wall loop per contour is assumed "
        "for the skins and webs, which are two roads wide, with no crossing pattern needed. The pockets are open at the "
        "feet and need no bridging."
    ),
    "open-infill": (
        "Open infill: the casing prints as the solid model with its top surfaces off, so slicer infill shows "
        "where a top skin would have been. The casing job sets top_shell_layers=0 and top_shell_thickness=0, "
        "applied as per-object settings when print settings are embedded and otherwise recommended, not embedded. "
        "They apply to the casing job only, never to the tub, pegs or pull, and only because this mode was chosen. "
        "Setting regions, which the slicer treats as settings and not as printed material, ask for solid fill "
        "(sparse_infill_density=100% with a solid-compatible pattern): one slab plate over the whole footprint "
        "from the bed to the top of the riding slab, and one bore block around each peg bore from the bed to the "
        "feet. Walls elsewhere keep the interior infill of the selected process or the avoid-crossings choice. "
        "This mode only makes sense with top surfaces off. If the receiving slicer drops per-object settings or "
        "region bodies, the casing prints as the solid model with that slicer on its own defaults: no failure, but not "
        "this mode. A slicer that does not understand modifier parts could print the regions as material, so check "
        "the preview before slicing: infill, not skin, in the last layers at the feet; solid layers through the "
        "slab; solid fill around each bore; and no slab over the slot. Neither this mode nor the 3MF region path "
        "is qualified on a native slicer or printed."
    ),
}
# Open infill: what the casing job's setting regions ask for, and the shells it turns off.
CASING_REGION_SETTINGS = {"sparse_infill_density": "100%", "sparse_infill_pattern": "rectilinear"}
OPEN_INFILL_TOP_SETTINGS = {"top_shell_layers": "0", "top_shell_thickness": "0"}
DEFAULT_CORE_ROAD = 1.4


def casing_core_assumption(value) -> str:
    if not isinstance(value, str) or value not in CASING_CORE_ASSUMPTIONS:
        raise PrintSettingsError(f"unknown casing_core: {value!r}")
    return CASING_CORE_ASSUMPTIONS[value]


def core_road(options: "PrintOptions") -> tuple[float, str]:
    """One deposited road for the webbed core: the selected process's wall line width, else the default."""
    for key in ("outer_wall_line_width", "line_width"):
        raw = options.process.get(key)
        if raw is not None and not raw.endswith("%"):
            width = float(raw)
            if width > 0:
                return width, key
    return DEFAULT_CORE_ROAD, "default"


def setting_value(key: str, raw) -> str:
    """Validate the supported setting's scalar value and return Orca serialization."""
    if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
        raise PrintSettingsError(f"{key} must have one scalar value")
    value = str(raw).strip()
    if key == "sparse_infill_pattern":
        if value not in PATTERNS:
            raise PrintSettingsError(f"unsupported sparse infill pattern: {value}")
        return value
    density = key == "sparse_infill_density"
    percent = density or (key.endswith("line_width") and value.endswith("%"))
    try:
        number = float(value.removesuffix("%") if percent else value)
    except ValueError:
        raise PrintSettingsError(f"{key} must be numeric") from None
    if not math.isfinite(number):
        raise PrintSettingsError(f"{key} must be finite")
    if key in INTEGER_KEYS:
        if not number.is_integer() or number < (1 if key == "fill_multiline" else 0):
            raise PrintSettingsError(f"{key} must be a non-negative integer" if key != "fill_multiline"
                                     else "fill_multiline must be an integer from 1 to 10")
        if key == "fill_multiline" and number > 10:
            raise PrintSettingsError("fill_multiline must be an integer from 1 to 10")
        if key == "wall_loops" and number > 1000:
            raise PrintSettingsError("wall_loops must be from 0 to 1000")
        return str(int(number))
    elif density:
        if not 0 <= number <= 100:
            raise PrintSettingsError("sparse_infill_density must be from 0% to 100%")
    elif number < 0 or (key == "layer_height" and number == 0):
        raise PrintSettingsError(f"{key} must be {'positive' if key == 'layer_height' else 'non-negative'}")
    return f"{number:g}" + ("%" if percent else "")


@dataclass
class PrintOptions:
    process: dict[str, str] = field(default_factory=dict)
    avoid_crossings: bool = False
    geometry_only: bool = True
    profile_name: str | None = None
    inherits: str | None = None
    ignored_fields: list[str] = field(default_factory=list)
    compatible_printers: list[str] = field(default_factory=list)

    def record(self) -> dict:
        return {
            "mode": "geometry-only" if self.geometry_only else "selected-process-overrides",
            "avoid_crossings": self.avoid_crossings,
            "process_profile": self.profile_name,
            "unresolved_inherits": self.inherits,
            "selected_process_overrides": self.process,
            "ignored_profile_fields": self.ignored_fields,
            "declared_compatible_printers": self.compatible_printers,
        }


def print_options(profile: dict | None = None, *, profile_name: str | None = None,
                  avoid_crossings: bool = False, geometry_only: bool = False) -> PrintOptions:
    if type(avoid_crossings) is not bool or type(geometry_only) is not bool:
        raise PrintSettingsError("print mode options must be true or false")
    if profile_name is not None and not isinstance(profile_name, str):
        raise PrintSettingsError("process profile name must be text")
    if geometry_only and (profile is not None or avoid_crossings):
        raise PrintSettingsError("geometry-only mode cannot apply a process profile or avoid-crossings override")
    options = PrintOptions(avoid_crossings=avoid_crossings,
                           geometry_only=geometry_only or (profile is None and not avoid_crossings))
    if profile is None:
        return options
    if not isinstance(profile, dict):
        raise PrintSettingsError("select one exported Orca process JSON object")
    declared_type = profile.get("type")
    process_id = profile.get("print_settings_id")
    process_marker = isinstance(process_id, str) and bool(process_id.strip())
    if (declared_type not in (None, "process")
            or "printer_settings_id" in profile or "filament_settings_id" in profile
            or (declared_type is None and not process_marker)):
        raise PrintSettingsError("select one Orca process JSON (type=process or print_settings_id); printer, filament, and project files are not accepted")
    options.process = {key: setting_value(key, value) for key, value in profile.items() if key in PROCESS_KEYS}
    options.profile_name = profile_name or str(profile.get("name", "selected process JSON"))
    if profile.get("inherits") and not isinstance(profile["inherits"], str):
        raise PrintSettingsError("process inherits must be a preset name")
    options.inherits = profile.get("inherits") or None
    compatible = profile.get("compatible_printers", [])
    if isinstance(compatible, list) and all(isinstance(item, str) for item in compatible):
        options.compatible_printers = compatible
    options.ignored_fields = sorted(set(profile) - PROCESS_KEYS - {"type", "name", "inherits", "print_settings_id", "compatible_printers"})
    return options


def load_print_options(path: Path | None = None, *, avoid_crossings=False, geometry_only=False) -> PrintOptions:
    try:
        profile = json.loads(path.read_text()) if path else None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PrintSettingsError(f"could not read process JSON: {error}") from None
    return print_options(profile, profile_name=path.name if path else None,
                         avoid_crossings=avoid_crossings, geometry_only=geometry_only)


def part_record(name: str, copies: int, options: PrintOptions, floor_mm: float | None = None,
                casing_core: str = "solid", regions: list[dict] | None = None) -> dict:
    casing_core_assumption(casing_core)
    recommended: dict[str, str] = {}
    reasons = []
    open_infill = name == "Casing" and casing_core == "open-infill"
    if open_infill:
        recommended.update(OPEN_INFILL_TOP_SETTINGS)
        reasons.append("Open-infill casing: top shells are off for this casing only (top_shell_layers=0, "
                       "top_shell_thickness=0) because open infill was chosen. Setting regions keep the slab and every "
                       "peg bore solid.")
    if name == "Casing" and casing_core == "webbed":
        recommended.update(sparse_infill_density="100%", sparse_infill_pattern="rectilinear", fill_multiline="1")
        reasons.append("Webbed casing: 100% infill with a solid-compatible sparse pattern, so any gap residue prints solid. "
                       "The actual solid-infill path pattern remains the receiver's setting.")
        if options.avoid_crossings:
            reasons.append("Avoid-crossings is not applied: a webbed casing has no sparse infill crossings to avoid.")
    if name in {"Peg", "Pull"}:
        recommended.update(sparse_infill_density="100%", sparse_infill_pattern="rectilinear", fill_multiline="1")
        reasons.append("Solid accessory: 100% infill with a solid-compatible sparse pattern. The actual solid-infill path pattern remains the receiver's setting.")
    if name == "Casing" and options.avoid_crossings and casing_core in ("solid", "open-infill"):
        recommended["sparse_infill_pattern"] = "tpmsd"
        reasons.append("Avoid-crossings choice uses TPMS-D for casing sparse infill; density stays inherited unless selected.")
    if floor_mm is not None:
        recommended["bottom_shell_layers"] = str(max(1, int(options.process.get("bottom_shell_layers", "1"))))
        recommended["bottom_shell_thickness"] = f"{max(floor_mm, float(options.process.get('bottom_shell_thickness', '0'))):g}"
        reasons.append(f"Keep the bed-facing authored floor/slab solid through at least {floor_mm:g} mm and one bottom layer.")
    applied = {} if options.geometry_only else {**options.process, **recommended}
    record = {
        "copies": copies,
        "orientation": ORIENTATIONS[name],
        "recommended_overrides": recommended,
        "applied_overrides": applied,
        "reasons": reasons,
    }
    if open_infill:
        items = list(regions or [])
        record["regions"] = {"embedded": not options.geometry_only, "settings": dict(CASING_REGION_SETTINGS),
                             "count": len(items), "items": items}
    return record


def region_lines(regions: dict) -> list[str]:
    """The casing job's setting regions: what they ask for, where they are, and whether the file carries them."""
    settings = ", ".join(f"`{key}={value}`" for key, value in regions["settings"].items())
    lines = [f"**Regions** ({regions['count']}, setting regions and not printed material): {settings}.", ""]
    if regions["embedded"]:
        lines += ["The regions are embedded in this file as modifier parts of the casing object.", ""]
    else:
        lines += ["The regions are not embedded in this file because it is geometry only. To use this mode, add "
                  "modifier regions with these settings by hand at the positions below, or print the plain solid casing.", ""]
    lines += ["| Region | Position x, y, z (mm) | Size x, y, z (mm) | z range (mm) |", "|---|---|---|---|"]
    for item in regions["items"]:
        lines.append(f"| {item['kind']} | {', '.join(f'{v:g}' for v in item['low_mm'])} | "
                     f"{', '.join(f'{v:g}' for v in item['size_mm'])} | "
                     f"{item['z_range_mm'][0]:g} to {item['z_range_mm'][1]:g} |")
    return lines + [""]


def write_printing_files(folder: Path, jobs: list[dict], options: PrintOptions, *, stem: str = "",
                         casing_core: str = "solid") -> list[Path]:
    """Keep a small, human-readable companion and exact values beside the print files."""
    json_path = folder / (f"{stem}.print-settings.json" if stem else "print-settings.json")
    md_path = folder / (f"{stem}.PRINTING.md" if stem else "PRINTING.md")
    assumption = casing_core_assumption(casing_core)
    record = {"version": 1, **options.record(), "casing_core": {"mode": casing_core, "assumptions": assumption},
              "inheritance": INHERITANCE_NOTE, "import_status": IMPORT_NOTE, "jobs": jobs}
    json_path.write_text(json.dumps(record, indent=2) + "\n")
    lines = ["# Printing", "", "Geometry only: no settings are embedded." if options.geometry_only else
             "These files include selected process overrides plus the part recommendations below.", "", INHERITANCE_NOTE, "", IMPORT_NOTE, ""]
    lines += [f"Casing core: {casing_core}. {assumption}", ""]
    if options.profile_name:
        lines += [f"Selected process JSON: {options.profile_name}.", ""]
    if options.inherits:
        lines += [f"Unresolved parent preset: {options.inherits}.", ""]
    if options.compatible_printers:
        lines += ["The selected JSON declares compatibility with: " + "; ".join(options.compatible_printers)
                  + ". This description does not select or configure a printer.", ""]
    for job in jobs:
        lines += [f"## {job['file']}", ""]
        for name, part in job["parts"].items():
            lines += [f"**{name} × {part['copies']}** — {part['orientation']}.", ""]
            settings = part["applied_overrides"]
            if settings:
                lines += ["| Applied setting | Value |", "|---|---|"]
                lines += [f"| `{key}` | `{value}` |" for key, value in sorted(settings.items())]
                lines.append("")
            else:
                lines += ["No object settings applied; use the receiving slicer's settings.", ""]
            lines += part["reasons"] + ([""] if part["reasons"] else [])
            if "regions" in part:
                lines += region_lines(part["regions"])
            if options.geometry_only and part["recommended_overrides"]:
                lines += ["Recommended, not embedded: " + "; ".join(f"{k}={v}" for k, v in part["recommended_overrides"].items()) + ".", ""]
    lines += ["Recommendations do not establish physical print performance. No G-code is generated or sent.", ""]
    md_path.write_text("\n".join(lines))
    return [json_path, md_path]
