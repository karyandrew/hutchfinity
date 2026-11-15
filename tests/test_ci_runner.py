"""Tests for ./ci, the offline gate. They run it against throwaway fixture trees
with a stub OpenSCAD, so they need no real OpenSCAD and must never skip."""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / "ci"
STUB = ROOT / "tests" / "fixtures" / "stub-openscad"

PASSING = """
import unittest
class T(unittest.TestCase):
    def test_a(self):
        self.assertTrue(True)
    def test_b(self):
        self.assertEqual(1, 1)
"""


class Fixture:
    """A throwaway checkout with a tests/ suite and an experiments suite."""

    def __init__(self, case, tests=None, experiments=None):
        self.root = Path(tempfile.mkdtemp(prefix="ci-fixture-"))
        case.addCleanup(self.cleanup)
        self.tmp = Path(tempfile.mkdtemp(prefix="ci-tmp-"))
        case.addCleanup(shutil.rmtree, self.tmp, True)
        self.write("tests", tests if tests is not None else {"test_ok.py": PASSING})
        self.write("experiments/baseplate-tessellation",
                   experiments if experiments is not None else {"test_exp.py": PASSING})

    def cleanup(self):
        for path, dirs, _files in os.walk(self.root):
            os.chmod(path, 0o700)
        shutil.rmtree(self.root, True)

    def write(self, rel, files):
        folder = self.root / rel
        folder.mkdir(parents=True, exist_ok=True)
        for name, body in files.items():
            (folder / name).write_text(textwrap.dedent(body))

    def run(self, mode="manifold", env=None, args=(), root=True):
        environ = {k: v for k, v in os.environ.items() if k != "OPENSCAD_BIN"}
        environ.update({"OPENSCAD_BIN": str(STUB), "HF_STUB_MODE": mode, "TMPDIR": str(self.tmp)})
        environ.update(env or {})
        for key in [k for k, v in environ.items() if v is None]:
            del environ[key]
        command = [sys.executable, str(CI)]
        if root:
            command += ["--root", str(self.root)]
        return subprocess.run(command + list(args), capture_output=True, text=True,
                              env=environ, cwd=str(self.tmp))

    def report(self):
        return json.loads((self.tmp / "hutchfinity-ci-report.json").read_text())

    def roster(self):
        return json.loads((self.tmp / "hutchfinity-ci-roster.json").read_text())


