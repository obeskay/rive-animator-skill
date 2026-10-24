#!/usr/bin/env python3
"""Build scene.rml for the living mascot: python3 examples/living-mascot/build.py

A worked example of the method in references/living-motion.md. Every number that
shapes the motion is in TOKENS, so "slower", "smaller" or "calmer" is a one-line
edit followed by a rebuild. Four state machine layers run at once, each keying its
own node in a nested chain, so idle life never stops while the character acts:

  Idle   breathing (volume kept), a slow lean, the sprout swaying a beat behind
  Blink  blinks close in 7 frames, hold 2, reopen in 11; one double blink on a glance
  Gaze   lookX 0..100 blends three poses; the eyes lead, the mouth follows
  Act    poke: crouch, stretch, a gravity arc, squash on contact, a happy settle
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
import motion_keys as K  # noqa: E402

TOKENS = {
    "breath_period": 120, "breath_amp": 0.016,        # 2 s, 1.6% of the height
    "lean_period": 240, "lean_amp": 0.03,             # 4 s, about 1.7 degrees
    "sprout_sway": 0.07, "sprout_lag": 8, "sprout_follow": 0.5,
    "hop_height": 48, "crouch": 0.86, "squash": 0.8,
    "gaze_face": 9, "gaze_eyes": 4,                   # artboard units at lookX 0 / 100
    "blinks": [78, 270, 296, 410],                    # frames in the 8 s blink loop
}
T = TOKENS
EMBER, CHEEK, SAGE, STEM = "FFE4572E", "FFF7967E", "FF6F8F72", "FF5B7A5E"
INK, CREAM, SHADOW = "FF1F1C19", "FFFBF8F2", "408E877E"   # a stone shadow reads on light and dark pages
IDLE_LEN, BLINK_LEN, HOP_LEN = 240, 480, 90


def bake(fn, length, step=6, periodic=True):
    return K.hermite_xml(K.bake(fn, length, step, periodic), indent="")


def flow(*keys):
    return K.hermite_xml(K.flow_points(list(keys)), indent="")


def flow_fn(*keys):
    return lambda t: K.flow(t, list(keys))


def hold(value, color=False):
    tag = "KeyFrameColor" if color else "KeyFrameDouble"
    return f'<{tag} value="{value if color else K._num(value)}" frame="0" interpolationType="hold"/>'


# ---------------------------------------------------------------- idle: one clock, every part out of phase
breath = lambda t: 1 + T["breath_amp"] * K.wave(t, T["breath_period"], 0.25)
lean = lambda t: T["lean_amp"] * K.wave(t, T["lean_period"])
sprout_idle = lambda t: (T["sprout_sway"] * K.wave(t, T["breath_period"], 0.4)
                         + T["sprout_follow"] * (lean(t - T["sprout_lag"]) - lean(t)))
idle = [
    K.keyed("0:11", {17: bake(breath, IDLE_LEN), 16: bake(lambda t: breath(t) ** -0.6, IDLE_LEN)}),
    K.keyed("0:12", {15: bake(lean, IDLE_LEN, step=20)}),
    K.keyed("0:31", {15: bake(sprout_idle, IDLE_LEN, step=10)}),
    K.keyed("0:60", {16: bake(lambda t: 1 + 0.6 * (breath(t) ** -0.6 - 1), IDLE_LEN, step=10)}),
]

# ---------------------------------------------------------------- blink: close fast, reopen slower, now and then twice
blink_keys = [(0, 1)]
for b in T["blinks"]:
    blink_keys += [(b, 1), (b + 7, 0.1), (b + 9, 0.1), (b + 20, 1, "out")]
blink_keys.append((BLINK_LEN, 1))
glint_keys = [(0, 1)]                      # the catchlight leaves while the lid is down, or it shows as a white seam
for b in T["blinks"]:
    glint_keys += [(b, 1), (b + 4, 0), (b + 12, 0), (b + 18, 1)]
glint_keys.append((BLINK_LEN, 1))
glance = [(0, 0), (262, 0), (270, -4, "out"), (334, -4), (344, 0)]   # a glance aside, blinking on the turn
blink = [
    K.keyed("0:24", {17: K.track_xml(blink_keys, indent="")}),
    K.keyed("0:22", {13: K.track_xml(glance + [(BLINK_LEN, 0)], indent="")}),
    K.keyed("0:26", {18: K.track_xml(glint_keys, indent="")}),
    K.keyed("0:27", {18: K.track_xml(glint_keys, indent="")}),
]

# ---------------------------------------------------------------- act: one main action, acted through poses
sy_keys = [(0, 1), (9, T["crouch"]), (15, 1.1), (29, 1.0), (40, 1.06), (44, T["squash"]), (52, 1.04), (64, 0.99), (76, 1)]
hop_sy = flow_fn(*sy_keys)


def hop_y(t):
    """On the ground until frame 14, then a gravity arc that lands on frame 44."""
    if t <= 14 or t >= 44:
        return 0.0
    return -T["hop_height"] * (1 - ((t - 29) / 15) ** 2)


lift = lambda t: 1 + hop_y(t) / 170        # the shadow shrinks with the height
act = [
    K.keyed("0:10", {
        14: bake(hop_y, HOP_LEN, step=2, periodic=False),
        17: flow(*sy_keys),
        16: bake(lambda t: hop_sy(t) ** -0.6, HOP_LEN, step=2, periodic=False),   # keep the volume
    }),
    K.keyed("0:25", {17: flow((0, 1), (9, 0.8), (15, 1), (44, 1), (49, 0.5), (70, 0.5), (84, 1))}),
    K.keyed("0:40", {17: flow((0, 0.42), (12, 0.42), (20, 0.8), (44, 0.8), (50, 1), (70, 1), (86, 0.42))}),
    K.keyed("0:44", {18: flow((0, 0), (44, 0), (50, 0.9), (72, 0.9), (88, 0))}),
    K.keyed("0:30", {15: flow((0, 0), (10, -0.14), (18, 0.22), (30, -0.06), (44, 0), (49, -0.26),
                              (58, 0.16), (67, -0.08), (76, 0.03), (86, 0))}),
    K.keyed("0:61", {
        16: bake(lambda t: lift(t) * (1 + 0.6 * (hop_sy(t) ** -0.6 - 1)), HOP_LEN, step=2, periodic=False),
        17: bake(lift, HOP_LEN, step=2, periodic=False),
    }),
]
rest = [
    K.keyed("0:10", {14: hold(0), 16: hold(1), 17: hold(1)}),
    K.keyed("0:25", {17: hold(1)}),
    K.keyed("0:40", {17: hold(0.42)}),
    K.keyed("0:44", {18: hold(0)}),
    K.keyed("0:30", {15: hold(0)}),
    K.keyed("0:61", {16: hold(1), 17: hold(1)}),
]


def look(x):
    return [K.keyed("0:20", {13: hold(x * T["gaze_face"])}), K.keyed("0:21", {13: hold(x * T["gaze_eyes"])})]


def animation(aid, name, length, blocks, loop=False):
    lv = ' loopValue="loop"' if loop else ""
    return (f'        <LinearAnimation{lv} duration="{length}" name="{name}" id="{aid}">\n'
            + "\n".join(blocks) + "\n        </LinearAnimation>")


def eye(side):
    x = 25 * side
    gid = "0:26" if side < 0 else "0:27"
    return f'''                                <Shape x="{x + 3}" y="-5" name="Glint{'L' if side < 0 else 'R'}" id="{gid}">
                                    <Ellipse width="5" height="5" originX="0.5" originY="0.5" name="Path"/>
                                    <Fill name="Fill"><SolidColor colorValue="{CREAM}" name="Cream"/></Fill>
                                </Shape>
                                <Shape x="{x}" name="Eye{'L' if side < 0 else 'R'}">
                                    <Ellipse width="14" height="20" originX="0.5" originY="0.5" name="Path"/>
                                    <Fill name="Fill"><SolidColor colorValue="{INK}" name="Ink"/></Fill>
                                </Shape>'''


SCENE = f'''<Rive version="1" kind="fragment">
    <!-- generated by build.py: edit TOKENS there and rebuild, not this file -->
    <Artboard defaultStateMachineId="0:80" width="320" height="300" name="Mascot" styleId="0:2" id="0:1">
        <LayoutComponentStyle name="Artboard Style" id="0:2"/>
        <Fill name="Background">
            <SolidColor colorValue="00000000" name="Clear"/>
        </Fill>

        <Node x="160" y="262" name="Ground">
        <Node name="Hop" id="0:10">
            <Node name="Breath" id="0:11">
                <Node name="Lean" id="0:12">
                    <Node y="-72" name="Face" id="0:20">
                        <Node name="Glance" id="0:22">
                            <Node name="Eyes" id="0:21">
                                <Node name="Blink" id="0:24">
                                    <Node name="Mood" id="0:25">
{eye(-1)}
{eye(1)}
                                    </Node>
                                </Node>
                            </Node>
                        </Node>
                        <Node y="16" scaleY="0.42" name="Mouth" id="0:40">
                            <Shape name="MouthShape">
                                <PointsPath isClosed="true" name="Path">
                                    <CubicDetachedVertex x="-10" y="0" inRotation="1.5707963" inDistance="5.5" outRotation="0" outDistance="0"/>
                                    <CubicDetachedVertex x="10" y="0" inRotation="3.1415927" inDistance="0" outRotation="1.5707963" outDistance="5.5"/>
                                    <CubicDetachedVertex x="0" y="10" inRotation="0" inDistance="5.5" outRotation="3.1415927" outDistance="5.5"/>
                                </PointsPath>
                                <Fill name="Fill"><SolidColor colorValue="{INK}" name="Ink"/></Fill>
                            </Shape>
                        </Node>
                        <Node y="12" opacity="0" name="Cheeks" id="0:44">
                            <Shape x="-44" name="CheekL">
                                <Ellipse width="18" height="10" originX="0.5" originY="0.5" name="Path"/>
                                <Fill name="Fill"><SolidColor colorValue="{CHEEK}" name="Blush"/></Fill>
                            </Shape>
                            <Shape x="44" name="CheekR">
                                <Ellipse width="18" height="10" originX="0.5" originY="0.5" name="Path"/>
                                <Fill name="Fill"><SolidColor colorValue="{CHEEK}" name="Blush"/></Fill>
                            </Shape>
                        </Node>
                    </Node>
                    <Shape x="-38" y="-106" rotation="-0.5" name="Shine">
                        <Ellipse width="30" height="14" originX="0.5" originY="0.5" name="Path"/>
                        <Fill name="Fill"><SolidColor colorValue="33FBF8F2" name="Shine"/></Fill>
                    </Shape>
                    <Shape name="Body" id="0:13">
                        <PointsPath isClosed="true" name="Path">
                            <CubicDetachedVertex x="0" y="-134" inRotation="3.1415927" inDistance="52" outRotation="0" outDistance="52"/>
                            <CubicDetachedVertex x="75" y="-60" inRotation="-1.5707963" inDistance="42" outRotation="1.5707963" outDistance="34"/>
                            <CubicDetachedVertex x="0" y="0" inRotation="0" inDistance="58" outRotation="3.1415927" outDistance="58"/>
                            <CubicDetachedVertex x="-75" y="-60" inRotation="1.5707963" inDistance="34" outRotation="-1.5707963" outDistance="42"/>
                        </PointsPath>
                        <Fill name="Fill"><SolidColor colorValue="{EMBER}" name="Ember"/></Fill>
                    </Shape>
                    <Node y="-128" name="Sprout" id="0:30">
                        <Node name="SproutSway" id="0:31">
                            <Node x="2" y="-21" rotation="-0.45" name="LeafR">
                                <Shape x="12">
                                    <Ellipse width="25" height="12" originX="0.5" originY="0.5" name="Path"/>
                                    <Fill name="Fill"><SolidColor colorValue="{SAGE}" name="Sage"/></Fill>
                                </Shape>
                            </Node>
                            <Node x="1" y="-17" rotation="3.55" name="LeafL">
                                <Shape x="10">
                                    <Ellipse width="20" height="10" originX="0.5" originY="0.5" name="Path"/>
                                    <Fill name="Fill"><SolidColor colorValue="{SAGE}" name="Sage"/></Fill>
                                </Shape>
                            </Node>
                            <Shape name="Stem">
                                <PointsPath isClosed="false" name="Path">
                                    <CubicDetachedVertex x="0" y="8" inRotation="1.5707963" inDistance="0" outRotation="-1.5707963" outDistance="12"/>
                                    <CubicDetachedVertex x="2" y="-21" inRotation="1.75" inDistance="10" outRotation="-1.5707963" outDistance="0"/>
                                </PointsPath>
                                <Stroke thickness="4" cap="round" name="Stroke"><SolidColor colorValue="{STEM}" name="Stem"/></Stroke>
                            </Shape>
                        </Node>
                    </Node>
                </Node>
            </Node>
        </Node>
        </Node>

        <Node x="160" y="263" name="Shadow" id="0:60">
            <Node name="ShadowLift" id="0:61">
                <Shape name="ShadowShape">
                    <Ellipse width="128" height="14" originX="0.5" originY="0.5" name="Path"/>
                    <Fill name="Fill"><SolidColor colorValue="{SHADOW}" name="Shadow"/></Fill>
                </Shape>
            </Node>
        </Node>

{animation("0:50", "Idle", IDLE_LEN, idle, loop=True)}
{animation("0:51", "Blinks", BLINK_LEN, blink, loop=True)}
{animation("0:52", "Rest", 1, rest)}
{animation("0:53", "Hop", HOP_LEN, act)}
{animation("0:54", "LookLeft", 1, look(-1))}
{animation("0:55", "LookAhead", 1, look(0))}
{animation("0:56", "LookRight", 1, look(1))}

        <StateMachine name="State Machine 1" id="0:80">
            <StateMachineNumber name="lookX" id="0:81" value="50"/>
            <StateMachineTrigger name="poke" id="0:82"/>
            <StateMachineListenerSingle targetId="0:13" listenerTypeValue="click" name="Poke">
                <ListenerTriggerChange inputId="0:82"/>
            </StateMachineListenerSingle>

            <StateMachineLayer name="Idle" id="0:83">
                <AnyState x="560" y="-120"/>
                <ExitState x="680" y="-120"/>
                <EntryState x="0" y="0"><StateTransition stateToId="0:84"/></EntryState>
                <AnimationState animationId="0:50" x="200" y="0" id="0:84"/>
            </StateMachineLayer>

            <StateMachineLayer name="Blink" id="0:85">
                <AnyState x="560" y="-120"/>
                <ExitState x="680" y="-120"/>
                <EntryState x="0" y="0"><StateTransition stateToId="0:86"/></EntryState>
                <AnimationState animationId="0:51" x="200" y="0" id="0:86"/>
            </StateMachineLayer>

            <StateMachineLayer name="Gaze" id="0:87">
                <AnyState x="560" y="-120"/>
                <ExitState x="680" y="-120"/>
                <EntryState x="0" y="0"><StateTransition stateToId="0:88"/></EntryState>
                <BlendState1DInput inputId="0:81" x="200" y="0" id="0:88">
                    <BlendAnimation1D animationId="0:54" value="0"/>
                    <BlendAnimation1D animationId="0:55" value="50"/>
                    <BlendAnimation1D animationId="0:56" value="100"/>
                </BlendState1DInput>
            </StateMachineLayer>

            <StateMachineLayer name="Act" id="0:89">
                <AnyState x="560" y="-120"/>
                <ExitState x="680" y="-120"/>
                <EntryState x="0" y="0"><StateTransition stateToId="0:90"/></EntryState>
                <AnimationState animationId="0:52" x="200" y="0" id="0:90">
                    <StateTransition stateToId="0:91">
                        <TransitionTriggerCondition inputId="0:82"/>
                    </StateTransition>
                </AnimationState>
                <AnimationState animationId="0:53" x="360" y="0" id="0:91">
                    <StateTransition stateToId="0:90" enableExitTime="true" exitTimeIsPercetange="true" exitTime="100"/>
                </AnimationState>
            </StateMachineLayer>
        </StateMachine>
    </Artboard>
</Rive>
'''

if __name__ == "__main__":
    (HERE / "scene.rml").write_text(SCENE)
    print(f"wrote {HERE / 'scene.rml'}")
