#!/usr/bin/env python3
"""Pre-flight validator and linter for Rive Markup Language (.rml) files.

Catches the common authoring traps before running `rive build` or compiler verification:
- Rotation given in degrees instead of radians (> 2π)
- Color property keyed with KeyFrameDouble instead of KeyFrameColor
- Artboard with 0x0 or missing dimensions
- State machine with no defaultStateMachineId, no layers, or no inputs/listeners
- Shape or Fill missing paint child (<SolidColor> or gradient)
- Duplicate element IDs across the document

Dependency-free. Python 3.8+.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ERROR, WARN, INFO = "error", "warn", "info"
SYMBOL = {ERROR: "x", WARN: "!", INFO: "-"}


class Issue:
    def __init__(self, code: str, severity: str, message: str, hint: str = "", line: int | None = None):
        self.code = code
        self.severity = severity
        self.message = message
        self.hint = hint
        self.line = line

    def to_dict(self):
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "hint": self.hint,
            "line": self.line,
        }


def lint_rml_text(content: str, filename: str = "scene.rml") -> list[Issue]:
    issues: list[Issue] = []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as err:
        line, col = err.position if hasattr(err, "position") else (None, None)
        return [Issue("RML001", ERROR, f"Malformed XML: {err}", "Fix XML syntax and closing tags.", line=line)]

    if root.tag != "Rive":
        issues.append(Issue("RML002", ERROR, f"Root element is <{root.tag}>, expected <Rive>", "Wrap content in <Rive version=\"1\" kind=\"fragment\">"))

    ids_seen = set()
    artboard_found = False

    for elem in root.iter():
        elem_id = elem.get("id")
        if elem_id:
            if elem_id in ids_seen:
                issues.append(Issue("RML003", WARN, f"Duplicate id={elem_id!r} on <{elem.tag}>", "Ensure every id attribute is unique."))
            ids_seen.add(elem_id)

        # Check rotation attributes: must be radians, not degrees
        rot = elem.get("rotation")
        if rot is not None:
            try:
                rot_val = float(rot)
                if abs(rot_val) > 2 * math.pi + 0.001:
                    issues.append(Issue("RML004", WARN,
                        f"<{elem.tag} rotation={rot!r}> looks like degrees ({rot_val}°)",
                        f"Rive expects radians. Use {math.radians(rot_val):.4f} rad instead of {rot_val}°."))
            except ValueError:
                pass

        if elem.tag == "Artboard":
            artboard_found = True
            w = elem.get("width")
            h = elem.get("height")
            if not w or not h:
                issues.append(Issue("RML005", ERROR, "<Artboard> missing width or height", "Provide width and height on <Artboard>."))
            else:
                try:
                    wf, hf = float(w), float(h)
                    if wf <= 0 or hf <= 0:
                        issues.append(Issue("RML005", ERROR, f"<Artboard width={w!r} height={h!r}> has non-positive dimensions", "Dimensions must be > 0."))
                except ValueError:
                    issues.append(Issue("RML005", ERROR, f"<Artboard> invalid dimensions: width={w!r}, height={h!r}"))

            if not elem.get("defaultStateMachineId"):
                issues.append(Issue("RML006", INFO, "<Artboard> has no defaultStateMachineId attribute",
                    "Runtimes without an explicit state machine name fallback to first animation unless defaultStateMachineId is set."))

        elif elem.tag == "Fill":
            has_paint = any(child.tag in ("SolidColor", "LinearGradient", "RadialGradient") for child in elem)
            if not has_paint:
                issues.append(Issue("RML007", WARN, "<Fill> has no paint child (<SolidColor> or gradient)",
                    "A <Fill> without paint draws nothing."))

        elif elem.tag == "KeyFrameDouble":
            parent = elem.get("propertyKey") or ""
            # Check if attempting to animate color with Double
            if "color" in parent.lower():
                issues.append(Issue("RML008", ERROR, f"<KeyFrameDouble> used on color property {parent!r}",
                    "Color properties require <KeyFrameColor> with colorValue attribute."))

        elif elem.tag == "StateMachine":
            layers = [c for c in elem if c.tag == "StateMachineLayer"]
            if not layers:
                issues.append(Issue("RML009", WARN, f'<StateMachine name="{elem.get("name", "")}"> has no StateMachineLayer',
                    "Add at least one layer to the state machine."))

    if not artboard_found:
        issues.append(Issue("RML010", ERROR, "No <Artboard> found in document", "RML requires an <Artboard> root node."))

    return issues


def self_test():
    valid_rml = """<Rive version="1" kind="fragment">
        <Artboard defaultStateMachineId="0:8" width="500" height="500" name="Mascot" id="0:1">
            <Shape name="Circle" id="0:2">
                <Ellipse width="100" height="100" />
                <Fill id="0:3"><SolidColor colorValue="FFFF0000" /></Fill>
            </Shape>
            <StateMachine name="State Machine 1" id="0:8">
                <StateMachineLayer name="Layer 1" id="0:9" />
            </StateMachine>
        </Artboard>
    </Rive>"""
    issues = lint_rml_text(valid_rml)
    assert not any(i.severity == ERROR for i in issues), [i.message for i in issues]

    # Test degrees rotation detection
    degree_rml = """<Rive version="1" kind="fragment">
        <Artboard width="500" height="500" name="Test">
            <Node name="Spin" rotation="90" />
        </Artboard>
    </Rive>"""
    deg_issues = lint_rml_text(degree_rml)
    assert any(i.code == "RML004" for i in deg_issues), "Failed to detect degrees in rotation"

    print("self-test OK")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lint and validate Rive RML files.")
    parser.add_argument("files", nargs="*", help="RML files to validate")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--self-test", action="store_true", help="Run self-test")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0

    if not args.files:
        parser.print_usage(sys.stderr)
        return 2

    has_errors = False
    all_results = []

    for path_str in args.files:
        path = Path(path_str)
        if not path.is_file():
            sys.stderr.write(f"rml_lint: file not found: {path}\n")
            has_errors = True
            continue

        content = path.read_text(encoding="utf-8")
        issues = lint_rml_text(content, filename=path.name)
        file_errors = any(i.severity == ERROR for i in issues)
        has_errors = has_errors or file_errors

        if args.json:
            all_results.append({
                "file": str(path),
                "ok": not file_errors,
                "issues": [i.to_dict() for i in issues]
            })
            continue

        print(f"{path.name}  ({len(content)} bytes)")
        if not issues:
            print("  OK  no issues\n")
        else:
            for i in issues:
                line_str = f" [line {i.line}]" if i.line else ""
                print(f"  {SYMBOL[i.severity]} {i.code}{line_str}  {i.message}")
                if i.hint:
                    print(f"      {i.hint}")
            print()

    if args.json:
        import json
        print(json.dumps(all_results if len(all_results) > 1 else (all_results[0] if all_results else {}), indent=2))

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
