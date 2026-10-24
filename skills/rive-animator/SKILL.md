---
name: rive-animator
description: >-
  Create, animate, inspect, lint, and repair Rive (.riv) files, RML scenes, and State Machines, and make
  them feel alive. Use when asked to build an interactive vector animation, mascot, or UI component from a
  brief or an SVG; give a character idle life (breathing, blinks, gaze, follow-through) or a control motion
  that never snaps; convert SVG/Lottie to Rive RML; inspect an existing .riv binary (artboards, animations,
  state machines, inputs, listeners, view models); generate copy-paste runtime wiring across React, Vue,
  Svelte, Web Canvas, Flutter, iOS/SwiftUI, Android Kotlin, and React Native; record README GIFs from the
  real runtime; or diagnose a Rive component that renders blank, ignores clicks, snaps, or fails to transition.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Rive Animator

A `.riv` is a small interactive program, not a picture: artboards, timelines, and a state machine
deciding which timeline plays and when. The failures that cost time never raise an error:

- **The file is not what was asked for.** It builds and loads, with a state that has no way out, an
  input nothing reads, a pose it snaps to, a loop that pops at its seam, or an angle in degrees.
- **The host wires it wrong.** An input name off by one letter, the wrong state machine, a canvas
  at 0×0. The runtime plays the first animation and stays silent.
- **It works and feels dead.** Everything moves in sync, every pose stops dead, colours swap,
  nothing breathes between actions.

Never type a state machine or input name from memory, and never claim it works without having
rendered and interacted with it.

---

## Make it alive

The method is in [references/living-motion.md](references/living-motion.md) (rossark's motion
method, translated to RML). The rules that matter most:

1. **Never teleport.** A transition into a one-frame pose needs `duration` (ms) and a cubic
   interpolator; colours blend with `KeyFrameColor interpolationType="linear"`; `hold` is the
   default and snaps.
2. **Pivots, and keyed values are absolute.** Animate a node inside a parent placed at the joint,
   so its rest value is `0`. Keying `y` on a node authored at `y="262"` moves it to `0`.
3. **One main action, two or three idle loops, one layer each.** Layers key their own nodes in a
   nested chain (`Ground › Hop › Breath › Lean`), so idle life never stops during the action.
4. **Poses flow, they don't stop.** Key a chain of poses with `flow`, a single move with `track`,
   anything computed (breathing, follow-through by delay, seeded waves) with `bake`:

   ```bash
   python3 scripts/motion_keys.py flow 0:1 9:0.86 15:1.1 44:0.8 52:1.04 76:1   # crouch, stretch, squash, settle
   python3 scripts/motion_keys.py track 0:1 7:0.1 9:0.1 20:1:out               # a blink: 7 / 2 / 11 frames
   python3 scripts/motion_keys.py wave --base 1 --amp 0.016 --period 120 --length 240
   ```
   `flow` and `bake` write exact `cubicValue` Hermite segments, verified against the renderer.
5. **Frequency decides how much.** Controls seen tens of times a day get a fast, small change and
   then rest; characters, rewards and empty states get the life.
6. **The rest pose is the authored pose**, for reduced motion and for hosts that never start the
   machine. One-shots must read on their final frame.

`examples/living-mascot/build.py` is the worked example: tokens at the top, four layers, a gaze
blend driven by the host, a hop acted through poses.

---

## Fast path: start from a recipe

`examples/` holds ready-to-run recipes, each a `rive.yaml`, a `scene.rml` and a compiled `.riv`:

| Component | Directory | Inputs | What it teaches |
|---|---|---|---|
| **Living Mascot** | `examples/living-mascot` | Number `lookX`, Trigger `poke` (and a click listener) | Four layers: breath, blinks, a gaze blend, a hop with squash, stretch and follow-through |
| **Toggle Switch** | `examples/toggle-switch` | Trigger `tap` (click listener) | Pose states with a 240 ms mix; a knob that stretches with its travel on a second layer |
| **Like Button** | `examples/like-heart` | Boolean `liked` | Anticipation, pop and settle in one `flow`; colour blend; seeded spark burst; faster exit |
| **Success Check** | `examples/success-check` | Trigger `fire` (toggles) | In from 0.92 with opacity, check drawn on; a second fire returns to rest |
| **Progress Ring** | `examples/progress-ring` | Number `progress` 0–100 | A `BlendState1DInput` on the value; completion as its own layer |
| **Tab Bar Bell** | `examples/tab-bar-item` | Boolean `active`, Trigger `tap` | Colour and badge on one layer, a hinge swing with a clapper that follows on another |
| **Rating Star** | `examples/rating-star` | Number `rating` | Outline to fill blend, a 72° twist that never rewinds, sparks on rays |
| **Audio Equalizer** | `examples/audio-equalizer` | Boolean `isPlaying` | Five bars on seeded wave pairs, a 320 ms mix to an asymmetric rest |
| **Spinner Loader** | `examples/spinner-loader` | none, mount it while loading | Linear rotation plus a trim chase that closes in three cycles |

```bash
cp -R examples/toggle-switch my-switch     # then edit my-switch/scene.rml
python3 scripts/rml_lint.py my-switch/scene.rml
rive my-switch --verify && rive my-switch --once
```

---

## Toolchain

