import unittest
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import rml_lint


class TestRmlLint(unittest.TestCase):
    def test_valid_rml(self):
        rml = """<Rive version="1" kind="fragment">
            <Artboard defaultStateMachineId="0:20" width="200" height="200" name="Valid">
                <Shape x="0" y="0" name="S"><Ellipse width="50" height="50"/><Fill><SolidColor colorValue="FFFF0000"/></Fill></Shape>
                <StateMachine name="SM" id="0:20"><StateMachineLayer name="L"/></StateMachine>
            </Artboard>
        </Rive>"""
        issues = rml_lint.lint_rml_text(rml)
        errors = [i for i in issues if i.severity == rml_lint.ERROR]
        self.assertEqual(len(errors), 0, [e.message for e in errors])

    def test_degree_rotation_warning(self):
        rml = """<Rive version="1" kind="fragment">
            <Artboard width="200" height="200" name="Deg">
                <Shape rotation="180" name="S"><Ellipse width="50" height="50"/></Shape>
            </Artboard>
        </Rive>"""
        issues = rml_lint.lint_rml_text(rml)
        codes = [i.code for i in issues]
        self.assertIn("RML004", codes)


if __name__ == "__main__":
    unittest.main()
