import unittest
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import svg2rml


class TestSvg2Rml(unittest.TestCase):
    def test_basic_svg_conversion(self):
        svg = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="10" width="80" height="80" rx="10" fill="#3B82F6" />
            <circle cx="50" cy="50" r="20" fill="#FFFFFF" />
        </svg>"""
        rml, warnings = svg2rml.convert_svg_to_rml(svg, name="TestIcon")
        self.assertIn("<Rive", rml)
        self.assertIn('name="TestIcon"', rml)
        self.assertIn("<PointsPath", rml)
        self.assertIn("<Fill", rml)
        self.assertIn("<StateMachine", rml)

    def test_path_svg_conversion(self):
        svg = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 10 C 20 20, 40 20, 50 10 L 90 90 Z" fill="#EF4444" />
        </svg>"""
        rml, warnings = svg2rml.convert_svg_to_rml(svg, name="VectorShape")
        self.assertIn("<PointsPath", rml)
        self.assertIn("<CubicDetachedVertex", rml)

    def test_cli_reads_svg_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "icon.svg"
            src.write_text('<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                           '<circle cx="12" cy="12" r="8" fill="#C8522B"/></svg>', encoding="utf-8")
            out = Path(tmp) / "scene.rml"
            self.assertEqual(svg2rml.main([str(src), "-o", str(out)]), 0)
            self.assertIn("<PointsPath", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
