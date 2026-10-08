<div align="center">

<img src="assets/banner-en.jpg" alt="rive-animator — Interactive vector runtimes that actually react before they ship" width="100%">

Stop fighting silent runtime bugs and blank canvases. A code-first Rive toolkit for AI coding agents and frontend developers: eight verified recipes, zero-dependency SVG-to-RML converter, pre-flight linter for silent traps, and copy-paste runtime wiring across 8 platforms.

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-black)](https://code.claude.com/docs)
[![Antigravity](https://img.shields.io/badge/Antigravity-Skill-black)](https://antigravity.google)
[![Rive](https://img.shields.io/badge/Rive-Format_7.3-black)](https://rive.app)
[![Tests](https://img.shields.io/badge/tests-8_passed-10B981?style=flat-square)](tests/)

English · [Español](README.es.md) · [中文](README.zh-CN.md)

</div>

---

## The Real Problem

Every developer who has tried shipping interactive vector graphics knows the frustration: **a `.riv` is a compiled program, not an image.** 

When motion or interactive state goes wrong in Rive, it almost never throws an error in your browser console:
1. **The Silent Freeze:** The file compiles cleanly and mounts, but the canvas stays at `0×0` because CSS sizing was missing, or an artboard had zero dimensions (`RV012`).
2. **The Name Mismatch Trap:** You wire `mouse_hover` in your React or Flutter component, but the state machine was authored as `mouseHover`. The runtime silently ignores your input and falls back to playing the default loop.
3. **The Degree Disaster:** A rotation keyframe was passed `90` or `180` instead of radians (`1.5708` / `3.1416`). The asset spins at 5,000 RPM into an unrecognizable blur.
4. **The One-Way Latch:** A toggle transitions to `active`, but the return transition was never authored. The component reacts on the first click and latches forever.

`rive-animator` eliminates this entire class of bugs before you touch production code.

---

## Two Ways In

| You have | Use | What it gives you |
|---|---|---|
| **An SVG icon, logo, or brief** | `python3 scripts/svg2rml.py` + Rive CLI | Instant RML scene with detached cubic vertices, shapes, and active state machine |
| **An existing `.riv` binary** | `python3 scripts/rive_lint.py` | Exact runtime state machine names, defect checks (`RV001`–`RV012`), and copy-paste code |

---

## What to ask your AI Assistant

| Say to Claude / Antigravity | What it does |
|---|---|
| *"Build an interactive toggle switch in Rive that feels like physical hardware"* | Starts from `toggle-switch`, sets 240ms cubic ease, authors click listener, verifies with `rive` |
| *"Convert this SVG logo to an interactive Rive artboard"* | Runs `svg2rml.py`, creates artboard and default state machine, validates syntax |
| *"Why does my Rive animation draw but ignore my clicks?"* | Lints with `rive_lint.py`, diagnoses missing inputs or listeners (`RV005`), prints exact wiring |
| *"Give me Flutter / SwiftUI / React wiring for mascot.riv"* | Runs `rive_lint.py mascot.riv -f <platform>` and generates native Dart, Swift, or TypeScript |
| *"Create a circular progress bar driven from 0 to 100"* | Adapts `progress-ring`, binds `progress` Number input to TrimPath, verifies easing |

---

## Shipped Recipes

`examples/` holds eight production-ready, verified recipes with `scene.rml`, `rive.yaml`, and compiled `.riv` binaries:

<table>
<tr>
<td width="25%" align="center" valign="top">
<b>Toggle Switch</b><br>
<code>examples/toggle-switch</code><br>
<sub>Hardware toggle feel, 240ms cubic ease, click listener.<br><b>Input:</b> <code>tap</code> (Trigger)<br><b>Size:</b> 540 B</sub>
</td>
<td width="25%" align="center" valign="top">
<b>Spinner Loader</b><br>
<code>examples/spinner-loader</code><br>
<sub>Circular stroke chase, continuous 60-frame loop.<br><b>Input:</b> <code>speed</code> (Number)<br><b>Size:</b> 374 B</sub>
</td>
<td width="25%" align="center" valign="top">
<b>Success Check</b><br>
<code>examples/success-check</code><br>
<sub>Settling disc with trim-draw checkmark on completion.<br><b>Input:</b> <code>fire</code> (Trigger)<br><b>Size:</b> 584 B</sub>
</td>
<td width="25%" align="center" valign="top">
<b>Like Button</b><br>
<code>examples/like-heart</code><br>
<sub>Micro-burst scale pop (0.8 → 1.25 → 1.0) and fill transition.<br><b>Input:</b> <code>liked</code> (Boolean)<br><b>Size:</b> 666 B</sub>
</td>
</tr>
<tr>
<td width="25%" align="center" valign="top">
<b>Rating Star</b><br>
<code>examples/rating-star</code><br>
<sub>Parametric 5-point star that scales and fills with color.<br><b>Input:</b> <code>rating</code> (Number)<br><b>Size:</b> 506 B</sub>
</td>
<td width="25%" align="center" valign="top">
<b>Progress Ring</b><br>
<code>examples/progress-ring</code><br>
<sub>Circular progress ring driven by numerical percentage.<br><b>Input:</b> <code>progress</code> (Number)<br><b>Size:</b> 399 B</sub>
</td>
<td width="25%" align="center" valign="top">
<b>Audio Equalizer</b><br>
<code>examples/audio-equalizer</code><br>
<sub>3 phase-offset audio bars bouncing upwards.<br><b>Input:</b> <code>isPlaying</code> (Boolean)<br><b>Size:</b> 754 B</sub>
</td>
<td width="25%" align="center" valign="top">
<b>Tab Bar Item</b><br>
<code>examples/tab-bar-item</code><br>
<sub>Dual-layer state machine: active color + spring tap bounce.<br><b>Inputs:</b> <code>active</code>, <code>tap</code><br><b>Size:</b> 635 B</sub>
</td>
</tr>
</table>

---

## Universal Framework Wiring

`scripts/rive_lint.py` automatically generates exact, copy-paste wiring tailored to your target platform:

```bash
python3 scripts/rive_lint.py mascot.riv --framework <platform>
```

Supported platforms:
- **React** (`@rive-app/react-canvas`): Hooks with `useRive` and `useStateMachineInput`.
- **Vue 3** (`@rive-app/canvas`): Composition API with `ref`, `onMounted`, and canvas resize.
- **Svelte** (`@rive-app/canvas`): Reactive canvas binding and lifecycle cleanup.
- **Vanilla Web Canvas** (`@rive-app/canvas`): Direct HTML5 canvas mounting.
- **Flutter** (`rive`): StateMachineController with typed `SMIBool`, `SMINumber`, `SMITrigger`.
- **SwiftUI / iOS** (`RiveRuntime`): Native `RiveViewModel` with state machine bindings.
- **Android Kotlin** (`app.rive:rive-android`): `RiveAnimationView` with typed state setters.
- **React Native** (`@rive-app/react-native`): Mobile canvas ref with touch gesture handlers.

See [references/universal-framework-wiring.md](references/universal-framework-wiring.md) for full examples.

---

## Toolchain Overview

Zero external dependencies. Pure Python 3.8+ standard library.

```
scripts/
├── rive_lint.py     # Binary inspector, defect audit, 8-framework wiring generator
├── rml_lint.py      # Pre-flight XML validator for degrees vs radians, colors, gotchas
├── svg2rml.py       # Direct zero-dependency SVG to RML artboard converter
├── lottie2rml.py    # Lottie JSON to RML converter with detached cubic vertices
├── svgpath.py       # Pure-Python SVG cubic bezier decomposition engine
└── svg2lottie.py    # Internal vector geometry tokenizer
```

---

## Defect Ledger

| Code | Level | Description | Fix |
|---|---|---|---|
| `RV001` | Error | Binary is corrupted, truncated, or invalid header | Re-export file; check git LFS pointer |
| `RV002` | Warning | Format version higher than runtime support | Rebuild with current Rive CLI version |
| `RV003` | Error | No artboard present; canvas stays empty | Author at least one `<Artboard>` |
| `RV004` | Info | Artboard has no state machine; static timeline only | Add `<StateMachine>` so inputs can drive it |
| `RV005` | Info | State machine has no inputs and no listeners | Add inputs or pointer listeners |
| `RV006` | Warning | Duplicate input name or casing collision | Match exact spelling and capitalization |
| `RV007` | Info | Artboard has no default state machine specified | Set `defaultStateMachineId` on Artboard |
| `RV008` | Warning | Embedded font or bitmap exceeds 150 KB | Subset font or load via CDN at runtime |
| `RV009` | Warning | State machine has no layers; can never transition | Add at least one `<StateMachineLayer>` |
| `RV010` | Warning | Timeline animation duration is 0 frames | Author positive frame duration |
| `RV011` | Warning | Input name has leading or trailing whitespace | Trim input names in RML |
| `RV012` | Error | Artboard has dimensions 0×0; renders blank | Set positive width and height on Artboard |
| `RML004` | Warning | Rotation authored in degrees (> 2π) | Use radians (`math.pi`), not degrees |
| `RML007` | Warning | `<Fill>` tag missing paint child | Add `<SolidColor colorValue="..."/>` child |
| `RML008` | Error | `KeyFrameDouble` placed on Color property | Use `KeyFrameColor` for color properties |

---

## Installation

### For Claude Code
```bash
claude plugin add obeskay/rive-animator-skill
```

### For Antigravity
Clone or link into your agent skills directory:
```bash
git clone https://github.com/obeskay/rive-animator-skill.git ~/.gemini/config/skills/rive-animator
```

### Local Testing
```bash
git clone https://github.com/obeskay/rive-animator-skill.git
cd rive-animator-skill
python3 -m unittest discover -s tests -v
```

---

## License

MIT © [ov (obeskay)](https://github.com/obeskay)
