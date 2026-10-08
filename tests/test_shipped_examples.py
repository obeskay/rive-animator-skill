import unittest
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_DIR / "scripts"
EXAMPLES_DIR = REPO_DIR / "examples"

sys.path.insert(0, str(SCRIPTS_DIR))
import rml_lint
import rive_lint


class TestShippedExamples(unittest.TestCase):
    def test_all_examples_valid(self):
        example_dirs = [d for d in EXAMPLES_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
        self.assertGreaterEqual(len(example_dirs), 8, "Expected at least 8 shipped examples")

        for ex_dir in example_dirs:
            with self.subTest(example=ex_dir.name):
                yaml_file = ex_dir / "rive.yaml"
                rml_file = ex_dir / "scene.rml"
                self.assertTrue(yaml_file.exists(), f"Missing rive.yaml in {ex_dir.name}")
                self.assertTrue(rml_file.exists(), f"Missing scene.rml in {ex_dir.name}")

                # Lint RML source
                rml_text = rml_file.read_text(encoding="utf-8")
                rml_issues = rml_lint.lint_rml_text(rml_text, filename=rml_file.name)
                rml_errors = [i for i in rml_issues if i.severity == rml_lint.ERROR]
                self.assertEqual(len(rml_errors), 0, f"RML errors in {ex_dir.name}: {[e.message for e in rml_errors]}")

                # Lint compiled binary if present
                riv_files = list(ex_dir.glob("build/*.riv"))
                if riv_files:
                    for riv_path in riv_files:
                        result, issues, size = rive_lint.inspect_file(riv_path)
                        self.assertIsNotNone(result, f"Failed to parse binary {riv_path}")
                        blocking = [i for i in issues if i["severity"] == rive_lint.ERROR]
                        self.assertEqual(len(blocking), 0, f"Binary error in {riv_path.name}: {blocking}")


if __name__ == "__main__":
    unittest.main()
