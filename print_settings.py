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


def part_record(name: str, copies: int, options: PrintOptions, floor_mm: float | None = None) -> dict:
    recommended: dict[str, str] = {}
    reasons = []
    if name in {"Peg", "Pull"}:
        recommended.update(sparse_infill_density="100%", sparse_infill_pattern="rectilinear", fill_multiline="1")
        reasons.append("Solid accessory: 100% infill with a solid-compatible sparse pattern. The actual solid-infill path pattern remains the receiver's setting.")
    if name == "Casing" and options.avoid_crossings:
        recommended["sparse_infill_pattern"] = "tpmsd"
        reasons.append("Avoid-crossings choice uses TPMS-D for casing sparse infill; density stays inherited unless selected.")
    if floor_mm is not None:
        recommended["bottom_shell_layers"] = str(max(1, int(options.process.get("bottom_shell_layers", "1"))))
        recommended["bottom_shell_thickness"] = f"{max(floor_mm, float(options.process.get('bottom_shell_thickness', '0'))):g}"
        reasons.append(f"Keep the bed-facing authored floor/slab solid through at least {floor_mm:g} mm and one bottom layer.")
    applied = {} if options.geometry_only else {**options.process, **recommended}
    return {
        "copies": copies,
        "orientation": ORIENTATIONS[name],
        "recommended_overrides": recommended,
        "applied_overrides": applied,
        "reasons": reasons,
    }


def write_printing_files(folder: Path, jobs: list[dict], options: PrintOptions, *, stem: str = "") -> list[Path]:
    """Keep a small, human-readable companion and exact values beside the print files."""
    json_path = folder / (f"{stem}.print-settings.json" if stem else "print-settings.json")
    md_path = folder / (f"{stem}.PRINTING.md" if stem else "PRINTING.md")
    record = {"version": 1, **options.record(), "inheritance": INHERITANCE_NOTE, "import_status": IMPORT_NOTE, "jobs": jobs}
    json_path.write_text(json.dumps(record, indent=2) + "\n")
    lines = ["# Printing", "", "Geometry only: no settings are embedded." if options.geometry_only else
             "These files include selected process overrides plus the part recommendations below.", "", INHERITANCE_NOTE, "", IMPORT_NOTE, ""]
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
            if options.geometry_only and part["recommended_overrides"]:
                lines += ["Recommended, not embedded: " + "; ".join(f"{k}={v}" for k, v in part["recommended_overrides"].items()) + ".", ""]
    lines += ["Recommendations do not establish physical print performance. No G-code is generated or sent.", ""]
    md_path.write_text("\n".join(lines))
    return [json_path, md_path]