class CiContract(unittest.TestCase):
    def test_ci_is_an_executable_python_script(self):
        self.assertTrue(CI.is_file())
        self.assertTrue(CI.stat().st_mode & stat.S_IXUSR)
        self.assertTrue(CI.read_text().startswith("#!/usr/bin/env python3"))

    def test_all_pass_exits_zero_with_a_complete_report(self):
        fx = Fixture(self)
        result = fx.run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = fx.report()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["exit_code"], 0)
        self.assertTrue(report["complete"])
        self.assertEqual(report["counts"]["expected"], 4)
        self.assertEqual(report["counts"]["run"], 4)
        self.assertEqual(report["counts"]["passed"], 4)
        self.assertEqual(report["counts"]["skipped"], 0)
        self.assertEqual(report["counts"]["failed"], 0)
        self.assertEqual(report["counts"]["errors"], 0)
        self.assertEqual(set(report["results"].values()), {"passed"})

    def test_roster_lists_every_test_id_with_its_suite(self):
        fx = Fixture(self)
        fx.run()
        roster = fx.roster()
        self.assertEqual(roster["count"], 4)
        self.assertEqual(roster["tests"], sorted([
            "tests::test_ok.T.test_a", "tests::test_ok.T.test_b",
            "experiments/baseplate-tessellation::test_exp.T.test_a",
            "experiments/baseplate-tessellation::test_exp.T.test_b"]))
        self.assertEqual({s["name"] for s in roster["suites"]},
                         {"tests", "experiments/baseplate-tessellation"})
        self.assertEqual(fx.report()["roster_sha256"], self.sha(fx))

    def sha(self, fx):
        import hashlib
        return hashlib.sha256((fx.tmp / "hutchfinity-ci-roster.json").read_bytes()).hexdigest()

    def test_a_failing_test_exits_one(self):
        fx = Fixture(self, tests={"test_bad.py": """
            import unittest
            class T(unittest.TestCase):
                def test_x(self):
                    self.fail("boom")
        """})
        result = fx.run()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = fx.report()
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["counts"]["failed"], 1)
        self.assertEqual(report["failed"], ["tests::test_bad.T.test_x"])

    def test_an_erroring_test_exits_one(self):
        fx = Fixture(self, tests={"test_err.py": """
            import unittest
            class T(unittest.TestCase):
                def test_x(self):
                    raise RuntimeError("boom")
        """})
        self.assertEqual(fx.run().returncode, 1)
        self.assertEqual(fx.report()["counts"]["errors"], 1)

    def test_a_failure_in_the_experiments_suite_exits_one(self):
        fx = Fixture(self, experiments={"test_bad.py": """
            import unittest
            class T(unittest.TestCase):
                def test_x(self):
                    self.fail("boom")
        """})
        self.assertEqual(fx.run().returncode, 1)

    def test_an_import_error_exits_one(self):
        fx = Fixture(self, tests={"test_broken.py": "import no_such_module_anywhere\n"})
        self.assertEqual(fx.run().returncode, 1)
        self.assertEqual(fx.report()["status"], "fail")

    def test_unexpected_success_exits_one(self):
        fx = Fixture(self, tests={"test_ux.py": """
            import unittest
            class T(unittest.TestCase):
                @unittest.expectedFailure
                def test_x(self):
                    pass
        """})
        self.assertEqual(fx.run().returncode, 1)


class CiNeverPassesOnSkips(unittest.TestCase):
    def assert_skip_fails(self, tests, skipped_ids):
        fx = Fixture(self, tests=tests)
        result = fx.run()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = fx.report()
        self.assertEqual(report["status"], "fail")
        self.assertGreaterEqual(report["counts"]["skipped"], 1)
        self.assertEqual(sorted(s["id"] for s in report["skipped"]), skipped_ids)
        return report

    def test_a_skipif_decorated_test_fails(self):
        report = self.assert_skip_fails({"test_skip.py": """
            import unittest
            class T(unittest.TestCase):
                @unittest.skipIf(True, "no openscad")
                def test_x(self):
                    pass
                def test_y(self):
                    pass
        """}, ["tests::test_skip.T.test_x"])
        self.assertEqual(report["skipped"][0]["reason"], "no openscad")

    def test_a_skipped_class_fails(self):
        self.assert_skip_fails({"test_skip.py": """
            import unittest
            @unittest.skipIf(True, "gate")
            class T(unittest.TestCase):
                def test_x(self):
                    pass
                def test_y(self):
                    pass
        """}, ["tests::test_skip.T.test_x", "tests::test_skip.T.test_y"])

    def test_skiptest_raised_inside_a_test_fails(self):
        self.assert_skip_fails({"test_skip.py": """
            import unittest
            class T(unittest.TestCase):
                def test_x(self):
                    self.skipTest("later")
        """}, ["tests::test_skip.T.test_x"])

    def test_skiptest_in_setupclass_fails_and_counts_the_unrun_tests(self):
        fx = Fixture(self, tests={"test_skip.py": """
            import unittest
            class T(unittest.TestCase):
                @classmethod
                def setUpClass(cls):
                    raise unittest.SkipTest("gate")
                def test_x(self):
                    pass
        """})
        self.assertEqual(fx.run().returncode, 1)
        report = fx.report()
        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["complete"])
        self.assertEqual(report["missing"], ["tests::test_skip.T.test_x"])

    def test_module_level_skip_fails(self):
        fx = Fixture(self, tests={"test_skip.py": """
            import unittest
            raise unittest.SkipTest("whole module")
        """})
        self.assertEqual(fx.run().returncode, 1)
        self.assertGreaterEqual(fx.report()["counts"]["skipped"], 1)

    def test_a_skipped_subtest_fails(self):
        fx = Fixture(self, tests={"test_skip.py": """
            import unittest
            class T(unittest.TestCase):
                def test_x(self):
                    with self.subTest("one"):
                        self.skipTest("later")
        """})
        self.assertEqual(fx.run().returncode, 1)
        self.assertGreaterEqual(fx.report()["counts"]["skipped"], 1)


