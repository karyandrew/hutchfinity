from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
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

    def test_cli_consumes_only_the_explicit_synthetic_admission_pair(self) -> None:
        result = self.run_cli("consume-synthetic-admission")
        self.assertEqual(result.returncode, 0, result.stderr)
        admitted = json.loads(result.stdout)
        self.assertEqual(admitted["admission_scope"], "synthetic_test_only")
        self.assertEqual(admitted["physical_fit_receipt"], "synthetic-fit-v1")
        self.assertEqual(admitted["lane_receipt"], "synthetic-lane-v1")
        self.assertFalse(admitted["production_authorized"])
        self.assertFalse(admitted["real_evidence_authority_configured"])
        self.assertTrue(all(row["selection_status"] == "PROVISIONAL" and row["physical_fit_state"] == "not_run" for row in self.maps["mappings"]))
        rejected = self.run_cli("consume-synthetic-admission", "--admission-id", "revoked-or-unknown")
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("not in the fixed admission source", rejected.stderr)


class AdmissionBoundaryTests(unittest.TestCase):
    """Test-owned enrollment, exclusively synthetic, through the public CLI.

    Invalid records are deliberately enrolled in the isolated test registry.
    This is not production enrollment and does not mock the consumer decision.
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = catalog_module.read_json(ROOT / "catalog/bin-skus.json")
        cls.maps = catalog_module.read_json(ROOT / "catalog/item-class-map.json")
        cls.sandbox = tempfile.TemporaryDirectory(prefix="synthetic-admission-controls-")
        cls.fixture = Path(cls.sandbox.name)
        (cls.fixture / "scripts").mkdir()
        shutil.copy2(SCRIPT, cls.fixture / "scripts/hutchfinity_catalog.py")
        shutil.copytree(ROOT / "catalog", cls.fixture / "catalog")
        git_dir = subprocess.check_output(["git", "rev-parse", "--absolute-git-dir"], cwd=ROOT, env=CatalogTests.subprocess_environment(), text=True).strip()
        (cls.fixture / ".git").write_text("gitdir: " + git_dir + "\n")
        sources = cls.catalog["source_files_and_hashes"]
        outputs = [row["output_hashes"][0] for row in cls.catalog["items"] if row["catalog_state"] == "build_managed"]
        for ref in sources + outputs:
            target = cls.fixture / ref["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / ref["path"], target)
        cls.registry_path = cls.fixture / "catalog/trust/synthetic-admission.json"
        cls.physical_path = cls.fixture / "catalog/receipts/synthetic-physical-fit.json"
        cls.lane_path = cls.fixture / "catalog/receipts/synthetic-lane.json"
        cls.original_registry = catalog_module.read_json(cls.registry_path)
        cls.original_physical = catalog_module.read_json(cls.physical_path)
        cls.original_lane = catalog_module.read_json(cls.lane_path)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.sandbox.cleanup()

    write_json = staticmethod(CatalogTests.write_json)
    subprocess_environment = staticmethod(CatalogTests.subprocess_environment)

    def fixture_cli(self, *arguments: object) -> subprocess.CompletedProcess[str]:
        env = self.subprocess_environment()
        env["GIT_WORK_TREE"] = str(self.fixture)
        return subprocess.run([sys.executable, str(self.fixture / "scripts/hutchfinity_catalog.py"), *map(str, arguments)], cwd=self.fixture, env=env, text=True, capture_output=True)

    def install_test_enrollment(self, registry=None, physical=None, lane=None, *, enroll_bytes=True):
        registry = copy.deepcopy(self.original_registry if registry is None else registry)
        self.write_json(self.physical_path, self.original_physical if physical is None else physical)
        self.write_json(self.lane_path, self.original_lane if lane is None else lane)
        if enroll_bytes:
            registry["admissions"][0]["physical"]["sha256"] = catalog_module.sha256(self.physical_path)
            registry["admissions"][0]["lane"]["sha256"] = catalog_module.sha256(self.lane_path)
        self.write_json(self.registry_path, registry)

    def test_public_cli_admitted_semantic_negative_matrix(self):
        cases = []
        def case(name, kind, mutate, expected): cases.append((name, kind, mutate, expected))
        for state in ("revoked", "stale"):
            case("admission-" + state, "registry", lambda r, st=state: r["admissions"][0].update(state=st), "revoked or stale")
            case("lane-" + state, "registry", lambda r, st=state: r["lanes"][0].update(state=st), "lane is unknown, revoked or stale")
            case("profile-" + state, "registry", lambda r, st=state: r["profiles"][0].update(state=st), "profile is missing, revoked or stale")
        case("unknown-lane", "registry", lambda r: r["lanes"].clear(), "lane is unknown")
        case("missing-profile", "registry", lambda r: r["profiles"].clear(), "profile is missing")
        case("stale-profile-revision", "registry", lambda r: r["profiles"][0].update(revision="test-v2"), "profile revision or digest")
        case("stale-profile-digest", "registry", lambda r: r["profiles"][0].update(sha256="4" * 64), "profile revision or digest")
        case("lane-profile", "registry", lambda r: r["lanes"][0]["profile"].update(revision="other"), "lane profile")
        case("duplicate-admission", "registry", lambda r: r["admissions"].append(copy.deepcopy(r["admissions"][0])), "duplicate admissions")
        case("unknown-root-field", "registry", lambda r: r.update(signer="caller"), "Additional properties")
        case("unknown-root-version", "registry", lambda r: r.update(schema="unknown/v1"), "schema validation")
        case("unconfigured-with-enrollment", "registry", lambda r: r.update(configuration="unconfigured"), "must have no enrollment")
        case("unknown-class", "registry", lambda r: r["admissions"][0].update(item_class_id="unknown"), "authoritative class")
        case("stale-class-admission", "registry", lambda r: r["admissions"][0].update(item_class_hash="0" * 64), "class identity or revision")
        case("unmanaged-sku", "registry", lambda r: r["admissions"][0].update(sku="bin-1x1x1h"), "authoritative class and current SKU")
        for kind in ("physical", "lane"):
            for state in ("fail", "inconclusive", "not_run", "stale"):
                case(kind + "-gate-" + state, kind, lambda r, st=state: r.update(result=st), "non-passing")
            for key in ("profile_id", "revision", "sha256"):
                case(kind + "-profile-" + key, kind, lambda r, k=key: r["profile"].update({k: "0" * 64 if k == "sha256" else "wrong"}), "receipt profile")
            case(kind + "-missing-profile", kind, lambda r: r.pop("profile"), "required property")
            case(kind + "-receipt-id", kind, lambda r: r.update(receipt_id="other-receipt"), "receipt identity")
            case(kind + "-source-revision", kind, lambda r: r.update(source_commit="0" * 40), "source revision")
            case(kind + "-scope", kind, lambda r: r.update(evidence_scope="real"), "receipt evidence scope")
            case(kind + "-workaround", kind, lambda r: r["workarounds"].append("force"), "workaround")
            case(kind + "-caller-signer", kind, lambda r: r.update(signer="trusted"), "Additional properties")
            case(kind + "-bad-date", kind, lambda r: r.update(performed_at="not-a-date"), "date-time")
        for key in self.original_physical["checks"]:
            case("missing-physical-check-" + key, "physical", lambda r, k=key: r["checks"].pop(k), "required property")
            case("failed-physical-check-" + key, "physical", lambda r, k=key: r["checks"].update({k:"fail"}), "non-passing")
        for key in self.original_lane["checks"]:
            case("missing-lane-check-" + key, "lane", lambda r, k=key: r["checks"].pop(k), "required property")
            case("inconclusive-lane-check-" + key, "lane", lambda r, k=key: r["checks"].update({k:"inconclusive"}), "non-passing")
        for field, value, message in [
            ("validation_lane", "other-lane", "cross-bound"), ("validation_receipt", "other-receipt", "cross-bound"),
            ("item_class_id", "short-roll-40x15", "class identity"), ("item_class_hash", "0" * 64, "class identity"),
            ("sku", "bin-2x4x10h", "SKU or output"), ("artifact_sha256", "0" * 64, "SKU or output"),
            ("sample_count", 1, "sample count"), ("tested_quantity", 0, "tested_quantity"),
            ("selected_orientation", "upright", "SKU/orientation")]:
            case("physical-"+field, "physical", lambda r, f=field, v=value: r.update({f:v}), message)
        case("excess-quantity", "physical", lambda r: r.update(tested_quantity=999), "source-derived capacity")
        case("insufficient-quantity", "physical", lambda r: r.update(tested_quantity=0), "tested_quantity")
        case("insufficient-quantity-policy", "registry", lambda r: r["admissions"][0].update(minimum_sample_count=3), "sample count")
        case("sample-too-small", "physical", lambda r: r["sample_dimensions_mm"].update(x=48.5), "class envelope")
        case("sample-excess-uncertainty", "physical", lambda r: r["sample_uncertainty_mm"].update(x=2), "class envelope")
        case("sample-undercoverage", "physical", lambda r: r["sample_uncertainty_mm"].update(x=0.1), "required class envelope")
        case("physical-source-digest", "physical", lambda r: r["source_and_output_hashes"][0].update(sha256="0"*64), "content binding")
        case("physical-output-path", "physical", lambda r: r["source_and_output_hashes"][-1].update(path="other.stl"), "content binding")
        case("lane-source-digest", "lane", lambda r: r["source_files_and_hashes"][0].update(sha256="0"*64), "content binding")
        case("lane-output-digest", "lane", lambda r: r["output_hashes"][0].update(sha256="0"*64), "hash does not match")
        case("lane-output-path", "lane", lambda r: r["output_hashes"][0].update(path="nonexistent.stl"), "does not exist")
        case("lane-output-escape", "lane", lambda r: r["output_hashes"][0].update(path="../outside.stl"), "escapes")
        case("lane-wrong-id", "lane", lambda r: r.update(lane_id="other-lane"), "lane receipt identity")
        case("lane-unverified-link", "lane", lambda r: r.update(source_output_link_state="unverified"), "reproduced")
        case("lane-incomplete-representatives", "lane", lambda r: r["representative_artifacts"].pop(), "too short")
        case("lane-wrong-tallest", "lane", lambda r: r["representative_artifacts"][2].update(sku="bin-3x3x10h"), "tallest")
        case("lane-duplicate-role", "lane", lambda r: r["representative_artifacts"][2].update(role="multi_cell"), "representative set")
        for name, kind, mutate, expected in cases:
            with self.subTest(control=name):
                records = {"registry":copy.deepcopy(self.original_registry), "physical":copy.deepcopy(self.original_physical), "lane":copy.deepcopy(self.original_lane)}
                mutate(records[kind])
                self.install_test_enrollment(**records)
                result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", "synthetic-pair-v1")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(expected, result.stderr)
                self.assertNotIn("admitted digest", result.stderr, "semantic control must pass the digest guard")
        self.install_test_enrollment()

    def test_public_cli_unconfigured_and_unadmitted_controls(self):
        self.install_test_enrollment()
        result = self.fixture_cli("consume-admission", "--admission-id", "synthetic-pair-v1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("is not configured", result.stderr)
        for flag in ("--trust-path", "--receipts-dir", "--signer", "--hash", "--PASS"):
            with self.subTest(caller_authority=flag):
                result = self.fixture_cli("consume-admission", "--admission-id", "synthetic-pair-v1", flag, "caller")
                self.assertEqual(result.returncode, 2)
                self.assertIn("unrecognized arguments", result.stderr)
        result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", "caller-created-pair")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not in the fixed", result.stderr)
        changed = copy.deepcopy(self.original_physical)
        changed["result"] = "fail"
        self.install_test_enrollment(physical=changed, enroll_bytes=False)
        result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", "synthetic-pair-v1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("admitted digest", result.stderr)
        self.install_test_enrollment()

    def test_general_consumer_second_pair_and_quantity_semantics(self):
        # An independently fixed second test enrollment proves no pair ID or
        # class/SKU constants are hidden in the consumer. No real enrollment.
        registry = copy.deepcopy(self.original_registry)
        physical = copy.deepcopy(self.original_physical)
        lane = copy.deepcopy(self.original_lane)
        classes = catalog_module.read_json(self.fixture / "catalog/item-classes.json")
        item = next(row for row in classes["items"] if row["item_class_id"] == "short-roll-40x15")
        item["minimum_quantity_per_bin"] = 2
        self.write_json(self.fixture / "catalog/item-classes.json", classes)
        mapping = catalog_module.select_item(item, self.catalog)
        sku = next(row for row in self.catalog["items"] if row["sku"] == mapping["preferred_sku"])
        physical.update(receipt_id="synthetic-roll-fit", item_class_id=item["item_class_id"], item_class_hash=catalog_module.stable_hash(item), sku=sku["sku"], artifact_sha256=sku["output_hashes"][0]["sha256"], source_and_output_hashes=catalog_module.artifact_hash_refs(sku), selected_orientation=mapping["selected_orientation"], sample_dimensions_mm=item["bounding_box_mm"], tested_quantity=2)
        lane["output_hashes"].append({key:sku["output_hashes"][0][key] for key in ("path","sha256")})
        entry = registry["admissions"][0]
        entry.update(admission_id="synthetic-roll-pair", item_class_id=item["item_class_id"], item_class_hash=physical["item_class_hash"], sku=sku["sku"])
        entry["physical"]["receipt_id"] = physical["receipt_id"]
        self.install_test_enrollment(registry, physical, lane)
        result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", "synthetic-roll-pair")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["item_class_id"], "short-roll-40x15")
        physical["tested_quantity"] = 1
        self.install_test_enrollment(registry, physical, lane)
        result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", "synthetic-roll-pair")
        self.assertEqual(result.returncode, 2)
        self.assertIn("fewer than minimum_quantity_per_bin", result.stderr)
        shutil.copy2(ROOT / "catalog/item-classes.json", self.fixture / "catalog/item-classes.json")
        self.install_test_enrollment()

    def install_shared_lane_enrollment(self):
        # Retain the square admission and enroll a distinct class-fit receipt
        # for the roll. Both admissions pin the same frozen lane bytes.
        registry = copy.deepcopy(self.original_registry)
        physical = copy.deepcopy(self.original_physical)
        lane = copy.deepcopy(self.original_lane)
        classes = catalog_module.read_json(self.fixture / "catalog/item-classes.json")
        item = next(row for row in classes["items"] if row["item_class_id"] == "short-roll-40x15")
        mapping = catalog_module.select_item(item, self.catalog)
        sku = next(row for row in self.catalog["items"] if row["sku"] == mapping["preferred_sku"])
        physical.update(receipt_id="synthetic-roll-fit", item_class_id=item["item_class_id"], item_class_hash=catalog_module.stable_hash(item), sku=sku["sku"], artifact_sha256=sku["output_hashes"][0]["sha256"], source_and_output_hashes=catalog_module.artifact_hash_refs(sku), selected_orientation=mapping["selected_orientation"], sample_dimensions_mm=item["bounding_box_mm"], sample_uncertainty_mm=item["uncertainty_mm"], tested_quantity=2)
        lane["output_hashes"].append({key: sku["output_hashes"][0][key] for key in ("path", "sha256")})
        self.install_test_enrollment(registry, lane=lane)
        registry = catalog_module.read_json(self.registry_path)
        entry = copy.deepcopy(registry["admissions"][0])
        entry.update(admission_id="synthetic-roll-pair", item_class_id=item["item_class_id"], item_class_hash=physical["item_class_hash"], sku=sku["sku"])
        physical_path = self.fixture / "catalog/receipts/synthetic-roll-fit.json"
        self.write_json(physical_path, physical)
        entry["physical"] = {"receipt_id": physical["receipt_id"], "path": "catalog/receipts/synthetic-roll-fit.json", "sha256": catalog_module.sha256(physical_path)}
        registry["admissions"].append(entry)
        self.write_json(self.registry_path, registry)
        self.addCleanup(self.install_test_enrollment)
        return registry

    def test_public_cli_joint_admissions_and_combined_demand_share_exact_lane(self):
        registry = self.install_shared_lane_enrollment()
        self.assertEqual(len(registry["admissions"]), 2)
        self.assertEqual(registry["admissions"][0]["lane"], registry["admissions"][1]["lane"])
        decisions = []
        for entry in registry["admissions"]:
            result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", entry["admission_id"])
            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads(result.stdout)
            self.assertEqual(decision["item_class_id"], entry["item_class_id"])
            self.assertEqual(decision["sku"], entry["sku"])
            self.assertEqual(decision["physical_fit_receipt"], entry["physical"]["receipt_id"])
            self.assertEqual(decision["selection_status"], "SYNTHETIC_ACCEPTED")
            self.assertFalse(decision["production_authorized"])
            self.assertFalse(decision["integrated_system_accepted"])
            decisions.append(decision)

        classes = catalog_module.read_json(self.fixture / "catalog/item-classes.json")
        maps = catalog_module.select_all(classes, self.catalog)
        for entry in registry["admissions"]:
            mapping = next(row for row in maps["mappings"] if row["item_class_id"] == entry["item_class_id"])
            mapping.update(selection_status="ACCEPTED", physical_fit_state="pass", physical_fit_receipt=entry["physical"]["receipt_id"], validation_lane=entry["lane_id"], validation_receipt=entry["lane"]["receipt_id"])
        maps_path = self.fixture / "shared-lane-maps.json"
        request_path = self.fixture / "shared-lane-request.json"
        output = self.fixture / "shared-lane-demand.json"
        request = catalog_module.read_json(ROOT / "catalog/receipts/synthetic-demand-request.json")
        roll_request = copy.deepcopy(request["artifact_demands"][0])
        roll_request.update(item_class_id="short-roll-40x15", required_quantity=2)
        request["artifact_demands"].append(roll_request)
        self.write_json(maps_path, maps)
        self.write_json(request_path, request)
        result = self.fixture_cli(
            "build-demand", "--catalog", self.fixture / "catalog/bin-skus.json",
            "--classes", self.fixture / "catalog/item-classes.json", "--maps", maps_path,
            "--request", request_path, "--receipts-dir", self.fixture / "unused-caller-receipts",
            "--output", output, "--evidence-scope", "synthetic_test_only",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        demand = catalog_module.read_json(output)
        self.assertEqual(demand["admission_provenance"], decisions)
        self.assertEqual([(row["item_class_id"], row["artifact_id_or_sku"], row["required_quantity"], row["physical_fit_receipt"], row["validation_receipt"]) for row in demand["artifact_demands"]], [
            ("square-stack-49", "bin-3x3x10h", 1, "synthetic-fit-v1", "synthetic-lane-v1"),
            ("short-roll-40x15", "bin-2x4x10h", 2, "synthetic-roll-fit", "synthetic-lane-v1"),
        ])
        self.assertEqual(demand["evidence_scope"], "synthetic_test_only")
        self.assertFalse(demand["production_authorized"])
        self.assertFalse(demand["integrated_system_accepted"])

    def test_public_cli_joint_admissions_refuse_conflicts_and_physical_reuse(self):
        registry = self.install_shared_lane_enrollment()
        alternate_path = self.fixture / "catalog/receipts/synthetic-lane-copy.json"
        shutil.copy2(self.lane_path, alternate_path)
        self.assertEqual(catalog_module.sha256(alternate_path), registry["admissions"][0]["lane"]["sha256"])
        for field, value in (("path", "catalog/receipts/synthetic-lane-copy.json"), ("sha256", "0" * 64)):
            with self.subTest(conflicting_lane_binding=field):
                changed = copy.deepcopy(registry)
                changed["admissions"][1]["lane"][field] = value
                self.write_json(self.registry_path, changed)
                for entry in changed["admissions"]:
                    result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", entry["admission_id"])
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("conflicting admitted lane receipt identity binding", result.stderr)
        changed = copy.deepcopy(registry)
        changed["admissions"][1]["physical"] = copy.deepcopy(changed["admissions"][0]["physical"])
        self.write_json(self.registry_path, changed)
        for entry in changed["admissions"]:
            result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", entry["admission_id"])
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("duplicate admitted physical receipt identity", result.stderr)

    def test_public_cli_malformed_roots_fail_closed(self):
        for payload, message in (("null", "schema validation"), ('{"configuration":"configured","configuration":"unconfigured"}', "duplicate JSON field"), ('{"value":NaN}', "non-finite JSON number")):
            self.registry_path.write_text(payload)
            result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", "synthetic-pair-v1")
            self.assertEqual(result.returncode, 2)
            self.assertIn(message, result.stderr)
        self.registry_path.unlink()
        result = self.fixture_cli("consume-admission", "--evidence-scope", "synthetic_test_only", "--admission-id", "synthetic-pair-v1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not exist", result.stderr)
        self.install_test_enrollment()

    def test_public_cli_mapping_demand_and_scope_isolation(self):
        self.install_test_enrollment()
        arguments = ["--catalog",self.fixture/"catalog/bin-skus.json","--classes",self.fixture/"catalog/item-classes.json","--maps",self.fixture/"catalog/receipts/synthetic-maps.json","--receipts-dir",self.fixture/"unused-caller-receipts"]
        output = self.fixture / "demand.json"
        demand_args = ["build-demand", *arguments, "--request",self.fixture/"catalog/receipts/synthetic-demand-request.json","--output",output]
        result = self.fixture_cli(*demand_args)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())
        result = self.fixture_cli(*demand_args, "--evidence-scope", "synthetic_test_only")
        self.assertEqual(result.returncode, 0, result.stderr)
        demand = catalog_module.read_json(output)
        self.assertFalse(demand["production_authorized"])
        self.assertFalse(demand["integrated_system_accepted"])
        self.assertEqual(demand["evidence_scope"], "synthetic_test_only")
        self.assertEqual(demand["admission_provenance"][0]["selection_status"], "SYNTHETIC_ACCEPTED")
        self.assertEqual(demand["admission_provenance"][0]["authority_revision"], "test-v1")
        self.assertEqual(catalog_module.read_json(self.fixture / "catalog/item-class-map.json"), self.maps)
        for field, value in (("validation_lane","other-lane"),("validation_receipt","other-receipt"),("physical_fit_receipt","unknown-fit")):
            maps = catalog_module.read_json(ROOT / "catalog/receipts/synthetic-maps.json")
            maps["mappings"][1][field] = value
            self.write_json(self.fixture / "catalog/receipts/synthetic-maps.json", maps)
            result = self.fixture_cli("validate-maps", *arguments, "--evidence-scope", "synthetic_test_only")
            self.assertEqual(result.returncode, 2, result.stderr)
        shutil.copy2(ROOT / "catalog/receipts/synthetic-maps.json", self.fixture / "catalog/receipts/synthetic-maps.json")



if __name__ == "__main__":
    unittest.main()
