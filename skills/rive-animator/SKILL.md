---
name: rive-animator
description: >-
  Create, inspect, lint, and repair Rive (.riv) files, RML scenes, and State Machines.
  Use when asked to build an interactive vector animation or UI component from a brief or an SVG;
  convert SVG/Lottie to Rive RML; inspect an existing .riv binary (artboards, animations, state machines,
  inputs, listeners, view models); generate copy-paste runtime wiring across React, Vue, Svelte, Web Canvas,
  Flutter, iOS/SwiftUI, Android Kotlin, and React Native; or diagnose a Rive component that renders blank,
  ignores clicks, or fails to transition.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Rive Animator

A `.riv` is a small interactive program, not a static picture: artboards, timelines, and a state machine deciding which timeline plays and when. The failures that cost time never raise an error:

- **The file is not what was asked for.** It builds and loads something — with a state that has no way out, a colour keyed by a double keyframe, an angle entered as degrees instead of radians, or a listener aimed at nothing.
- **The host wires it wrong.** An input name off by one letter, the wrong state machine, or a canvas at 0×0. The runtime plays the first animation and stays silent.

Never type a state machine name or input identifier from memory, and never claim it works without having rendered and interacted with it.

---

## The animation toolbox: pick by the job, combine for the feeling

Top-tier craft separates an app from lifeless AI slop. Never ask for "generic animation" — select the exact technique from the toolbox and layer them together:

| Archetype | Pick When | Role in Composition |
|---|---|---|
| **Keyframes** | Choreographing a fixed timeline sequence | Internal Rive timelines: X/Y travel, scale pop, opacity, colors |
| **Springs** | UI controls need organic responsiveness | Host-level settling, button feedback, sheet dismissals |
| **Gestures** | Direct manipulation follows pointer/touch | Host tracking streamed into Rive `StateMachineNumber` (`tiltX`, `tiltY`) |
| **Physics** | Dynamic forces, collisions, gravity | Bound collisions, ragdoll dynamics, rolling elements |
| **SVG Paths** | Drawing curves, spline travel, morphing | Vector contour deformation, `followPath`, organic background masks |
| **Layout Transitions** | Reordering, expanding, connecting views | Native FLIP / View Transitions when elements shift |
| **Rive / Lottie** | Interactive vector runtime | Stateful characters, triggers, multi-layer inputs, nested artboards |
| **Skeletal Rigs** | Posing connected characters | Hierarchical bone joints, IK/FK character poses |
| **Particles** | Milestone celebrations & bursts | Confetti, starbursts, achievement bursts fired on Rive events |
| **Shaders** | Pixel-level transformations | Glass refractions, liquid warps, dynamic blurs behind surfaces |

> **The Composition Rule**: Real delight comes from layering. Combine a Rive state machine character + an SVG path morphing background mask + 3D parallax depth + host gesture tilt + spring snap landing + particle celebration.
> Full guide: [references/animation-toolbox-cheatsheet.md](references/animation-toolbox-cheatsheet.md).

---

## Fast path: start from a recipe


`examples/` holds ready-to-run interactive recipes. Each has its own `rive.yaml`, `scene.rml`, and compiled `.riv` binary. Starting from the nearest one beats a blank page:

| Component | Directory | Inputs | What it teaches |
|---|---|---|---|
| **Toggle Switch** | `examples/toggle-switch` | Trigger `tap` | Hardware-feel switch with 240 ms cubic ease and click listener |
| **Spinner Loader** | `examples/spinner-loader` | Number `speed` | Indeterminate circular chase with trim path and speed control |
| **Success Check** | `examples/success-check` | Trigger `fire` | Settling disc + trim-draw checkmark on trigger fire |
| **Like Button** | `examples/like-heart` | Boolean `liked` | Cubic scale pop (0.8 → 1.25 → 1.0) and state colour transition |
| **Rating Star** | `examples/rating-star` | Number `rating` | Parametric 5-point Star scaling and filling based on value |
| **Progress Ring** | `examples/progress-ring` | Number `progress` | Circular progress arc driven by 0–100 numerical value |
| **Audio Equalizer** | `examples/audio-equalizer` | Boolean `isPlaying` | 3 phase-offset bars bouncing upwards (`originY="1.0"`) |
| **Tab Bar Icon** | `examples/tab-bar-item` | Boolean `active`, Trigger `tap` | 2-layer state machine: color selection + spring bounce |