class CiSetupFailures(unittest.TestCase):
    MARKER = """
        import os, unittest
        from pathlib import Path
        class T(unittest.TestCase):
            def test_x(self):
                Path(os.environ["TMPDIR"], "ran-marker").write_text("ran")
    """

    def assert_setup_failure(self, fx, result, needle=None):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse((fx.tmp / "ran-marker").exists(), "tests must not run after a setup failure")
        report = fx.report()
        self.assertEqual(report["status"], "setup-failure")
        self.assertEqual(report["exit_code"], 2)
        self.assertFalse(report["complete"])
        self.assertTrue(report["reason"])
        if needle:
            self.assertIn(needle, (report["reason"] + result.stderr).lower())

    def test_missing_openscad_is_setup_failure_not_pass(self):
        fx = Fixture(self, tests={"test_m.py": self.MARKER})
        result = fx.run(env={"OPENSCAD_BIN": str(fx.tmp / "no-such-openscad")})
        self.assert_setup_failure(fx, result, "openscad")

    def test_openscad_without_manifold_is_setup_failure(self):
        fx = Fixture(self, tests={"test_m.py": self.MARKER})
        self.assert_setup_failure(fx, fx.run(mode="classic"), "manifold")

    def test_openscad_that_cannot_start_is_setup_failure(self):
        fx = Fixture(self, tests={"test_m.py": self.MARKER})
        self.assert_setup_failure(fx, fx.run(mode="broken"), "openscad")

    def test_openscad_is_found_on_path_when_the_variable_is_unset(self):
        fx = Fixture(self)
        bindir = fx.tmp / "bin"
        bindir.mkdir()
        (bindir / "openscad").symlink_to(STUB)
        result = fx.run(env={"OPENSCAD_BIN": None, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(fx.report()["openscad"]["path"], str(bindir / "openscad"))

    def test_tests_receive_the_checked_openscad_binary(self):
        fx = Fixture(self, tests={"test_env.py": """
            import os, unittest
            class T(unittest.TestCase):
                def test_x(self):
                    self.assertEqual(os.environ["OPENSCAD_BIN"], %r)
        """ % str(STUB)})
        self.assertEqual(fx.run().returncode, 0)

    def test_an_empty_suite_is_setup_failure(self):
        fx = Fixture(self, tests={"notes.txt": "no tests here"},
                     experiments={"notes.txt": "none"})
        self.assert_setup_failure(fx, fx.run())

    def test_a_missing_tests_directory_is_setup_failure(self):
        fx = Fixture(self)
        shutil.rmtree(fx.root / "tests")
        self.assert_setup_failure(fx, fx.run())

    def test_a_missing_root_is_setup_failure(self):
        fx = Fixture(self)
        result = fx.run(args=["--root", str(fx.tmp / "nowhere")])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_report_directory_inside_the_checkout_is_setup_failure(self):
        fx = Fixture(self, tests={"test_m.py": self.MARKER})
        result = fx.run(args=["--report-dir", str(fx.root / "reports")])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse((fx.root / "reports").exists())
        self.assertFalse((fx.tmp / "ran-marker").exists())

    def test_a_tmpdir_inside_the_checkout_is_setup_failure(self):
        fx = Fixture(self, tests={"test_m.py": self.MARKER})
        inside = fx.root / "scratch"
        inside.mkdir()
        result = fx.run(env={"TMPDIR": str(inside)})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(os.listdir(inside), [])

    def test_a_missing_report_directory_is_setup_failure(self):
        fx = Fixture(self)
        result = fx.run(args=["--report-dir", str(fx.tmp / "not-created")])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse((fx.tmp / "not-created").exists())

    def test_unknown_option_is_setup_failure(self):
        fx = Fixture(self)
        self.assertEqual(fx.run(args=["--frobnicate"]).returncode, 2)

    def test_a_stale_report_is_removed_before_a_setup_failure(self):
        fx = Fixture(self)
        (fx.tmp / "hutchfinity-ci-report.json").write_text('{"status": "pass"}')
        (fx.tmp / "hutchfinity-ci-roster.json").write_text('{"count": 99}')
        result = fx.run(mode="classic")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(fx.report()["status"], "setup-failure")
        self.assertFalse((fx.tmp / "hutchfinity-ci-roster.json").exists())


class CiEvidence(unittest.TestCase):
    def test_roster_exists_before_tests_run_and_report_only_after(self):
        fx = Fixture(self, tests={"test_order.py": """
            import os, unittest
            from pathlib import Path
            class T(unittest.TestCase):
                def test_x(self):
                    tmp = Path(os.environ["TMPDIR"])
                    self.assertTrue((tmp / "hutchfinity-ci-roster.json").is_file())
                    self.assertFalse((tmp / "hutchfinity-ci-report.json").exists())
        """})
        result = fx.run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((fx.tmp / "hutchfinity-ci-report.json").is_file())

    def test_report_dir_option_redirects_both_files(self):
        fx = Fixture(self)
        other = fx.tmp / "reports"
        other.mkdir()
        self.assertEqual(fx.run(args=["--report-dir", str(other)]).returncode, 0)
        self.assertTrue((other / "hutchfinity-ci-roster.json").is_file())
        self.assertTrue((other / "hutchfinity-ci-report.json").is_file())
        self.assertFalse((fx.tmp / "hutchfinity-ci-report.json").exists())

    def test_report_names_the_openscad_that_was_checked(self):
        fx = Fixture(self)
        fx.run()
        openscad = fx.report()["openscad"]
        self.assertEqual(openscad["path"], str(STUB))
        self.assertIn("2025.01.01", openscad["version"])
        self.assertEqual(openscad["backend"], "Manifold")

    def test_report_names_what_ci_leaves_out_and_why(self):
        fx = Fixture(self)
        fx.run()
        excluded = {e["path"]: e["reason"] for e in fx.report()["excluded"]}
        self.assertIn("scripts/test_presentation_packet_negative.py", excluded)
        self.assertTrue(excluded["scripts/test_presentation_packet_negative.py"])

    def test_a_read_only_checkout_is_not_written(self):
        fx = Fixture(self)
        before = sorted(str(p.relative_to(fx.root)) for p in fx.root.rglob("*"))
        for path, dirs, files in os.walk(fx.root):
            for name in files:
                os.chmod(os.path.join(path, name), 0o444)
            os.chmod(path, 0o555)
        result = fx.run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = sorted(str(p.relative_to(fx.root)) for p in fx.root.rglob("*"))
        self.assertEqual(before, after)

    def test_a_failing_run_still_writes_a_complete_report(self):
        fx = Fixture(self, tests={"test_bad.py": """
            import unittest
            class T(unittest.TestCase):
                def test_x(self):
                    self.fail("boom")
                def test_y(self):
                    pass
        """})
        fx.run()
        report = fx.report()
        self.assertTrue(report["complete"])
        self.assertEqual(report["counts"]["run"], report["counts"]["expected"])
        self.assertEqual(report["results"]["tests::test_bad.T.test_x"], "failed")
        self.assertEqual(report["results"]["tests::test_bad.T.test_y"], "passed")


if __name__ == "__main__":
    unittest.main()
