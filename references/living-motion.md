# Living motion in Rive

How to make a `.riv` feel alive instead of busy: characters, icons, controls, loaders and
whole scenes. The method is [rossark-motion-skill](https://github.com/rossark0/rossark-motion-skill)
(MIT, rossark0) translated to RML: its engine becomes `scripts/motion_keys.py`, its clocks
become state machine layers, and its checks become renders you read before shipping.
`examples/living-mascot/build.py` is the worked example; every rule below is in it.

Read the project's own motion notes first (a `MOTION.md` next to the art, `CLAUDE.md`, saved
memory). The owner's rules override everything here.

## 1. Principles

1. **Never teleport.** Nothing snaps from one value to another. In Rive the snaps hide in three
   places, and all three build clean:
   - a transition into a one-frame pose with no `duration` (lint `RML012`). Give it
     `duration="160"`–`"300"` (milliseconds) and a nested `CubicEaseInterpolator`;
   - a `hold` keyframe between two different values, the default when `interpolationType` is
     missing;
   - a colour swapped with `hold`. Colours blend: `<KeyFrameColor ... interpolationType="linear"/>`.
2. **Calm by default.** Two curves cover almost everything:

   | Moves that | Curve | `x1 y1 x2 y2` |
   |---|---|---|
   | travel (gaze, sway, a lid closing, a knob crossing) | ease-in-out | `0.77 0 0.175 1` |
   | open or arrive (a lid reopening, a pop, a check drawing on) | ease-out | `0.23 1 0.32 1` |
   | loop forever (rotation, rain, a conveyor) | linear | — |
   | fall away, under gravity | ease-in, or bake the parabola | — |

   `ElasticInterpolator` only when the brand asks for bounce.
3. **Small amplitudes.** Breathing 1–2% of the height, a head tilt 2–6°, a sway 1.5–4°. When unsure,
   halve it.
