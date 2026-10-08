# Motion taste in Rive

`--verify`, `inspect` and a screenshot prove a file is not broken. This page is about
whether it is worth using. The house style is the same one the lottie-animator skill
follows (`references/motion-taste.md` there): quiet, precise, warm — zero overshoot,
nothing growing from a point, rests as part of the motion. Depart from it when the brief
asks, and say so.

## Taste, craft & delight vs AI slop

A vibe-coded app often feels lifeless because generative AI defaults to the middle:
it implements raw functional features and bare-bones static UI, skipping the "last mile"
of craft. What makes users stop and feel delight is intentional, human-calibrated motion:

1. **Never ask for "generic animation"**: Pick the specific mechanism (Keyframes, Springs,
   Gestures, Physics, SVG paths, Layout transitions, Rive, Skeletal rigs, Particles, Shaders).
   See `references/animation-toolbox-cheatsheet.md` for the full 11-archetype matrix.
2. **Combine for the feeling**: The best apps do not rely on one technique in isolation.
   Layer a Rive character with an SVG morphing background mask, 3D parallax depth, host-level
   continuous gesture tilt, and particle celebration bursts.
3. **The 5-beat action choreography**:
   - **Beat 1: Rest**: Settled neutral pose.
   - **Beat 2: Anticipation**: Counter-movement (crouch before jumping, pull back before drinking).
   - **Beat 3: Action Apex**: Peak transformation/displacement.
   - **Beat 4: Settle**: Elastic dampening past the target.
   - **Beat 5: Return to Rest**: Clean loop back to baseline.


## Easing, as RML

Every eased segment is a keyframe (or transition) with `interpolationType="cubic"` and a
nested curve. Without the child the ease silently does nothing.

```xml
<KeyFrameDouble value="0" frame="0" interpolationType="cubic">
    <CubicEaseInterpolator x1="0.23" y1="1" x2="0.32" y2="1"/>
</KeyFrameDouble>
```

| Token | `x1 y1 x2 y2` | Use for |
|---|---|---|
| out | `0.23 1 0.32 1` | Arrivals, feedback, state changes on controls |
| in-out | `0.77 0 0.175 1` | Travel on screen, morphs, loops |
| glide | `0.32 0.72 0 1` | Large surfaces: sheets, cards, panels |
| in | `0.55 0 1 0.45` | Exits only, about 70% of the entrance duration |
| linear | `interpolationType="linear"` | Constant rotation, progress |
| playful | `ElasticInterpolator`, or `0.34 1.56 0.64 1` via `cubicValue` | Only when the brief asks for bounce |

Remember the defaults work against you: keyframes are `hold` and animations are
`oneShot` unless you write otherwise.

## Timing

| Motion | Transition `duration` (ms) | Timeline frames at 60 fps |
|---|---|---|
| Press, hover, toggle | 120–240 | 6–14 |
| Icon or card entrance | 300–500 | 18–30 |
| Hero reveal | 500–700 | 30–42 |
| Stagger between siblings | — | 3 |
| Hold before a loop repeats | — | ≥ 12 |

`StateTransition.duration` is milliseconds; `LinearAnimation.duration` is frames.

**For controls, prefer state transitions to timelines.** One single-key `hold` animation
per state, and an eased `StateTransition` between them: the runtime blends the two poses
over `duration`, the result is interruptible, and there is no in-between to author. The
recipe below is built that way.

## Art direction

- **Palette** (ARGB): paper `FFF3EEE6`, sand `FFE4D9C6`, ink `FF1E1B18`, stone
  `FF8A8178`, clay `FFC8522B`, sage `FF6F8163`, night `FF171513`. One accent per
  artboard.
- **No slop.** No purple or indigo gradients, no neon on black, no glows. `Feather`
  on a stroke is the only glow the format does, and it is almost never needed.
- **Squircle surfaces.** `Rectangle` corners are circular. For a continuous-curvature
  card, build the path with `motion.squircle()` from the lottie-animator skill and pass
  it through `scripts/lottie2rml.py`, which writes it as a `PointsPath` of detached
  cubic vertices. Pills (radius = half the height) are fine as `Rectangle`.
- **One stroke weight**, round caps and joins.
- **Draw order**: the first sibling paints on top. A knob goes before its track.

## The taste pass

After the build, capture the motion and judge it:

```bash
mkdir -p build/onion
for k in 0 2 4 6 8 10 12 14 16 18 20 22; do
  rive . --screenshot=build/onion/f$(printf %02d $k).png --pointer=click@120,80 --advance=$k
done
ffmpeg -loglevel error -y -framerate 12 -pattern_type glob -i 'build/onion/f*.png' \
  -vf tmix=frames=12 -update 1 -frames:v 12 build/onion.png
```

