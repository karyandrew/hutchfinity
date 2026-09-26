from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/hutchfinity_catalog.py"
SPEC = importlib.util.spec_from_file_location("hutchfinity_catalog", SCRIPT)
assert SPEC and SPEC.loader
catalog_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog_module)


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads((ROOT / "catalog/bin-skus.json").read_text())
        cls.classes = json.loads((ROOT / "catalog/item-classes.json").read_text())
        cls.maps = json.loads((ROOT / "catalog/item-class-map.json").read_text())

    def test_source_revision_survives_catalog_commit_but_changes_with_geometry(self) -> None:
        environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        environment.update({"GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"})
        with tempfile.TemporaryDirectory(prefix="catalog-revision-") as raw:
            root = Path(raw)
            def git(*args: str) -> str:
                return subprocess.check_output(["git", *args], cwd=root, env=environment, text=True).strip()
            git("init", "--quiet")
            source = root / catalog_module.CUP_SOURCE
            source.parent.mkdir(parents=True)
            source.write_text("// owned synthetic geometry revision one\n")
            git("add", ".")
            git("commit", "--quiet", "-m", "source")
            source_head = git("rev-parse", "HEAD")
            with mock.patch.object(catalog_module, "ROOT", root):
                self.assertEqual(source_head, catalog_module.source_commit())
                (root / "catalog.json").write_text('{"source_commit":"' + source_head + '"}\n')
                git("add", ".")
                git("commit", "--quiet", "-m", "catalog")
                self.assertNotEqual(source_head, git("rev-parse", "HEAD"))
                self.assertEqual(source_head, catalog_module.source_commit())
                source.write_text("// owned synthetic geometry revision two\n")
                git("add", ".")
                git("commit", "--quiet", "-m", "changed source")
                self.assertEqual(git("rev-parse", "HEAD"), catalog_module.source_commit())
                self.assertNotEqual(source_head, catalog_module.source_commit())

    def test_source_revision_refuses_shallow_history(self) -> None:
        environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        environment.update({
            "GIT_AUTHOR_NAME": "Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        })
        with tempfile.TemporaryDirectory(prefix="catalog-shallow-") as raw:
            root = Path(raw)
            source_repo = root / "source"
            shallow_repo = root / "shallow"
            source_repo.mkdir()

            def git(cwd: Path, *args: str) -> str:
                return subprocess.check_output(
                    ["git", *args], cwd=cwd, env=environment, text=True,
                ).strip()

            git(source_repo, "init", "--quiet")
            source = source_repo / catalog_module.CUP_SOURCE
            source.parent.mkdir(parents=True)
            source.write_text("// owned synthetic geometry revision one\n")
            git(source_repo, "add", ".")
            git(source_repo, "commit", "--quiet", "-m", "source one")
            source.write_text("// owned synthetic geometry revision two\n")
            git(source_repo, "add", ".")
            git(source_repo, "commit", "--quiet", "-m", "source two")
            subprocess.run(
                [
                    "git", "clone", "--quiet", "--depth", "1",
                    source_repo.resolve().as_uri(), str(shallow_repo),
                ],
                check=True,
                env=environment,
            )
            self.assertEqual("true", git(shallow_repo, "rev-parse", "--is-shallow-repository"))
            with mock.patch.object(catalog_module, "ROOT", shallow_repo):
                with self.assertRaisesRegex(ValueError, "full Git history is required"):
                    catalog_module.source_commit()

    @staticmethod
    def passing_receipt(mapping: dict) -> dict:
        artifact_hash = next(row["sha256"] for row in mapping["source_and_output_hashes"] if row["path"].endswith(".stl"))
        return {
            "schema": "hutchfinity-physical-fit-receipt/v1",
            "receipt_id": mapping["physical_fit_receipt"],
            "item_class_id": mapping["item_class_id"],
            "item_class_hash": mapping["item_class_hash"],
            "sku": mapping["preferred_sku"],
            "artifact_sha256": artifact_hash,
            "validation_lane": mapping["validation_lane"],
            "validation_receipt": mapping["validation_receipt"],
            "sample_kind": "dimensional_surrogate",
            "sample_dimensions_mm": {"x": 49.0, "y": 49.0, "z": 30.0},
            "sample_uncertainty_mm": {"x": 0.5, "y": 0.5, "z": 0.5},
            "tested_quantity": 1,
            "checks": {
                "load_unload": "pass",
                "quantity": "pass",
                "retrieval": "pass",
                "adjacent_interference": "pass",
                "base_engagement": "pass",
                "ordinary_handling": "pass",
            },
            "workarounds": [],
            "result": "pass",
            "performed_at": "2026-09-25T00:00:00Z",
        }

    @staticmethod
    def demand_request(quantity: object = 1) -> dict:
        return {
            "manifest_id": "neutral-test",
            "as_of": "2026-09-25T00:00:00Z",
            "artifact_demands": [{
                "item_class_id": "square-stack-49",
                "required_quantity": quantity,
                "allowed_materials": ["test-material"],
                "allowed_colors": [],
                "priority_class": "test",
            }],
        }

    @staticmethod
    def accepted_maps(maps: dict) -> dict:
        accepted = copy.deepcopy(maps)
        accepted["mappings"][1].update({
            "selection_status": "ACCEPTED",
            "physical_fit_state": "pass",
            "physical_fit_receipt": "fit-one",
            "validation_lane": "lane-one",
            "validation_receipt": "validation-one",
        })
        return accepted

    @staticmethod
    def subprocess_environment() -> dict[str, str]:
        environment = os.environ.copy()
        for key in catalog_module.GIT_SELECTOR_ENV:
            environment.pop(key, None)
        environment["GIT_WORK_TREE"] = str(ROOT)
        environment["GIT_PAGER"] = "cat"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return environment

    def run_cli(self, *arguments: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(argument) for argument in arguments)],
            cwd=ROOT,
            env=self.subprocess_environment(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    @staticmethod
    def write_json(path: Path, value: object) -> None:
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_generated_artifacts_are_current(self) -> None:
        self.assertEqual(catalog_module.build_catalog(), self.catalog)
        self.assertEqual(catalog_module.select_all(self.classes, self.catalog), self.maps)

    def test_inventory_separates_managed_from_unmanaged_outputs(self) -> None:
        self.assertEqual(
            self.catalog["inventory_summary"],
            {
                "tracked_bin_outputs": 126,
                "build_managed_outputs": 22,
                "tracked_unmanaged_outputs": 104,
                "source_output_links_reproduced": 0,
            },
        )

    def test_source_dimensions_are_not_nominal_cell_math(self) -> None:
        sku = next(row for row in self.catalog["items"] if row["sku"] == "bin-2x9x10h")
        self.assertEqual(sku["verified_internal_bounds_mm"]["wall_span_mm"], {"x": 39.1, "y": 186.1, "z": 33.04})
        self.assertEqual(sku["verified_internal_bounds_mm"]["conservative_flat_floor_span_mm"], {"x": 34.0, "y": 181.0})
        self.assertNotEqual(sku["verified_internal_bounds_mm"]["wall_span_mm"]["y"], 9 * 21)

    def test_initial_selection_and_fallbacks(self) -> None:
        mappings = {row["item_class_id"]: row for row in self.maps["mappings"]}
        self.assertEqual(mappings["long-rod-178"]["preferred_sku"], "bin-2x9x10h")
        self.assertEqual(mappings["long-rod-178"]["fallback_skus"], ["bin-2x10x10h"])
        self.assertEqual(mappings["square-stack-49"]["preferred_sku"], "bin-3x3x10h")
        self.assertEqual(mappings["square-stack-49"]["fallback_skus"], ["bin-3x5x10h"])
        self.assertEqual(mappings["short-roll-40x15"]["preferred_sku"], "bin-2x4x10h")
        self.assertEqual(mappings["short-roll-40x15"]["fallback_skus"], ["bin-2x5x10h"])
        self.assertEqual(mappings["flat-185x82x13"]["preferred_sku"], "bin-5x9x5h")
        self.assertEqual(mappings["flat-185x82x13"]["fallback_skus"], [])
        self.assertTrue(all(row["selection_status"] == "PROVISIONAL" for row in mappings.values()))
        self.assertTrue(all(row["physical_fit_state"] == "not_run" for row in mappings.values()))

    def test_quantity_constraint_changes_selection(self) -> None:
        item = copy.deepcopy(next(row for row in self.classes["items"] if row["item_class_id"] == "short-roll-40x15"))
        item["minimum_quantity_per_bin"] = 3
        result = catalog_module.select_item(item, self.catalog)
        self.assertEqual(result["preferred_sku"], "bin-2x5x10h")
        self.assertGreaterEqual(result["quantity_capacity"], 3)

    def test_flat_object_wall_bbox_is_not_treated_as_fit_oracle(self) -> None:
        mapping = next(row for row in self.maps["mappings"] if row["item_class_id"] == "flat-185x82x13")
        evaluation = mapping["candidate_evaluations"][0]
        self.assertEqual(evaluation["outcome"], "inconclusive")
        self.assertGreater(evaluation["wall_span_margins_mm"]["y"], 0)
        self.assertLess(evaluation["flat_floor_margins_mm"]["y"], 0)

    def test_negative_margin_is_failure_not_tight_fit(self) -> None:
        item = copy.deepcopy(next(row for row in self.classes["items"] if row["item_class_id"] == "square-stack-49"))
        item["bounding_box_mm"]["x"] = 1000
        sku = next(row for row in self.catalog["items"] if row["sku"] == "bin-3x3x10h")
        result = catalog_module.best_evaluation(item, sku)
        self.assertEqual(result["outcome"], "fail")
        self.assertIn("negative wall-span margin", result["reasons"])

    def test_custom_sku_requires_explicit_unsatisfied_constraint(self) -> None:
        item = copy.deepcopy(next(row for row in self.classes["items"] if row["item_class_id"] == "square-stack-49"))
        item["separator_or_compartment_need"] = "required"
        item["initial_evaluation_target_skus"] = []
        result = catalog_module.select_item(item, self.catalog)
        self.assertEqual(result["selection_status"], "CUSTOM_SKU_REQUIRED")
        self.assertIsNone(result["preferred_sku"])

    def test_closed_schemas_validate_current_records(self) -> None:
        schemas = [json.loads(path.read_text()) for path in sorted((ROOT / "catalog/schemas").glob("*.schema.json"))]
        for schema in schemas:
            jsonschema.Draft202012Validator.check_schema(schema)
        catalog_module.validate_item_class_set(self.classes)
        catalog_module.validate_catalog_schema(self.catalog)
        catalog_module.validate_map_set_schema(self.maps)

        malformed = copy.deepcopy(self.maps)
        malformed["unexpected"] = True
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            catalog_module.validate_map_set_schema(malformed)
        malformed_catalog = copy.deepcopy(self.catalog)
        malformed_catalog["unexpected"] = True
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            catalog_module.validate_catalog_schema(malformed_catalog)
        malformed_classes = copy.deepcopy(self.classes)
        malformed_classes["unexpected"] = True
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            catalog_module.validate_item_class_set(malformed_classes)

        bad_date = self.demand_request()
        bad_date["as_of"] = "not-a-date"
        with self.assertRaisesRegex(ValueError, "not a 'date-time'"):
            catalog_module.validate_schema(bad_date, "demand-request.schema.json", "demand request")

    def test_caller_receipt_cannot_confer_acceptance(self) -> None:
        accepted = self.accepted_maps(self.maps)
        with tempfile.TemporaryDirectory() as temporary:
            receipts = Path(temporary)
            with self.assertRaisesRegex(ValueError, "does not exist"):
                catalog_module.validate_map_set(accepted, self.classes, self.catalog, receipts)
            receipt = self.passing_receipt(accepted["mappings"][1])
            self.write_json(receipts / "fit-one.json", receipt)
            with self.assertRaisesRegex(ValueError, "independently trusted physical and lane evidence"):
                catalog_module.validate_map_set(accepted, self.classes, self.catalog, receipts)

    def test_demand_interface_rejects_provisional_and_caller_claimed_acceptance(self) -> None:
        request = self.demand_request()
        with tempfile.TemporaryDirectory() as temporary:
            receipts = Path(temporary)
            with self.assertRaisesRegex(ValueError, "ACCEPTED"):
                catalog_module.build_demand(self.maps, request, receipts, self.classes, self.catalog)
            accepted = self.accepted_maps(self.maps)
            receipt = self.passing_receipt(accepted["mappings"][1])
            self.write_json(receipts / "fit-one.json", receipt)
            with self.assertRaisesRegex(ValueError, "independently trusted physical and lane evidence"):
                catalog_module.build_demand(accepted, request, receipts, self.classes, self.catalog)
            unsafe = copy.deepcopy(request)
            unsafe["artifact_demands"][0]["private_item_name"] = "must not pass through"
            with self.assertRaisesRegex(ValueError, "Additional properties"):
                catalog_module.build_demand(accepted, unsafe, receipts, self.classes, self.catalog)

    def test_cli_adversarial_receipt_and_binding_counterexamples(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            receipts = temporary_path / "receipts"
            receipts.mkdir()
            maps_path = temporary_path / "maps.json"
            accepted = self.accepted_maps(self.maps)
            receipt = self.passing_receipt(accepted["mappings"][1])
            self.write_json(receipts / "fit-one.json", receipt)

            base_arguments = (
                "validate-maps", "--maps", maps_path,
                "--catalog", ROOT / "catalog/bin-skus.json",
                "--classes", ROOT / "catalog/item-classes.json",
                "--receipts-dir", receipts,
            )

            self.write_json(maps_path, accepted)
            result = self.run_cli(*base_arguments)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("independently trusted physical and lane evidence", result.stderr)

            unknown_wrapper = copy.deepcopy(accepted)
            unknown_wrapper["unexpected"] = True
            self.write_json(maps_path, unknown_wrapper)
            result = self.run_cli(*base_arguments)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("Additional properties", result.stderr)
            self.write_json(maps_path, accepted)

            bad_sample = copy.deepcopy(receipt)
            bad_sample["sample_dimensions_mm"] = {"x": 1, "y": 1, "z": 1}
            bad_sample["sample_uncertainty_mm"] = {"x": 999, "y": 999, "z": 999}
            bad_sample["tested_quantity"] = 999
            self.write_json(receipts / "fit-one.json", bad_sample)
            result = self.run_cli(*base_arguments)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("authoritative class envelope", result.stderr)

            bad_date = copy.deepcopy(receipt)
            bad_date["performed_at"] = "not-a-date"
            self.write_json(receipts / "fit-one.json", bad_date)
            result = self.run_cli(*base_arguments)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("not a 'date-time'", result.stderr)

            for invalid_quantity in (-1, 0, True, 1.5):
                with self.subTest(receipt_quantity=invalid_quantity):
                    bad_quantity = copy.deepcopy(receipt)
                    bad_quantity["tested_quantity"] = invalid_quantity
                    self.write_json(receipts / "fit-one.json", bad_quantity)
                    result = self.run_cli(*base_arguments)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("tested_quantity", result.stderr)

            self.write_json(receipts / "fit-one.json", receipt)
            joint_class_forgery = copy.deepcopy(accepted)
            joint_class_forgery["mappings"][1]["item_class_hash"] = "0" * 64
            forged_receipt = copy.deepcopy(receipt)
            forged_receipt["item_class_hash"] = "0" * 64
            self.write_json(maps_path, joint_class_forgery)
            self.write_json(receipts / "fit-one.json", forged_receipt)
            result = self.run_cli(*base_arguments)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("item_class_hash", result.stderr)

            for field_change in ("source_hash", "nonexistent_output"):
                forged = copy.deepcopy(accepted)
                if field_change == "source_hash":
                    forged["mappings"][1]["source_and_output_hashes"][0]["sha256"] = "0" * 64
                else:
                    output = next(
                        row for row in forged["mappings"][1]["source_and_output_hashes"]
                        if row["path"].endswith(".stl")
                    )
                    output.update({"path": "scad/gridfinity/stl/nonexistent.stl", "sha256": "0" * 64})
                self.write_json(maps_path, forged)
                result = self.run_cli(*base_arguments)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("source_and_output_hashes", result.stderr)

    def test_cli_rejects_invalid_quantities_and_refuses_demand_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            receipts = temporary_path / "receipts"
            receipts.mkdir()
            maps_path = temporary_path / "maps.json"
            request_path = temporary_path / "request.json"
            output_path = temporary_path / "manifest.json"
            accepted = self.accepted_maps(self.maps)
            receipt = self.passing_receipt(accepted["mappings"][1])
            self.write_json(maps_path, accepted)
            self.write_json(receipts / "fit-one.json", receipt)
            arguments = (
                "build-demand", "--maps", maps_path,
                "--catalog", ROOT / "catalog/bin-skus.json",
                "--classes", ROOT / "catalog/item-classes.json",
                "--request", request_path,
                "--receipts-dir", receipts,
                "--output", output_path,
            )

            for invalid_quantity in (-7, 0, True, 1.5):
                with self.subTest(quantity=invalid_quantity):
                    self.write_json(request_path, self.demand_request(invalid_quantity))
                    result = self.run_cli(*arguments)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("required_quantity", result.stderr)
                    self.assertFalse(output_path.exists())

            invalid_date = self.demand_request()
            invalid_date["as_of"] = "not-a-date"
            self.write_json(request_path, invalid_date)
            result = self.run_cli(*arguments)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("not a 'date-time'", result.stderr)

            self.write_json(request_path, self.demand_request())
            result = self.run_cli(*arguments)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("independently trusted physical and lane evidence", result.stderr)
            self.assertFalse(output_path.exists())

    def test_cli_current_provisional_maps_validate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cli(
                "validate-maps",
                "--maps", ROOT / "catalog/item-class-map.json",
                "--catalog", ROOT / "catalog/bin-skus.json",
                "--classes", ROOT / "catalog/item-classes.json",
                "--receipts-dir", temporary,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