4. **Pivots, and keyed values are absolute.** Every moving part is a `Node` placed at its joint (a
   stem's base, a hinge, the feet). A keyed `x`, `y` or `rotation` replaces the authored value in the
   parent's space, so keying `y="0"` on a node authored at `y="262"` throws it off the artboard.
   Put the animated node inside a parent at the pivot, so its rest value is `0`.
5. **Overlap and follow-through by delay, not springs.** A child reads its parent a few frames
   late at part of the strength: `child(t) = 0.5 × (parent(t − 6) − parent(t))`. The bell's
   clapper and the mascot's sprout do this; `motion_keys.bake` writes it as keyframes.
6. **Variety without chaos.** Repeated items (dots, bars, sparks) each get their own phase, period,
   size and distance from `seeded(i)`. Periods divide the loop length, so the loop still closes.
   Never everything in sync.
7. **One main action, two or three idle loops.** In Rive each is a state machine layer. Side
   elements stay quiet.
8. **Opacity only to appear or disappear** (a spark, a blush, a catchlight during a blink). Never
   to dim something halfway.
9. **The layout never moves.** Motion lives inside the artboard; the host never resizes the canvas
   to animate.
10. **The rest pose is the authored pose.** A host with reduced motion, or one that never starts
    the machine, shows the values written on the nodes. Author them equal to the rest state
    (the mascot's mouth is authored at `scaleY="0.42"`, its cheeks at `opacity="0"`). One-shots
    must read on their final frame.
11. **Nothing runs unseen.** The host pauses the instance off screen or in the background.
12. **Enough frames.** At 60 fps a blink closes in 7 frames, holds 2, reopens in 11; anything
    under 6 frames flickers. GIFs play at 50 fps at most.

## 2. Three ways to key a channel

Rive eases each keyframe segment on its own, so a chain of poses keyed with ease-in-out slows to
zero at every pose: the character stops dead at each key and reads as a robot.

| Job | Use | What it writes |
|---|---|---|
| one move: a blink, a press, a lid | `track` | one `cubic` keyframe per segment, eased into every key |
| acting through poses: a hop, a lean, a head turn | `flow` | monotone cubic Hermite through the poses, never stopping, never overshooting |
| anything computed: breathing, sway, follow-through, sums of waves | `bake` | the function sampled every few frames with its true slope |

`flow` and `bake` write each segment as a `cubicValue` keyframe whose `CubicValueInterpolator`
holds the Hermite handles (`x1 = 1/3`, `x2 = 2/3`, `y1 = v0 + m0·h/3`, `y2 = v1 − m1·h/3`). With
the time handles at the thirds, time stays linear and the curve is the Hermite exactly; measured
in the real renderer it matches to a quarter pixel.

```bash
python3 scripts/motion_keys.py track 0:1 7:0.1 9:0.1 20:1:out          # a blink
python3 scripts/motion_keys.py flow 0:1 9:0.86 15:1.1 44:0.8 52:1.04 76:1   # crouch, stretch, squash, settle
python3 scripts/motion_keys.py wave --base 1 --amp 0.016 --period 120 --length 240   # breathing
```

Each prints the `<KeyFrameDouble>` lines for one `<KeyedProperty>`. From Python, `K.bake(fn, length)`
and `K.keyed(object_id, {property_key: lines})` build whole `<KeyedObject>` blocks; keep every
number in a `TOKENS` dict at the top of the build script so "slower" is a one-line change.

## 3. Layers are channels

A layer keys its own node; layers never key the same property. Nest the nodes so their transforms
compose, outermost first:

| Layer | Node chain (mascot) | Keys |
|---|---|---|
| Act (the main action) | `Ground › Hop` | y, scale (squash and stretch) |
| Idle (never stops) | `Hop › Breath › Lean` | scale (breath), rotation (lean) |
| Gaze (host driven) | `Face › Glance › Eyes` | x, through a `BlendState1DInput` on `lookX` |
| Blink (its own loop) | `Eyes › Blink › Mood` | scaleY (blink); Act keys `Mood` for the happy squint |

Loop lengths that divide one another (idle 4 s, blink 8 s) keep the whole character periodic, so
a recording or a GIF of it closes without a seam.

Blend weights run 0–100 and every pose must key every blended property (`rive docs easing`).

## 4. Recipes by subject

Frames at 60 fps.

| Subject | Recipe |
|---|---|
| Character | breathing 1.5% over 120 f with `scaleX = scaleY^-0.6`; a blink every 3–4 s; gaze glides in ~30 f and holds ≥ 60 f |
| Tail, sprout, hair, antenna | rotation at the root, the parent's motion 6–9 f late at 0.4–0.6 |
| Bell, phone, alarm | a decaying swing at the hinge (18°, −15°, 10°, −6°, 0 over 42 f); the clapper follows 4 f late |
| Plant, flag | sway 1.5–4° at the base over 180–360 f; leaves on seeded phases |
| Equalizer, waves | each bar the sum of two waves with seeded periods that divide the loop |
| Loader | linear rotation plus a trim chase whose start and end ease on `travel`; the arc advances a whole number of turns per loop |
| Icon, logo | plays once on appear, then rests; no endless loops on interface chrome |
| Celebration (like, rating, success) | anticipation dip to 0.84–0.9, pop to 1.12–1.16, settle; sparks on seeded rays appear and leave with opacity |
| Progress, charts | the value drives a blend; completion is its own state (a colour blend and one breath out) |
| Floating, hopping | crouch 9 f, stretch, a gravity arc `y = −h·(1 − ((t − apex)/half)²)`, squash 0.8 on contact, settle by 30 f |
| Shadow | stays on the floor; its scale is `1 + y/170` while the body is in the air |

## 5. Characters

- **Face.** Eyes as plain dark shapes under a `Blink` node scaled on Y about the eye centre. A
  catchlight drawn on the eye leaves (opacity) while the lid is down, or it shows as a white seam.
  The lower lid is optional; a blink of 7/2/11 frames reads as a blink at any size.
- **Gaze.** The host writes `lookX` (0 left, 50 ahead, 100 right); a `BlendState1DInput` mixes three
  poses. The eyes travel further than the mouth (eyes lead the turn). Blink on a turn.
- **Body.** The breath scales the body from its feet; the lean rotates it from its feet. Both
  never stop, even during the action.
- **Acting.** Key the main action with `flow`. One `poke` trigger, an exit-time return to a pose
  state: `Rest → Hop → Rest`. Happy on landing: the eyes squint to 0.5, the cheeks appear, the
  mouth opens, all back by ~90 f.
- **Alive checklist.** Nothing frozen while on screen. No moment where every part stops. The
  sprout, the clapper, the knob arrive after the body. Left and right never mirror. The shadow
  changes with the height. Every prop or cursor enters from beyond the edge, already moving.

## 6. Interface motion

- **Frequency decides how much.** Hundreds of times a day: nothing. Tens (toggles, tabs, likes):
  a fast, small change. Rare (onboarding, rewards, empty states): characters and scenes.
- **Durations.** Press 100–160 ms, popovers 125–200, menus 150–250, sheets 200–500. Keep interface
  moves under 300 ms.
- **Exits are faster than entrances.** Like plays 36 f; unlike mixes back in 160 ms.
- **Nothing from nothing.** Enter from 0.9–0.97 scale with opacity, never from 0 (sparks excepted).
- **Interruptible.** A transition into a pose mixes from the current value, so a fast double tap
  turns around mid-flight. A one-shot re-entered restarts at frame 0: use poses for anything a
  person can toggle quickly, one-shots only for accents (the knob's squish, the bell's swing).

## 7. Checking it

Builds and inspections never look at a pixel. Render, then read the numbers.

```bash
rive <dir> --screenshot=f.png --advance=30                    # the frame shows animation time 29
for n in 1 15 30 45 60; do rive <dir> --screenshot=f$n.png --advance=$n; done
ffmpeg -pattern_type glob -i 'f*.png' -vf "tile=5x1" sheet.png  # a contact sheet to read
rive <dir> --screenshot=hop.png --pointer=click@160,200 --advance=45
node scripts/make-gifs.mjs --sheet                             # every README GIF and its sheet
```

- Two frames of a loop must differ; frame 0 must equal the last frame (`make-gifs` sessions end
  in the state they started in, so the GIF loops without a seam).
- A control must look different after a click and the same again after a second one.
- With a reference video, measure it frame by frame rather than by eye: rossark's
  `tools/sheet.sh` (contact sheets at the source frame rate), `tools/track_edges.py` (a 2% squash
  or a float is invisible on a sheet and obvious in numbers) and `tools/sample_colors.py`.

## 8. Workflow

1. Read the project's notes and the art's header comments.
2. List what could live: the subject, its parts and pivots, repeated items, the background.
3. Pick one main action and two or three idle loops; cut the rest.
4. Split the art into nodes at their pivots without changing frame 0.
5. Put every number in tokens; key with `track`, `flow` or `bake`.
6. Lint (`rml_lint.py`: dead inputs, snaps, seams), `rive --verify`, `rive inspect` problems `[]`.
7. Render and read: frame 0, the final frame of each one-shot, the loop seam, the alive checklist.
8. Hand off in plain words: what moves, what was left still on purpose, what was not seen on a
   real device.
