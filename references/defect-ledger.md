# Defect ledger

## At runtime

| Symptom | Root cause | Remedy |
|---|---|---|
| Canvas blank, no console error | Container is 0×0 (flex/grid child with no height) | Give the parent `h-64`, `aspect-square` or an explicit height; the canvas follows it |
| "Problem loading file; may be corrupt!" | `src` returned something that is not a `.riv` — usually an HTML 404 or an LFS pointer; or a truncated upload | Fetch the URL in the browser; `python3 scripts/rive_lint.py file.riv` reports `RV001` on a bad file |
| Draws, but never reacts to inputs | State machine or input name does not match the file; or the file has no default machine and the runtime fell back to the first animation | Copy names from `rive_lint.py`; pass `stateMachines:` explicitly |
| Draws, never reacts to hover or click | The machine has no listeners (rive_lint: `0 listeners`) and the host does not set the input; or the listener targets nothing / the artboard itself | Set the input from the host, or in RML give the artboard a background shape and target it |
| Reacts once, then never again | The return transition was never authored | Author both directions; two clicks must return to rest (`--pointer=click` twice) |
| Reacts to the wrong thing, or only in part of the button | Every listener under the pointer fires; stacked targets fight | Move suspect targets off-artboard to find the culprit; `isTargetOpaque` on the blocker |
| Plays once and stops | `loopValue` defaults to `oneShot` | `loopValue="loop"` (or `pingPong`) |
| Plays like a slideshow | `interpolationType` defaults to `hold` | Set it on every keyframe but the last |
| Spins wildly | Rotation authored in degrees | Radians: `6.2831855` per turn |
| Colour, boolean or id never animates | Keyframe element does not match the property type | `KeyFrameColor`, `KeyFrameBool`, `KeyFrameId` (hold) |
| Bound data never arrives | No default state machine; dangling `sourcePathIds`; bind on the wrong element (`width` is on `Rectangle`, not `Shape`); nested artboard inherits the parent's data context | `inspect` `problems`; literal probe (`text="LITERAL-HERE"`); inputs for component-internal machines |
| Shape invisible | Declared after the sibling covering it (first declared is on top); `Fill` without a paint child; `Feather` inside a `Fill`; `hidden="true"` (editor-only, does nothing) | Reorder; add `SolidColor`; feather the stroke; remove the paint or move it off-artboard |
| Blurry on Retina / 4K | Drawing surface at 1× | react-canvas: give the container CSS size; plain runtime: `resizeDrawingSurfaceToCanvas()` on load and on resize |
| Content clipped at the edges | Artboard smaller than its own motion, or `Fit.Cover` | Grow the artboard; `Fit.Contain` |
| Memory grows on route changes | Instances created in effects without `cleanup()` | Use the hook, or `rive.cleanup()` in the effect's return |
| Screenshot shows the rest pose, not the animation | `--screenshot` with no `--advance` captures frame 0 before the machine ran | `--advance=1` at least; compare frames at two times |
| Text renders as nothing | Font asset file missing on disk; `TextValueRun` without `styleId`; `TextStylePaint` without a `Fill` | `grep 'file="' *.rml` and check the disk; `rive docs text` |

## `rive_lint.py` codes

The linter reads the binary. Its codes are file-level; the table above is what you see
in a browser.

| Code | Severity | Meaning |
|---|---|---|
| `RV001` | error | Not a Rive file, truncated, or a property key neither the runtime nor the file's table of contents can type. The runtime would refuse it. |
| `RV002` | warn | Format major version is not 7. Re-export. |
| `RV003` | error | No artboard. Nothing can be displayed (a script-only test project builds this way). |
| `RV004` | info | Artboard has no state machine: it can play timelines (`animations:`) but cannot react. |
| `RV005` | info | State machine has no inputs and no listeners: it runs on its own; nothing the host sets changes it. |
| `RV006` | warn | Two inputs in one machine differ only by case or spacing, or are duplicates. `useStateMachineInput` matches the exact string. |
| `RV007` | info | Artboard has state machines but no default. Name the machine explicitly in the host. |
| `RV008` | warn | An embedded font or image over 150 KB, or a file over 1 MB that is mostly vectors. |
| `RV009` | warn | State machine with no layers. |
| `RV010` | warn | Animation with zero duration. |
| `RV011` | warn | Input name has leading or trailing whitespace. |

## `rive inspect` problem kinds worth knowing

`syntax`, `unresolved-bind-path`, `bind-target-missing-property`,
`incompatible-bind-types`, `missing-reference`, `no-default-state-machine`,
`no-artboards`, `paint-without-shape-paint`, `states-overlap`, `artboards-overlap`,
`artboard-without-style`, `draw-target-not-child-of-rules`. Not checked: an id that is
set but points at nothing (`stateToId`, `animationId`, `inputId`), a missing asset file,
a keyframe of the wrong type, anything about appearance, anything in a `.luau` script.
`problems: []` means nothing on the checked list is wrong — not that the file is right.
