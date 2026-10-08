<div align="center">

# Rive Animator

**Interactive vector runtimes that actually react before they ship.**

A code-first Rive toolkit and AI agent skill. Eight production-ready recipes, a zero-dependency SVG-to-RML converter, a pre-flight linter for the defects that fail silently, deep binary inspection, and copy-paste runtime wiring across 8 platforms.

[![Rive](https://img.shields.io/badge/Rive-Format_7.3-000000?style=flat-square&logo=rive&logoColor=white)](https://rive.app)
[![Tests](https://img.shields.io/badge/tests-8_passed-10B981?style=flat-square)](tests/)
[![Python](https://img.shields.io/badge/python-3.8+-3B82F6?style=flat-square&logo=python&logoColor=white)](scripts/)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-8B5CF6?style=flat-square)](#zero-dependencies)
[![Platforms](https://img.shields.io/badge/runtimes-8_frameworks-EC4899?style=flat-square)](#universal-framework-wiring)
[![License](https://img.shields.io/badge/license-MIT-6B7280?style=flat-square)](LICENSE)

[Why](#why) · [Recipes](#recipes) · [What to ask for](#what-to-ask-for) · [Universal Wiring](#universal-framework-wiring) · [Toolchain](#toolchain) · [Install](#install)

</div>

---

## Why

A `.riv` is a small interactive program, not a static image: artboards, timelines, and a state machine deciding which timeline plays and when.

The failures that cost hours never throw an error:

1. **The file is not what was asked for.** It builds and draws something — with a state that has no return transition, a colour keyed by a `KeyFrameDouble`, an angle keyed in degrees (`90`) instead of radians (`1.5708`), or a listener pointing to nothing.
2. **The host wires it wrong.** An input name off by one letter (`mouse_hover` vs `mouseHover`), the wrong state machine name, or a canvas container at `0×0`. The runtime plays the default timeline and says nothing.

This skill fixes both. The tools catch the silent traps before compilation, inspect binaries directly from disk, and generate exact, verified copy-paste wiring for your framework of choice.

---

## What to ask for

| Say to Claude / Antigravity | What it does |
|---|---|
| *"Build an interactive toggle switch in Rive that feels like physical hardware"* | Starts from `toggle-switch`, keys zero-overshoot cubic easing, authors click listener, verifies with `rive` |
| *"Convert this SVG icon into an interactive Rive artboard"* | Runs `svg2rml.py`, creates artboard and default state machine, generates preview screenshot |
| *"Why does this .riv file render but ignore my clicks?"* | Lints with `rive_lint.py`, diagnoses missing inputs or listeners (`RV005`), prints exact wiring |
| *"Generate Flutter and SwiftUI wiring for mascot.riv"* | Runs `rive_lint.py mascot.riv -f all` and prints native Swift and Dart controllers |
| *"A circular progress bar driven from 0 to 100"* | Adapts `progress-ring`, binds `progress` Number input to TrimPath, verifies easing |

---

## Recipes

`examples/` provides eight tested, verified recipes with `scene.rml`, `rive.yaml`, and compiled `.riv` binaries:

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

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│   React          Vue 3          Svelte         Web Canvas              │
│   Flutter        SwiftUI (iOS)  Android Kotlin React Native            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### React (`@rive-app/react-canvas`)
```tsx
import { useRive, useStateMachineInput } from '@rive-app/react-canvas';

const { rive, RiveComponent } = useRive({
  src: '/toggle-switch.riv',
  stateMachines: 'State Machine 1',
  autoplay: true,
});
const tap = useStateMachineInput(rive, 'State Machine 1', 'tap');
// tap.fire();
```

### Flutter (`rive`)
```dart
import 'package:rive/rive.dart';

SMITrigger? _tap;
void _onRiveInit(Artboard artboard) {
  final controller = StateMachineController.fromArtboard(artboard, 'State Machine 1');
  if (controller != null) {
    artboard.addController(controller);
    _tap = controller.findInput('tap') as SMITrigger?;
  }
}
// RiveAnimation.asset('assets/toggle-switch.riv', onInit: _onRiveInit)
```

### SwiftUI / iOS (`RiveRuntime`)
```swift
import SwiftUI
import RiveRuntime

@StateObject private var rive = RiveViewModel(
    fileName: "toggle-switch",
    stateMachineName: "State Machine 1",
    autoPlay: true
)
// In Body: rive.view().frame(width: 240, height: 160)
// rive.triggerInput("tap")
```

See [references/universal-framework-wiring.md](references/universal-framework-wiring.md) for Vue 3, Svelte, Vanilla Web, Android Kotlin, and React Native.

---

## Toolchain

Zero external dependencies. Pure Python 3.8+ standard library.

### 1. SVG to RML Converter (`scripts/svg2rml.py`)
Converts any SVG into an RML scene with detached cubic vertices, parametric shapes, fills, strokes, and a default state machine:
```bash
python3 scripts/svg2rml.py logo.svg --size 240 -o my-icon/scene.rml
```

### 2. Pre-flight RML Linter (`scripts/rml_lint.py`)
Catches errors in milliseconds before compiling with `rive`:
- Detects rotation values authored in degrees (> 2π) instead of radians
- Catches `KeyFrameDouble` placed on Color properties
- Identifies empty `<Fill>` tags lacking paint children
- Warns on missing `defaultStateMachineId`
```bash
python3 scripts/rml_lint.py scene.rml
```

### 3. Binary Inspector & Linter (`scripts/rive_lint.py`)
Reads runtime `.riv` binaries using the exact registry decoding rules of `rive-runtime`:
```bash
python3 scripts/rive_lint.py public/mascot.riv
python3 scripts/rive_lint.py public/mascot.riv --json
python3 scripts/rive_lint.py public/mascot.riv --framework all
```

---

## Defect Ledger

| Code | Level | Description |
|---|---|---|
| `RV001` | Error | Binary is corrupted, truncated, or invalid Rive header |
| `RV002` | Warning | Format version higher than runtime support |
| `RV003` | Error | No artboard present; canvas stays empty |
| `RV004` | Info | Artboard has no state machine; only plays static timelines |
| `RV005` | Info | State machine has no inputs and no listeners; cannot react |
| `RV006` | Warning | Duplicate input name or inputs differing only by casing/spacing |
| `RV007` | Info | Artboard has no default state machine specified |
| `RV008` | Warning | Embedded font or bitmap exceeds 150 KB |
| `RV009` | Warning | State machine has no layers; can never transition |
| `RV010` | Warning | Timeline animation duration is 0 frames |
| `RV011` | Warning | Input name has leading or trailing whitespace |
| `RV012` | Error | Artboard has dimensions 0×0; will render blank or clipped |

---

## Install

### For Claude Code
```bash
claude plugin add obeskay/rive-animator-skill
```

### For Antigravity
Clone or link into your agent skills directory:
```bash
git clone https://github.com/obeskay/rive-animator-skill.git ~/.gemini/config/skills/rive-animator
```

### Manual Usage
Clone the repo and use the Python tools anywhere:
```bash
git clone https://github.com/obeskay/rive-animator-skill.git
cd rive-animator-skill
python3 -m unittest discover -s tests -v
```

---

## License

MIT © [ov (obeskay)](https://github.com/obeskay)