```bash
# Copy and adapt an existing recipe
cp -R examples/toggle-switch my-switch
# Edit my-switch/scene.rml, then verify and build
rive my-switch --verify
rive my-switch --once
```

---

## Toolchain overview

| Task | Command | Description |
|---|---|---|
| **Convert SVG to Rive** | `python3 scripts/svg2rml.py logo.svg -o proj/scene.rml` | Zero-dependency direct converter: paths, circles, rects, gradients |
| **Convert Lottie to Rive** | `python3 scripts/lottie2rml.py anim.json -o proj/scene.rml` | Turns Lottie JSON into RML with detached cubic vertices |
| **Pre-flight RML Lint** | `python3 scripts/rml_lint.py proj/scene.rml` | Checks degrees vs radians, missing state machines, color keyframes |
| **Compile & Verify** | `rive proj --verify` | Rive CLI verification: validates syntax and imports |
| **Inspect & Wire Binary** | `python3 scripts/rive_lint.py proj/build/proj.riv` | Deep binary inspection + copy-paste runtime wiring |
| **Multi-Framework Wiring** | `python3 scripts/rive_lint.py file.riv -f <platform>` | Generates code for React, Vue, Svelte, Web, Flutter, SwiftUI, Android, RN |
| **Record Interactive GIFs** | `node scripts/make-gifs.mjs [name]` | Headless Puppeteer + Rive canvas-advanced scripted session recording |

---

## Authoring: write → verify → inspect → screenshot → look

```bash
rive create mascot                           # creates rive.yaml + scene.rml
python3 scripts/rml_lint.py mascot/scene.rml # pre-flight check before compilation
rive mascot --verify                         # compiles and re-imports; exit 1 on errors
rive mascot --once                           # builds mascot/build/mascot.riv
python3 scripts/rive_lint.py mascot/build/mascot.riv --framework react

# Visual verification: screenshots at different states must differ
mkdir -p mascot/build
rive mascot --screenshot=mascot/build/f1.png  --advance=1
rive mascot --screenshot=mascot/build/f30.png --advance=30
rive mascot --screenshot=mascot/build/on.png  --pointer=click@120,60 --advance=20
```

Read the PNGs. A loop is at rest on frame 0, so one screenshot proves nothing: two at different times must differ. A control must look different after a click and the same again after a second one.

Before writing RML, read `rive docs format` and `references/rml-authoring.md`. Before keying any attribute, check `rive schema <Type>`.

### The 5-beat choreography & rest invariant

When authoring actions for characters or controls:
1. **Rest Invariant**: Every state machine must have an explicit Resting state. Actions must be closed loops (`Rest -> Action -> Rest`) using `enableExitTime="true"` so they never latch.
2. **5-Beat Choreography**:
   - **Beat 1 (Rest)**: Settled baseline pose.
   - **Beat 2 (Anticipation)**: Subtle recoil or counter-motion before the action.
   - **Beat 3 (Apex)**: Peak displacement and expression.
   - **Beat 4 (Settle)**: Secondary overshoot / dampening.
   - **Beat 5 (Return)**: Smooth resolution back to Rest.
3. **Visual Edge-Case Audit**: Inspect captures for artboard clipping, jagged vector tangents, latching states, and abrupt non-eased transitions.

---


## Starting from an SVG

Convert any SVG icon, logo, or illustration into an interactive Rive project in one command:

