#!/usr/bin/env python3
"""Convert an SVG directly into an RML scene for the Rive CLI.

    python3 svg2rml.py icon.svg -o myproject/scene.rml
    python3 svg2rml.py icon.svg --size 512 --name Mascot -o mascot/scene.rml
    python3 svg2rml.py --self-test

Converts SVG paths, rects, circles, ellipses, lines, polylines, polygons,
groups, transforms, fills, and strokes into RML:
- Node per SVG group/layer
- Shape per vector element
- PointsPath with StraightVertex and CubicDetachedVertex
- Parametric Rectangle and Ellipse elements preserved
- Automatic looping placeholder timeline and default state machine

Zero external dependencies. Python 3.8+.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import svg2lottie
    import lottie2rml
except ImportError as err:
    sys.exit(f"Error importing converter modules: {err}")


def convert_svg_to_rml(
    source_path_or_text: str | Path,
    name: str | None = None,
    size: float | None = None,
    current_color: str | None = None,
    fps: int = 60,
) -> tuple[str, list[str]]:
    """Convert SVG source (path or raw XML string) to an RML XML string."""
    if isinstance(source_path_or_text, Path):
        source = source_path_or_text.read_text(encoding="utf-8")
    else:
        source = source_path_or_text

    lottie_dict, warnings = svg2lottie.convert(
        source,
        size=size,
        current_color=current_color,
        fps=fps,
    )
    if name:
        lottie_dict["nm"] = name

    rml_xml, rml_warnings = lottie2rml.convert(lottie_dict)
    all_warnings = list(warnings) + list(rml_warnings)
    return rml_xml, all_warnings


def self_test():
    svg_sample = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="40" fill="#2563EB" />
        <path d="M30 50 L45 65 L70 35" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none" />
    </svg>"""
    rml, warnings = convert_svg_to_rml(svg_sample, name="Checkmark")
    assert "<Rive" in rml, "Missing <Rive root"
    assert 'name="Checkmark"' in rml, "Missing artboard name"
    assert "<PointsPath" in rml or "<Ellipse" in rml, "Missing geometry"
    assert "<Fill" in rml, "Missing Fill"
    assert "<Stroke" in rml, "Missing Stroke"
    assert "<StateMachine" in rml, "Missing default state machine"
    print("self-test OK")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert an SVG file directly into an RML scene for Rive CLI."
    )
    parser.add_argument("source", nargs="?", help="SVG file path")
    parser.add_argument("-o", "--output", help="Write RML to this file (directories created as needed)")
    parser.add_argument("--stdout", action="store_true", help="Print RML to stdout")
    parser.add_argument("--name", help="Artboard name (default: derived from filename or SVG)")
    parser.add_argument("--size", type=float, help="Scale artboard to this square size (e.g. 512)")
    parser.add_argument("--current-color", help="Hex color to replace currentColor (e.g. #000000)")
    parser.add_argument("--self-test", action="store_true", help="Run internal self-test")

    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0

    if not args.source:
        parser.print_help(sys.stderr)
        return 2

    source_path = Path(args.source)
    if not source_path.exists():
        sys.stderr.write(f"Error: file not found: {source_path}\n")
        return 1

    artboard_name = args.name or source_path.stem

    try:
        rml_xml, warnings = convert_svg_to_rml(
            source_path,
            name=artboard_name,
            size=args.size,
            current_color=args.current_color,
        )
    except Exception as err:
        sys.stderr.write(f"Conversion error: {err}\n")
        return 1

    for w in warnings:
        sys.stderr.write(f"warning: {w}\n")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rml_xml, encoding="utf-8")
        sys.stderr.write(f"Wrote {len(rml_xml)} bytes to {out_path}\n")
    elif args.stdout or not args.output:
        sys.stdout.write(rml_xml)

    return 0


if __name__ == "__main__":
    sys.exit(main())