| Task | Command | Notes |
|---|---|---|
| **Bake motion keys** | `python3 scripts/motion_keys.py flow\|track\|wave …` | Also importable: `bake`, `keyed`, `wave`, `seeded` |
| **Convert SVG to Rive** | `python3 scripts/svg2rml.py logo.svg -o proj/scene.rml` | Paths, circles, rects, gradients, transforms |
| **Convert Lottie to Rive** | `python3 scripts/lottie2rml.py anim.json -o proj/scene.rml` | Detached cubic vertices |
| **Pre-flight RML lint** | `python3 scripts/rml_lint.py proj/scene.rml` | Degrees, colours, dead inputs, snaps, loop seams |
| **Compile and verify** | `rive proj --verify`, `rive inspect proj --json` | Run both; neither is a superset |
| **Inspect and wire a binary** | `python3 scripts/rive_lint.py file.riv -f <platform>` | Exact names and copy-paste wiring for 8 platforms |
| **Record README GIFs** | `node scripts/make-gifs.mjs [hero\|recipes] [--sheet]` | Real runtime, scripted inputs and cursor, 50 fps, seamless loops |

Python scripts use only the standard library.

---

## Authoring: write → lint → verify → render → read

```bash
rive create mascot                               # rive.yaml + scene.rml
python3 scripts/rml_lint.py mascot/scene.rml     # before compiling
rive mascot --verify                             # compiles and re-imports; exit 1 on errors
rive inspect mascot --json | jq .problems        # wiring problems: want []
rive mascot --once                               # mascot/build/mascot.riv
python3 scripts/rive_lint.py mascot/build/mascot.riv --framework react

for n in 1 30 60; do rive mascot --screenshot=mascot/build/f$n.png --advance=$n; done
rive mascot --screenshot=mascot/build/hit.png --pointer=click@120,60 --advance=20
```

Read the PNGs. `--advance=N` shows animation time `N-1`. A loop is at rest on frame 0, so one
screenshot proves nothing: two at different times must differ. A control must look different
after a click and the same again after a second one. Inputs without listeners cannot be driven
from the CLI: record them with `scripts/make-gifs.mjs`, which sets them in the real runtime.

Before writing RML, read `rive docs format` and [references/rml-authoring.md](references/rml-authoring.md).
Before keying any attribute, check `rive schema <Type>`.

**Inputs or view models.** `StateMachineBool/Number/Trigger` are deprecated for new top-level files:
drive those with view model properties (`rive docs data`). Inputs remain right for a component's own
behaviour once it is nested, because a nested artboard does not bind its own view model. The recipes
use inputs because each is a nestable component.

### The rest invariant and the five beats

1. **Rest invariant.** Every layer has an explicit resting state, and every action closes:
   `Rest → Action → Rest`, with `enableExitTime="true"` on the way back, or a pose transition with a
   mix. Nothing latches.
2. **Five beats** for an action: rest, anticipation (a small counter-motion), apex, settle, return.
   Key them as one `flow` channel so the motion never stops between beats.

---

## Universal runtime wiring

```bash
python3 scripts/rive_lint.py public/mascot.riv -f react     # also vue, svelte, web, flutter,
python3 scripts/rive_lint.py public/mascot.riv -f all       # swiftui, android, react-native
```

Full patterns: [references/universal-framework-wiring.md](references/universal-framework-wiring.md).

---

## Common traps

| Symptom | Code | Cause | Fix |
|---|---|---|---|
| **Canvas blank, no error** | `RV012`, `RV001` | Artboard 0×0 (`RV012`), a 404 page or LFS pointer served as `.riv` (`RV001`), or a container with no CSS size (no code: check the layout) | Size the container; run `rive_lint.py` |
| **Draws but never reacts** | `RV005` | No inputs and no listeners, or the host used a wrong name | Copy names from `rive_lint.py` |
| **Host sets an input, nothing moves** | `RML011` | The input is declared but no condition, listener or blend reads it | Wire it, or delete it |
| **Snaps between states** | `RML012` | A transition into a one-frame pose with no `duration` | `duration="160"`–`"300"` plus a cubic interpolator |
| **Pops once per loop** | `RML013` | A `loop` whose last key differs from its first | Close the loop, or `pingPong` |
| **Thrown off the artboard** | — | A keyed `x`/`y` replaces the authored value | Animate a child of a node at the pivot |
| **Reacts once, never returns** | — | The return transition was never authored; no linter sees it | Render two clicks: the second must return to rest |
| **Spins 57 times** | `RML004` | Rotation in degrees, as an attribute or a keyframe value | Radians: a full turn is `6.2831853` |
| **Colour never animates** | `RML008` | `KeyFrameDouble` on `colorValue` (key 37) | `KeyFrameColor` with ARGB hex |
| **Shape invisible** | `RML007` | `<Fill>` without paint, or covered: the first sibling paints on top | Add `<SolidColor>`; reorder |
| **White seam on a closed eye** | — | A catchlight squashed with the lid | Fade it out during the blink |

Full catalog: [references/defect-ledger.md](references/defect-ledger.md).

---

## Finishing checklist

1. `rml_lint.py` reports no errors and no `RML011`–`RML013` warnings you cannot explain.
2. `rive <dir> --verify` exits 0 and `rive inspect <dir> --json` reports `problems: []`.
3. Renders at two times differ; frame 0 is a good drawing; each one-shot reads on its last frame.
4. A second gesture returns the component to rest.
5. Input names in host code came from `rive_lint.py`.
6. The alive checklist in [references/living-motion.md](references/living-motion.md#5-characters)
   and the taste pass in [references/motion-taste.md](references/motion-taste.md) both pass.
7. Report what was rendered and verified, and what was not seen on a real device.
