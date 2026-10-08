#!/usr/bin/env python3
"""Convert a static Lottie composition into an RML scene for the Rive CLI.

    python3 lottie2rml.py icon.json -o myproject/scene.rml
    python3 lottie2rml.py icon.json --stdout
    python3 lottie2rml.py --self-test

Pair it with svg2lottie.py from the lottie-animator skill and SVG art becomes a
Rive artboard without anyone typing a bezier handle:

    python3 .../lottie-animator/scripts/svg2lottie.py logo.svg -o logo.json --size 512
    python3 lottie2rml.py logo.json -o rive-logo/scene.rml
    rive rive-logo --verify && rive rive-logo --screenshot=rive-logo/build/logo.png

Every shape layer becomes a Node, every group a Shape, every path a PointsPath
of detached cubic vertices; rectangles, ellipses and polystars stay parametric.
Fills, strokes, gradients, trim paths and rounded corners carry over. Layer
parenting becomes nesting. Animated properties are read at their first keyframe
and reported: the output is a still scene, and the motion is authored in RML
afterwards (`rive docs easing`).

The artboard gets a looping placeholder timeline and a default state machine so
it is alive on load: without one an artboard receives no input and no data
(`rive docs gotchas`).

Dependency-free. Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr

LINE_CAP = {1: "butt", 2: "round", 3: "square"}
LINE_JOIN = {1: "miter", 2: "round", 3: "bevel"}


class Warnings(list):
    def add(self, message):
        if message not in self:
            self.append(message)


# -- values -------------------------------------------------------------------
def num(n):
    """Compact decimal: 12, 12.5, -0.333."""
    if isinstance(n, bool) or not isinstance(n, (int, float)):
        return str(n)
    text = "%.4f" % n
    text = text.rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def value(prop, where, warnings, default=None):
    """The static value of a Lottie property; the first keyframe if animated."""
    if not isinstance(prop, dict) or "k" not in prop:
        return default if prop is None else prop
    k = prop["k"]
    if prop.get("a") == 1 and isinstance(k, list) and k and isinstance(k[0], dict):
        warnings.add("%s is animated; the scene uses its first keyframe" % where)
        return k[0].get("s", default)
    return k


def scalar(v, default=0.0):
    if isinstance(v, list):
        return float(v[0]) if v else default
    return float(v) if isinstance(v, (int, float)) else default


def pair(v, default=(0.0, 0.0)):
    if isinstance(v, list) and len(v) >= 2:
        return float(v[0]), float(v[1])
    return default


def argb(rgba, opacity=1.0):
    r, g, b = (rgba + [0, 0, 0])[:3]
    a = rgba[3] if len(rgba) > 3 else 1.0
    channels = (a * opacity, r, g, b)
    return "%02X%02X%02X%02X" % tuple(int(round(max(0.0, min(1.0, c)) * 255)) for c in channels)


# -- xml ----------------------------------------------------------------------
def el(tag, attrs=None, children=None):
    return {"tag": tag, "attrs": attrs or {}, "children": children or []}


def serialize(node, depth=0):
    pad = "    " * depth
    attrs = "".join(
        " %s=%s" % (k, quoteattr(v if isinstance(v, str) else num(v)))
        for k, v in node["attrs"].items() if v is not None
    )
    if not node["children"]:
        return "%s<%s%s/>" % (pad, node["tag"], attrs)
    inner = "\n".join(serialize(child, depth + 1) for child in node["children"])
    return "%s<%s%s>\n%s\n%s</%s>" % (pad, node["tag"], attrs, inner, pad, node["tag"])


class Ids:
    def __init__(self, start=2):
        self.next = start

    def take(self):
        value = "0:%d" % self.next
        self.next += 1
        return value


# -- transforms ---------------------------------------------------------------
def transform_attrs(tr, where, warnings, offset=(0.0, 0.0)):
    """RML transform attributes for a Lottie transform, plus the anchor to
    subtract from everything positioned inside it.

    Lottie: point v renders at p + R.S.(v - a). Rive: child at q renders at
    (x, y) + R.S.q. So x,y = p (minus the enclosing anchor) and q = v - a.
    """
    if not isinstance(tr, dict):
        tr = {}
    if isinstance(tr.get("p"), dict) and tr["p"].get("s"):
        x = scalar(value(tr["p"].get("x"), where + ".p.x", warnings, 0))
        y = scalar(value(tr["p"].get("y"), where + ".p.y", warnings, 0))
        p = (x, y)
    else:
        p = pair(value(tr.get("p"), where + ".p", warnings, [0, 0]))
    a = pair(value(tr.get("a"), where + ".a", warnings, [0, 0]))
    s = pair(value(tr.get("s"), where + ".s", warnings, [100, 100]), (100.0, 100.0))
    r = scalar(value(tr.get("r"), where + ".r", warnings, 0))
    o = scalar(value(tr.get("o"), where + ".o", warnings, 100), 100.0)
    attrs = {"x": p[0] - offset[0], "y": p[1] - offset[1]}
    if abs(r) > 1e-9:
        attrs["rotation"] = math.radians(r)
    if abs(s[0] - 100) > 1e-9:
        attrs["scaleX"] = s[0] / 100.0
    if abs(s[1] - 100) > 1e-9:
        attrs["scaleY"] = s[1] / 100.0
    if abs(o - 100) > 1e-9:
        attrs["opacity"] = o / 100.0
    if "sk" in tr and abs(scalar(value(tr["sk"], where + ".sk", warnings, 0))) > 1e-9:
        warnings.add("%s has a skew; Rive has no skew, it is dropped" % where)
    return attrs, a


# -- geometry -----------------------------------------------------------------
def path_element(item, anchor, where, warnings, radius=0.0):
    shape = value(item.get("ks"), where + ".ks", warnings)
    if not isinstance(shape, dict) or not isinstance(shape.get("v"), list):
        warnings.add("%s has no vertices; skipped" % where)
        return None
    vertices = shape["v"]
    ins = shape.get("i") or [[0, 0]] * len(vertices)
    outs = shape.get("o") or [[0, 0]] * len(vertices)
    children = []
    for (vx, vy), (ix, iy), (ox, oy) in zip(vertices, ins, outs):
        x, y = vx - anchor[0], vy - anchor[1]
        d_in, d_out = math.hypot(ix, iy), math.hypot(ox, oy)
        if d_in < 1e-6 and d_out < 1e-6:
            attrs = {"x": x, "y": y}
            if radius > 0:
                attrs["radius"] = radius
            children.append(el("StraightVertex", attrs))
        else:
            children.append(el("CubicDetachedVertex", {
                "x": x, "y": y,
                "inRotation": math.atan2(iy, ix), "inDistance": d_in,
                "outRotation": math.atan2(oy, ox), "outDistance": d_out,
            }))
    if not children:
        return None
    return el("PointsPath", {"isClosed": "true" if shape.get("c") else "false",
                             "name": item.get("nm") or "Path"}, children)


def parametric_element(item, anchor, where, warnings, radius=0.0):
    ty = item["ty"]
    p = pair(value(item.get("p"), where + ".p", warnings, [0, 0]))
    attrs = {"x": p[0] - anchor[0], "y": p[1] - anchor[1], "originX": 0.5, "originY": 0.5}
    if ty == "rc":
        w, h = pair(value(item.get("s"), where + ".s", warnings, [0, 0]))
        corner = scalar(value(item.get("r"), where + ".r", warnings, 0)) or radius
        attrs.update({"width": w, "height": h})
        if corner > 0:
            attrs["cornerRadiusTL"] = corner
        return el("Rectangle", dict(attrs, name=item.get("nm") or "Rectangle"))
    if ty == "el":
        w, h = pair(value(item.get("s"), where + ".s", warnings, [0, 0]))
        attrs.update({"width": w, "height": h})
        return el("Ellipse", dict(attrs, name=item.get("nm") or "Ellipse"))
    # polystar
    outer = scalar(value(item.get("or"), where + ".or", warnings, 0))
    points = int(round(scalar(value(item.get("pt"), where + ".pt", warnings, 5))))
    rotation = scalar(value(item.get("r"), where + ".r", warnings, 0))
    attrs.update({"width": outer * 2, "height": outer * 2, "points": points})
    if abs(rotation) > 1e-9:
        attrs["rotation"] = math.radians(rotation)
    if item.get("sy", 1) == 1:
        inner = scalar(value(item.get("ir"), where + ".ir", warnings, outer / 2))
        attrs["innerRadius"] = inner / outer if outer else 0.5
        return el("Star", dict(attrs, name=item.get("nm") or "Star"))
    return el("Polygon", dict(attrs, name=item.get("nm") or "Polygon"))


# -- paint --------------------------------------------------------------------
def gradient_element(item, anchor, where, warnings):
    g = item.get("g") or {}
    count = int(g.get("p") or 0)
    raw = value(g.get("k"), where + ".g", warnings, []) or []
    colors = [raw[i:i + 4] for i in range(0, min(len(raw), count * 4), 4)]
    alphas = {}
    for i in range(count * 4, len(raw) - 1, 2):
        alphas[round(raw[i], 4)] = raw[i + 1]
    stops = []
    for pos, r, gg, b in colors:
        alpha = alphas.get(round(pos, 4), 1.0)
        stops.append(el("GradientStop", {"colorValue": argb([r, gg, b, alpha]), "position": pos}))
    if not stops:
        warnings.add("%s gradient has no stops; painted flat" % where)
        return el("SolidColor", {"colorValue": "FF000000", "name": "Color"})
    s = pair(value(item.get("s"), where + ".s", warnings, [0, 0]))
    e = pair(value(item.get("e"), where + ".e", warnings, [0, 0]))
    tag = "RadialGradient" if item.get("t") == 2 else "LinearGradient"
    return el(tag, {"startX": s[0] - anchor[0], "startY": s[1] - anchor[1],
                    "endX": e[0] - anchor[0], "endY": e[1] - anchor[1], "name": "Gradient"}, stops)


def paint_elements(item, anchor, where, warnings, trims):
    ty = item["ty"]
    opacity = scalar(value(item.get("o"), where + ".o", warnings, 100), 100.0) / 100.0
    if ty in ("fl", "st"):
        color = value(item.get("c"), where + ".c", warnings, [0, 0, 0, 1])
        paint = el("SolidColor", {"colorValue": argb(list(color), opacity), "name": "Color"})
    else:
        paint = gradient_element(item, anchor, where, warnings)
        if abs(opacity - 1) > 1e-9:
            warnings.add("%s gradient opacity %.2f is not carried; bake it into the stops" % (where, opacity))
    if ty in ("fl", "gf"):
        attrs = {"name": item.get("nm") or "Fill"}
        if item.get("r") == 2:
            attrs["fillRule"] = "evenOdd"
        return el("Fill", attrs, [paint])
    attrs = {
        "thickness": scalar(value(item.get("w"), where + ".w", warnings, 1), 1.0),
        "cap": LINE_CAP.get(item.get("lc"), "butt"),
        "join": LINE_JOIN.get(item.get("lj"), "miter"),
        "name": item.get("nm") or "Stroke",
    }
    children = [paint]
    for trim in trims:
        children.append(el("TrimPath", {
            "start": scalar(value(trim.get("s"), where + ".tm.s", warnings, 0)) / 100.0,
            "end": scalar(value(trim.get("e"), where + ".tm.e", warnings, 100)) / 100.0,
            "offset": scalar(value(trim.get("o"), where + ".tm.o", warnings, 0)) / 360.0,
            "modeValue": "synchronized" if trim.get("m") == 2 else "sequential",
            "name": trim.get("nm") or "Trim",
        }))
    if item.get("d"):
        warnings.add("%s has dashes; DashPath is not converted" % where)
    return el("Stroke", attrs, children)


# -- shapes -------------------------------------------------------------------
UNSUPPORTED = {"rp": "repeater", "mm": "merge paths", "op": "offset path",
               "pb": "pucker/bloat", "tw": "twist", "zz": "zig zag"}


def convert_group(items, anchor, where, warnings, ids, name="Group", transform=None):
    """A Lottie group becomes a Shape (paths + paints), or a Node holding
    nested groups when it has any. Item order is kept: first on top."""
    tr = next((i for i in items if isinstance(i, dict) and i.get("ty") == "tr"), transform)
    attrs, own_anchor = transform_attrs(tr, where + ".tr", warnings, anchor)
    nested = [i for i in items if isinstance(i, dict) and i.get("ty") == "gr"]
    geometry, paints, trims = [], [], []
    radius = 0.0
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        ty = item.get("ty")
        here = "%s.it[%d]" % (where, index)
        if item.get("hd"):
            continue
        if ty == "rd":
            radius = scalar(value(item.get("r"), here + ".r", warnings, 0))
        elif ty == "tm":
            trims.append(item)
        elif ty in UNSUPPORTED:
            warnings.add("%s: %s is not converted" % (here, UNSUPPORTED[ty]))
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        ty = item.get("ty")
        here = "%s.it[%d]" % (where, index)
        if item.get("hd"):
            continue
        if ty == "sh":
            node = path_element(item, own_anchor, here, warnings, radius)
            if node:
                geometry.append(node)
        elif ty in ("rc", "el", "sr"):
            geometry.append(parametric_element(item, own_anchor, here, warnings, radius))
        elif ty in ("fl", "st", "gf", "gs"):
            paints.append(paint_elements(item, own_anchor, here, warnings, trims))
    if trims and not any(p["tag"] == "Stroke" for p in paints):
        warnings.add("%s: trim path on a fill; Rive trims strokes only" % where)

    shape = None
    if geometry:
        if not paints:
            warnings.add("%s has geometry but no fill or stroke; it will not draw" % where)
        shape = el("Shape", {"name": name, "id": ids.take()}, geometry + paints)
    if not nested:
        if shape is None:
            return None
        shape["attrs"] = dict(attrs, **shape["attrs"])
        return shape
    children = []
    for index, item in enumerate(items):
        if isinstance(item, dict) and item.get("ty") == "gr" and not item.get("hd"):
            child = convert_group(item.get("it") or [], own_anchor, "%s.it[%d]" % (where, index),
                                  warnings, ids, item.get("nm") or "Group")
            if child:
                children.append(child)
    if shape is not None:
        children.append(shape)
    if not children:
        return None
    return el("Node", dict(attrs, name=name, id=ids.take()), children)


def convert_layer(layer, where, warnings, ids):
    ty = layer.get("ty")
    if layer.get("hd"):
        return None
    if ty == 3:  # null: a transform with nothing to draw, still a parent
        attrs, anchor = transform_attrs(layer.get("ks"), where + ".ks", warnings)
        return el("Node", dict(attrs, name=layer.get("nm") or "Null", id=ids.take())), anchor
    if ty != 4:
        warnings.add("%s: layer type %r (%s) is not converted" % (
            where, ty, {0: "precomp", 1: "solid", 2: "image", 5: "text"}.get(ty, "unknown")))
        return None
    attrs, anchor = transform_attrs(layer.get("ks"), where + ".ks", warnings)
    node = el("Node", dict(attrs, name=layer.get("nm") or "Layer", id=ids.take()))
    for index, item in enumerate(layer.get("shapes") or []):
        if not isinstance(item, dict) or item.get("hd"):
            continue
        here = "%s.shapes[%d]" % (where, index)
        if item.get("ty") == "gr":
            child = convert_group(item.get("it") or [], anchor, here, warnings, ids, item.get("nm") or "Group")
        else:
            # Loose geometry outside a group: Lottie draws it at zero size, but
            # the intent is clear enough to honour.
            child = convert_group([item], anchor, here, warnings, ids, item.get("nm") or "Shape")
        if child:
            node["children"].append(child)
    return node, anchor


def convert(data, name=None):
    warnings = Warnings()
    if not isinstance(data, dict) or not isinstance(data.get("layers"), list):
        raise ValueError("not a Lottie composition: no layers array")
    ids = Ids()
    artboard_id = ids.take()
    width = float(data.get("w") or 512)
    height = float(data.get("h") or 512)
    title = name or data.get("nm") or "Artboard"

    built = {}       # ind -> (node, anchor)
    order = []
    for index, layer in enumerate(data["layers"]):
        if not isinstance(layer, dict):
            continue
        result = convert_layer(layer, "$.layers[%d]" % index, warnings, ids)
        if result is None:
            continue
        ind = layer.get("ind", index)
        built[ind] = (result[0], result[1], layer.get("parent"))
        order.append(ind)

    roots = []
    for ind in order:
        node, anchor, parent = built[ind]
        if parent is not None and parent in built and parent != ind:
            parent_node, parent_anchor, _ = built[parent]
            node["attrs"]["x"] -= parent_anchor[0]
            node["attrs"]["y"] -= parent_anchor[1]
            parent_node["children"].append(node)
        else:
            if parent is not None:
                warnings.add("$.layers ind %r is parented to %r, which was not converted" % (ind, parent))
            roots.append(node)
    if any(built[i][2] is not None for i in order):
        warnings.add("layer parenting became nesting; Rive draws by tree order, so a child now draws with its parent")
    if not roots:
        raise ValueError("nothing convertible: no visible shape layers")

    animation_id, machine_id, layer_id, state_id, style_id = (ids.take() for _ in range(5))
    # The editor gives every artboard a layout style; inspect warns when it is missing.
    style = el("LayoutComponentStyle", {"name": "Artboard Style", "id": style_id})
    scene = el("Artboard", {"defaultStateMachineId": machine_id, "styleId": style_id, "width": width,
                            "height": height, "name": title, "id": artboard_id}, [style] + roots + [
        el("LinearAnimation", {"loopValue": "loop", "duration": 60, "name": "Idle", "id": animation_id}),
        el("StateMachine", {"name": "State Machine 1", "id": machine_id}, [
            el("StateMachineLayer", {"name": "Layer 1", "id": layer_id}, [
                el("AnyState", {"x": 400, "y": 0}),
                el("ExitState", {"x": 480, "y": 0}),
                el("EntryState", {"x": 0, "y": 16}, [el("StateTransition", {"stateToId": state_id})]),
                el("AnimationState", {"x": 160, "y": 0, "animationId": animation_id, "id": state_id}),
            ]),
        ]),
    ])
    root = el("Rive", {"version": "1", "kind": "fragment"}, [scene])
    return serialize(root) + "\n", warnings


# -- cli ----------------------------------------------------------------------
def self_test():
    import xml.etree.ElementTree as ET
    data = {"v": "5.12.1", "fr": 60, "ip": 0, "op": 60, "w": 100, "h": 100, "nm": "T", "layers": [{
        "ty": 4, "ind": 1, "nm": "L", "ip": 0, "op": 60, "st": 0,
        "ks": {"a": {"a": 0, "k": [50, 50, 0]}, "p": {"a": 0, "k": [50, 50, 0]},
               "s": {"a": 0, "k": [100, 100, 100]}, "r": {"a": 0, "k": 90}, "o": {"a": 0, "k": 100}},
        "shapes": [{"ty": "gr", "nm": "G", "it": [
            {"ty": "sh", "nm": "P", "ks": {"a": 0, "k": {"c": True, "v": [[10, 10], [90, 10], [90, 90]],
                                                        "i": [[0, 0], [0, 0], [-30, 0]], "o": [[0, 0], [0, 40], [0, 0]]}}},
            {"ty": "rc", "nm": "R", "p": {"a": 0, "k": [50, 50]}, "s": {"a": 0, "k": [20, 10]}, "r": {"a": 0, "k": 3}},
            {"ty": "fl", "nm": "F", "c": {"a": 0, "k": [1, 0, 0, 1]}, "o": {"a": 0, "k": 50}},
            {"ty": "st", "nm": "S", "c": {"a": 0, "k": [0, 0, 1, 1]}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 2}, "lc": 2, "lj": 2},
            {"ty": "tm", "s": {"a": 0, "k": 0}, "e": {"a": 1, "k": [{"t": 0, "s": [25]}, {"t": 30, "s": [100]}]}, "o": {"a": 0, "k": 90}},
            {"ty": "tr", "a": {"a": 0, "k": [50, 50]}, "p": {"a": 0, "k": [50, 50]}, "s": {"a": 0, "k": [100, 100]},
             "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
        ]}]}]}
    text, warnings = convert(data)
    root = ET.fromstring(text)
    assert root.tag == "Rive" and root.get("kind") == "fragment"
    artboard = root.find("Artboard")
    assert artboard.get("defaultStateMachineId") == artboard.find("StateMachine").get("id")
    assert artboard.get("styleId") == artboard.find("LayoutComponentStyle").get("id")
    node = artboard.find("Node")
    assert node.get("x") == "50" and node.get("rotation") == num(math.pi / 2), node.attrib
    shape = node.find("Shape")
    assert shape.get("x") == "0" and shape.get("y") == "0", shape.attrib
    vertices = shape.find("PointsPath").findall("*")
    assert [v.tag for v in vertices] == ["StraightVertex", "CubicDetachedVertex", "CubicDetachedVertex"], [v.tag for v in vertices]
    assert vertices[0].get("x") == "-40" and vertices[0].get("y") == "-40", vertices[0].attrib
    assert vertices[1].get("outDistance") == "40" and vertices[1].get("outRotation") == num(math.pi / 2), vertices[1].attrib
    assert vertices[2].get("inDistance") == "30" and vertices[2].get("inRotation") == num(math.pi), vertices[2].attrib
    rect = shape.find("Rectangle")
    assert rect.get("width") == "20" and rect.get("cornerRadiusTL") == "3" and rect.get("x") == "0", rect.attrib
    fill = shape.find("Fill").find("SolidColor")
    assert fill.get("colorValue") == "80FF0000", fill.attrib
    trim = shape.find("Stroke").find("TrimPath")
    assert trim.get("end") == "0.25" and trim.get("offset") == "0.25", trim.attrib
    assert any("tm.e is animated" in w for w in warnings), warnings
    print("self-test OK")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert a static Lottie composition into RML.")
    parser.add_argument("source", nargs="?", help="Lottie .json")
    parser.add_argument("-o", "--output", help="write the RML here (directories are created)")
    parser.add_argument("--stdout", action="store_true", help="print the RML instead of writing it")
    parser.add_argument("--name", help="artboard name (default: the composition's nm)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    if not args.source or not (args.output or args.stdout):
        parser.print_usage(sys.stderr)
        return 2
    source = Path(args.source)
    if not source.is_file():
        print("lottie2rml: no such file: %s" % source, file=sys.stderr)
        return 2
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("lottie2rml: cannot read %s: %s" % (source, exc), file=sys.stderr)
        return 2
    try:
        text, warnings = convert(data, args.name)
    except ValueError as exc:
        print("lottie2rml: %s" % exc, file=sys.stderr)
        return 1
    for warning in warnings:
        print("warning: %s" % warning, file=sys.stderr)
    if args.stdout:
        sys.stdout.write(text)
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print("%s -> %s  (%d layers -> RML, %d warning%s)" % (
            source, out, len(data.get("layers") or []), len(warnings), "" if len(warnings) == 1 else "s"))
        print("Next: rive <project> --verify, then --screenshot and look at it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
