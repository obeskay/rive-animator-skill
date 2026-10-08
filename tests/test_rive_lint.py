import unittest
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import rive_lint


class TestRiveLint(unittest.TestCase):
    def test_fixture_self_test(self):
        parsed = rive_lint.parse(rive_lint._FIXTURE)
        self.assertEqual((parsed["major"], parsed["minor"]), (7, 3))
        model = rive_lint.build(parsed["objects"])
        ab, = model["artboards"]
        self.assertEqual(ab["name"], "Artboard")
        self.assertEqual((ab["width"], ab["height"]), (500.0, 500.0))

        issues = rive_lint.lint(parsed, model, len(rive_lint._FIXTURE))
        codes = {i["code"] for i in issues}
        self.assertIn("RV005", codes)

    def test_framework_wiring(self):
        parsed = rive_lint.parse(rive_lint._FIXTURE)
        model = rive_lint.build(parsed["objects"])
        path = Path("mascot.riv")

        for fw in ["react", "vue", "svelte", "web", "flutter", "swiftui", "android", "react-native"]:
            sections = rive_lint.wiring(path, model, framework=fw)
            self.assertTrue(len(sections) >= 1)
            title, lines = sections[0]
            # swiftui, android, react-native use path.stem ('mascot'), others use 'mascot.riv'
            expected = "mascot" if fw in ("swiftui", "react-native", "android") else "mascot.riv"
            self.assertTrue(any(expected in l for l in lines), f"File name missing in {fw} wiring")

    def test_all_frameworks_wiring(self):
        parsed = rive_lint.parse(rive_lint._FIXTURE)
        model = rive_lint.build(parsed["objects"])
        path = Path("mascot.riv")

        sections = rive_lint.wiring(path, model, framework="all")
        self.assertEqual(len(sections), len(rive_lint.FRAMEWORK_GENERATORS))


if __name__ == "__main__":
    unittest.main()
