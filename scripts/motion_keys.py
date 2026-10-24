#!/usr/bin/env python3
"""Bake living motion into RML keyframes. Standard library only.

Rive eases every keyframe segment on its own, so a chain of poses keyed with an
ease-in-out curve slows to zero at every pose and reads as a robot. Three ways to
key a channel, by the job:

  track  one move (a blink, a lid, a press): each segment eases in and out, or
         eases out when marked `out`. It stops at every key, on purpose.
  flow   acting through key poses (a hop, a lean, a head turn): passes through
         every pose with a continuous speed and never overshoots one (monotone
         cubic Hermite). Each segment is ONE keyframe with a CubicValueInterpolator
         whose control values are the Hermite handles, so the curve is exact.
  bake   anything computed (breathing, sway, follow-through, a sum of waves):
         sampled every few frames with its true slope, written the same way.
         Periodic functions close their loop with no seam.

Frames are at 60 fps (one frame is 16.7 ms). Output is the <KeyFrameDouble> lines
that go inside one <KeyedProperty>.

  python3 scripts/motion_keys.py track 0:1 7:0.1 9:0.1 20:1:out
  python3 scripts/motion_keys.py flow 0:1 10:0.86 16:1.1 44:1 50:0.8 62:1.04 76:1
  python3 scripts/motion_keys.py wave --base 1 --amp 0.018 --period 120 --length 240

As a module, `bake(fn, length)` and `keyed(object_id, {property_key: keys})` build
whole <KeyedObject> blocks from Python, see examples/living-mascot/build.py.
"""
import argparse
import math
import sys

TRAVEL = (0.77, 0.0, 0.175, 1.0)  # things that travel: gaze, sway, a lid closing
ARRIVE = (0.23, 1.0, 0.32, 1.0)   # things that open or arrive: a lid reopening, a pop
SINE = (0.37, 0.0, 0.63, 1.0)     # half a sine wave between two extremes


# shaping helpers, the same ones as the rossark motion engine, in frames

def wave(t, period, phase=0.0):
    """A smooth -1..1 back-and-forth. `phase` (0..1) offsets one part from the next."""
    return math.sin((t / period + phase) * 2 * math.pi)


def bell(p):
    """0 at both ends of 0..1 and 1 in the middle: fade in and out."""
    return math.sin(math.pi * min(1.0, max(0.0, p)))


def seg(t, a, b):
    """0 before frame a, 1 after frame b, a smoothstep between: one beat of a scene."""
    p = min(1.0, max(0.0, (t - a) / (b - a)))
    return p * p * (3 - 2 * p)


def seeded(i, salt=0):
    """Stable pseudo-random 0..1 for item i: variety that is the same every build."""
    x = math.sin(i * 12.9898 + salt * 78.233) * 43758.5453
    return x - math.floor(x)


# curves

def _num(v):
    return f"{v:.6f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def flow_points(keys):
    """(frame, value) poses -> (frame, value, slope) with monotone tangents."""
    keys = sorted((round(f), v) for f, v in keys)   # whole frames, so the handles match what is written
    n = len(keys)
    if n < 2:
        raise ValueError("flow needs at least two keys")
    if len({f for f, _ in keys}) != n:
        raise ValueError("flow keys need distinct frames")
    slopes = [(keys[i + 1][1] - keys[i][1]) / (keys[i + 1][0] - keys[i][0]) for i in range(n - 1)]
    tangents = [0.0] * n
    for j in range(1, n - 1):
        a, b = slopes[j - 1], slopes[j]
        if a * b <= 0:
            continue
        h0, h1 = keys[j][0] - keys[j - 1][0], keys[j + 1][0] - keys[j][0]
        w0, w1 = 2 * h1 + h0, h1 + 2 * h0
        tangents[j] = (w0 + w1) / (w0 / a + w1 / b)
    return [(f, v, m) for (f, v), m in zip(keys, tangents)]