`build/onion.png` averages the captures: the spacing between ghosts is the easing, their
path is the arc. Drop the `--pointer` for an autonomous timeline. Then ask:

1. **Spacing** — do ghosts bunch at the end of each move (an ease-out), not evenly?
2. **Arcs** — does long travel curve?
3. **Origin** — does anything grow from a point or pop from nothing?
4. **Hierarchy** — one hero, landing last?
5. **Restraint** — is anything moving that would be better still?
6. **Rest** — a readable hold at the end, and at both ends of a loop?
7. **Colour** — one accent, no slop, legible on every background?
8. **Round trip** — after-again matches rest (`--pointer=click` twice, with a `move` between)?

## Recipe: a toggle that feels like hardware

Verified with the Rive CLI 1.0.2: `--verify` clean, `problems: []`, rest and off
captures byte-identical, on and mid-transition distinct, onion showing the knob
decelerating into place.

```xml
<Rive version="1" kind="fragment">
    <Artboard defaultStateMachineId="0:20" styleId="0:2" width="240" height="160" name="Toggle" id="0:1">
        <LayoutComponentStyle name="Artboard Style" id="0:2"/>
        <Fill name="Paper">
            <SolidColor colorValue="FFF3EEE6" name="Color"/>
        </Fill>

        <Shape x="92" y="80" name="Knob" id="0:10">
            <Ellipse width="52" height="52" originX="0.5" originY="0.5" name="Path"/>
            <Fill name="Fill">
                <SolidColor colorValue="FFF3EEE6" name="Color"/>
            </Fill>
        </Shape>

        <Shape x="120" y="80" name="Track" id="0:11">
            <Rectangle width="120" height="64" cornerRadiusTL="32" originX="0.5" originY="0.5" name="Path"/>
            <Fill name="Fill">
                <SolidColor colorValue="FF8A8178" name="Color" id="0:12"/>
            </Fill>
        </Shape>

        <LinearAnimation duration="1" name="Off" id="0:30">
            <KeyedObject objectId="0:10">
                <KeyedProperty propertyKey="13">
                    <KeyFrameDouble value="92" frame="0" interpolationType="hold"/>
                </KeyedProperty>
            </KeyedObject>
            <KeyedObject objectId="0:12">
                <KeyedProperty propertyKey="37">
                    <KeyFrameColor value="FF8A8178" frame="0" interpolationType="hold"/>
                </KeyedProperty>
            </KeyedObject>
        </LinearAnimation>

        <LinearAnimation duration="1" name="On" id="0:31">
            <KeyedObject objectId="0:10">
                <KeyedProperty propertyKey="13">
                    <KeyFrameDouble value="148" frame="0" interpolationType="hold"/>
                </KeyedProperty>
            </KeyedObject>
            <KeyedObject objectId="0:12">
                <KeyedProperty propertyKey="37">
                    <KeyFrameColor value="FF6F8163" frame="0" interpolationType="hold"/>
                </KeyedProperty>
            </KeyedObject>
        </LinearAnimation>

        <StateMachine name="State Machine 1" id="0:20">
            <StateMachineTrigger name="tap" id="0:21"/>
            <StateMachineListenerSingle targetId="0:11" listenerTypeValue="click" name="Tap">
                <ListenerTriggerChange inputId="0:21"/>
            </StateMachineListenerSingle>

            <StateMachineLayer name="Toggle" id="0:22">
                <AnyState x="480" y="0"/>
                <ExitState x="560" y="0"/>
                <EntryState x="0" y="16">
                    <StateTransition stateToId="0:23"/>
                </EntryState>

                <AnimationState animationId="0:30" x="160" y="0" id="0:23">
                    <StateTransition stateToId="0:24" duration="240" interpolationType="cubic">
                        <CubicEaseInterpolator x1="0.23" y1="1" x2="0.32" y2="1"/>
                        <TransitionTriggerCondition inputId="0:21"/>
                    </StateTransition>
                </AnimationState>

                <AnimationState animationId="0:31" x="320" y="0" id="0:24">
                    <StateTransition stateToId="0:23" duration="240" interpolationType="cubic">
                        <CubicEaseInterpolator x1="0.23" y1="1" x2="0.32" y2="1"/>
                        <TransitionTriggerCondition inputId="0:21"/>
                    </StateTransition>
                </AnimationState>
            </StateMachineLayer>
        </StateMachine>
    </Artboard>
</Rive>
```

Why it reads well: one hero property (the knob's `x`), the colour change riding the
same 240 ms `out` transition, 6 px of track showing around the knob on both sides, the
knob in the paper colour so the track carries the state, and both directions authored so
the control never latches. The listener targets the track, not the artboard, and the
knob is declared first so it draws on top. The host drives it with
`useStateMachineInput(rive, 'State Machine 1', 'tap')?.fire()`, or lets the click
listener handle the pointer on its own.