```bash
# 1. Convert SVG directly to RML scene
python3 scripts/svg2rml.py logo.svg --size 200 --name "Logo" -o rive-logo/scene.rml
printf 'name: rive-logo\n' > rive-logo/rive.yaml

# 2. Verify and build
rive rive-logo --verify && rive rive-logo --once

# 3. Inspect binary and get copy-paste wiring
python3 scripts/rive_lint.py rive-logo/build/rive-logo.riv
```

`svg2rml.py` converts SVG paths, rects, circles, ellipses, lines, polylines, polygons, groups, transforms, fills, and strokes into RML `<Shape>`, `<PointsPath>`, `<CubicDetachedVertex>`, `<Fill>`, and `<Stroke>`. The output includes an active placeholder timeline and a default state machine so it is alive on load.

---

## Universal runtime wiring

Pass `-f / --framework` to `scripts/rive_lint.py` to get exact copy-paste integration:

```bash
python3 scripts/rive_lint.py public/mascot.riv -f react
python3 scripts/rive_lint.py public/mascot.riv -f flutter
python3 scripts/rive_lint.py public/mascot.riv -f swiftui
python3 scripts/rive_lint.py public/mascot.riv -f vue
python3 scripts/rive_lint.py public/mascot.riv -f svelte
python3 scripts/rive_lint.py public/mascot.riv -f all
```

Supported frameworks:
- `react`: `@rive-app/react-canvas`
- `vue`: `@rive-app/canvas` with Vue 3 `ref` and `onMounted`
- `svelte`: `@rive-app/canvas` with Svelte `onMount`
- `web`: Vanilla HTML5 canvas with `@rive-app/canvas`
- `flutter`: `rive` package with `StateMachineController`
- `swiftui`: `RiveRuntime` iOS/macOS with `RiveViewModel`
- `android`: `app.rive:rive-android` with `RiveAnimationView`
- `react-native`: `@rive-app/react-native`
- `all`: Prints copy-paste snippets for all frameworks side by side

Full patterns and examples: [references/universal-framework-wiring.md](references/universal-framework-wiring.md).

---

## Common traps and defects

| Symptom | Code | Cause | Fix |
|---|---|---|---|
| **Canvas blank, no error** | `RV012` | Container CSS is 0×0; or Artboard width/height is 0; or URL returned 404 HTML | Set positive CSS size on container; check `rive_lint.py` |
| **Draws but never reacts** | `RV005` | State machine has no inputs and no listeners; or host used wrong input name | Copy exact strings from `rive_lint.py`; check state machine layers |
| **Reacts once, never returns** | `RV009` | Return transition was never authored (one-way trap) | Two clicks or state flip must return component to rest |
| **Spins 57 times / crazy speed** | `RML004` | Rotation keyed in **degrees** instead of **radians** | Rive expects radians: 360° is `6.2831853` rad (`2 * math.pi`) |
| **Colour never animates** | `RML008` | `KeyFrameDouble` placed on a Color property | Use `KeyFrameColor` with ARGB hex value (e.g. `FFEF4444`) |
| **Shape invisible** | `RML007` | `<Fill>` declared without `<SolidColor>` or gradient child; or covered by opaque sibling | Add `<SolidColor colorValue="..."/>`; declared first draws on top |
| **Blurry on Retina/HiDPI** | - | Canvas drawn at 1× DPR | Web: `r.resizeDrawingSurfaceToCanvas()`; React handles automatically |

Full defect catalog with remedies: [references/defect-ledger.md](references/defect-ledger.md).

---

## Finishing checklist

Before declaring an animation finished:

1. `python3 scripts/rml_lint.py <scene.rml>` reports no errors.
2. `rive <dir> --verify` exits with code 0 and 0 warnings.
3. Screenshots at two distinct timestamps differ (proves motion is alive).
4. After-again gesture matches rest state (proves interactive state machine doesn't latch).
5. All input names in host code came directly from `rive_lint.py`, never from memory.
6. The taste pass in [references/motion-taste.md](references/motion-taste.md) was checked: zero overshoot on UI switches, natural easing, one hero property, restrained palette.
7. Report what was rendered and verified.