def flow(t, keys):
    """The value of a flow channel at frame t (for deriving other channels from it)."""
    pts = flow_points(keys)
    if t <= pts[0][0]:
        return pts[0][1]
    if t >= pts[-1][0]:
        return pts[-1][1]
    i = max(j for j in range(len(pts) - 1) if pts[j][0] <= t)
    (f0, v0, m0), (f1, v1, m1) = pts[i], pts[i + 1]
    h = f1 - f0
    s = (t - f0) / h
    return ((2 * s**3 - 3 * s**2 + 1) * v0 + (s**3 - 2 * s**2 + s) * h * m0
            + (-2 * s**3 + 3 * s**2) * v1 + (s**3 - s**2) * h * m1)


def bake(fn, length, step=4, periodic=True, start=0):
    """Sample fn(frame) every `step` frames over [start, start+length] with its slope.

    With periodic=True the slope at both ends is the same, so a `loop` closes cleanly
    as long as fn itself repeats every `length` frames.
    """
    count = max(1, round(length / step))
    eps = 0.01
    pts = []
    for i in range(count + 1):
        f = start + round(length * i / count)
        lo, hi = f - eps, f + eps
        if not periodic:
            lo, hi = max(start, lo), min(start + length, hi)
        pts.append((f, fn(f), (fn(hi) - fn(lo)) / (hi - lo)))
    return pts


def hermite_xml(points, indent="    "):
    """(frame, value, slope) -> KeyFrameDouble lines with exact CubicValueInterpolators."""
    out = []
    for i, (f, v, m) in enumerate(points):
        frame = round(f)
        if i == len(points) - 1:
            out.append(f'{indent}<KeyFrameDouble value="{_num(v)}" frame="{frame}" interpolationType="linear"/>')
            break
        f1, v1, m1 = points[i + 1]
        h = round(f1) - frame
        y1, y2 = v + m * h / 3, v1 - m1 * h / 3
        if abs(v1 - v) < 1e-9 and abs(m) < 1e-9 and abs(m1) < 1e-9:
            out.append(f'{indent}<KeyFrameDouble value="{_num(v)}" frame="{frame}" interpolationType="linear"/>')
            continue
        out.append(f'{indent}<KeyFrameDouble value="{_num(v)}" frame="{frame}" interpolationType="cubicValue">')
        out.append(f'{indent}    <CubicValueInterpolator x1="0.333333" y1="{_num(y1)}" x2="0.666667" y2="{_num(y2)}"/>')
        out.append(f'{indent}</KeyFrameDouble>')
    return "\n".join(out)


def track_xml(keys, indent="    "):
    """(frame, value, 'out'|None) -> KeyFrameDouble lines that ease into every key.

    The curve marked on a key shapes the segment ARRIVING at it, as in the rossark
    engine; Rive reads the curve from the key the segment LEAVES, so it is shifted.
    """
    out = []
    for i, key in enumerate(keys):
        f, v = key[0], key[1]
        if i == len(keys) - 1:
            out.append(f'{indent}<KeyFrameDouble value="{_num(v)}" frame="{round(f)}" interpolationType="linear"/>')
            break
        nxt = keys[i + 1]
        curve = ARRIVE if len(nxt) > 2 and nxt[2] == "out" else TRAVEL
        if nxt[1] == v:
            out.append(f'{indent}<KeyFrameDouble value="{_num(v)}" frame="{round(f)}" interpolationType="linear"/>')
            continue
        out.append(f'{indent}<KeyFrameDouble value="{_num(v)}" frame="{round(f)}" interpolationType="cubic">')
        out.append(f'{indent}    <CubicEaseInterpolator x1="{curve[0]}" y1="{curve[1]}" x2="{curve[2]}" y2="{curve[3]}"/>')
        out.append(f'{indent}</KeyFrameDouble>')
    return "\n".join(out)


def keyed(object_id, channels, indent="            "):
    """{property_key: keyframe lines} -> one <KeyedObject> block."""
    lines = [f'{indent}<KeyedObject objectId="{object_id}">']
    for key, body in channels.items():
        lines.append(f'{indent}    <KeyedProperty propertyKey="{key}">')
        lines.append("\n".join(f"{indent}        {ln}" for ln in body.splitlines()))
        lines.append(f'{indent}    </KeyedProperty>')
    lines.append(f'{indent}</KeyedObject>')
    return "\n".join(lines)


def _bezier_value(p0, p1, p2, p3, s):
    return (1 - s) ** 3 * p0 + 3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s * s * p2 + s ** 3 * p3


def self_test():
    poses = [(0, 1), (10, 0.86), (16, 1.1), (44, 1), (50, 0.8), (62, 1.04), (76, 1)]
    pts = flow_points(poses)
    for f, v in poses:
        assert abs(flow(f, poses) - v) < 1e-9, "flow must pass through every pose"
    for (f0, v0), (f1, v1) in zip(poses, poses[1:]):
        lo, hi = min(v0, v1), max(v0, v1)
        for k in range(1, 20):
            v = flow(f0 + (f1 - f0) * k / 20, poses)
            assert lo - 1e-9 <= v <= hi + 1e-9, "flow must never overshoot a pose"
    # the cubicValue handles reproduce the Hermite curve exactly (x1/x2 at thirds keep time linear)
    (f0, v0, m0), (f1, v1, m1) = pts[1], pts[2]
    h = f1 - f0
    for k in range(11):
        s = k / 10
        assert abs(_bezier_value(v0, v0 + m0 * h / 3, v1 - m1 * h / 3, v1, s) - flow(f0 + h * s, poses)) < 1e-9
    breath = bake(lambda t: 1 + 0.02 * wave(t, 120, 0.25), 240, step=12)
    assert abs(breath[0][1] - breath[-1][1]) < 1e-9 and abs(breath[0][2] - breath[-1][2]) < 1e-6, "loop seam"
    assert "cubicValue" in hermite_xml(pts) and "CubicEaseInterpolator" in track_xml([(0, 1), (7, 0.1), (20, 1, "out")])
    print("self-test OK")


def _parse_keys(tokens):
    keys = []
    for tok in tokens:
        parts = tok.split(":")
        key = (float(parts[0]), float(parts[1]))
        keys.append(key + ((parts[2],) if len(parts) > 2 else ()))
    return keys


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bake living motion into RML keyframes (60 fps frames).")
    sub = ap.add_subparsers(dest="cmd")
    t = sub.add_parser("track", help="one move: eases into every key; FRAME:VALUE[:out]")
    t.add_argument("keys", nargs="+")
    f = sub.add_parser("flow", help="acting through poses, never stopping, never overshooting; FRAME:VALUE")
    f.add_argument("keys", nargs="+")
    w = sub.add_parser("wave", help="a seamless sine loop, for breathing, sway and bob")
    w.add_argument("--base", type=float, default=0)
    w.add_argument("--amp", type=float, required=True)
    w.add_argument("--period", type=float, required=True, help="frames; must divide --length")
    w.add_argument("--length", type=float, required=True, help="the animation's duration in frames")
    w.add_argument("--phase", type=float, default=0)
    w.add_argument("--step", type=float, default=0, help="frames between samples (default: a quarter period)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        self_test()
        return 0
    try:
        return _run(a)
    except ValueError as err:
        sys.stderr.write(f"motion_keys: {err}\n")
        return 2


def _run(a):
    if a.cmd == "track":
        print(track_xml(_parse_keys(a.keys), indent=""))
    elif a.cmd == "flow":
        print(hermite_xml(flow_points([k[:2] for k in _parse_keys(a.keys)]), indent=""))
    elif a.cmd == "wave":
        if a.period <= 0 or a.length <= 0:
            sys.stderr.write("motion_keys: --period and --length must be positive\n")
            return 2
        if abs(a.length / a.period - round(a.length / a.period)) > 1e-9:
            sys.stderr.write("motion_keys: --period must divide --length or the loop pops\n")
            return 2
        step = a.step or a.period / 4
        print(hermite_xml(bake(lambda x: a.base + a.amp * wave(x, a.period, a.phase), a.length, step), indent=""))
    else:
        sys.stderr.write("usage: motion_keys.py {track,flow,wave} ... (see --help)\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
