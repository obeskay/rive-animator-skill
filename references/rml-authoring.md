# RML: the working subset

`rive docs format` is the reference; `rive schema <Type>` is the truth about any
property (type, default, accepted enum names, property key). This page is the part you
use every time, and the part that builds clean while being wrong. Read any topic with
`rive docs <topic>`: `format`, `skeleton`, `workflow`, `gotchas`, `drawing`,
`transforms`, `easing`, `state-machines`, `data`, `layout`, `text`, `rigging`.

## The skeleton

The smallest scene that moves on its own (`rive docs skeleton`):

```xml
<Rive version="1" kind="fragment">
    <Artboard defaultStateMachineId="0:7" width="500" height="500" name="Artboard" id="0:2">
        <Fill name="Background">
            <SolidColor colorValue="FF1D1D1D" name="Color"/>
        </Fill>

        <Shape x="250" y="250" name="Triangle" id="0:14">
            <Triangle originX="0.5" originY="0.5" width="220" height="200" name="Path"/>
            <Fill name="Fill">
                <SolidColor colorValue="FF57A5E0" name="Color"/>
            </Fill>
        </Shape>

        <StateMachine name="State Machine 1" id="0:7">
            <StateMachineLayer name="Layer 1" id="0:8">
                <AnyState x="200" y="-120"/>
                <ExitState x="400" y="-120"/>
                <EntryState>
                    <StateTransition stateToId="0:12"/>
                </EntryState>
                <AnimationState x="200" animationId="0:6" id="0:12"/>
            </StateMachineLayer>
        </StateMachine>

        <LinearAnimation loopValue="loop" duration="120" name="Spin" id="0:6">
            <KeyedObject objectId="0:14">
                <KeyedProperty propertyKey="15">
                    <KeyFrameDouble value="0" interpolationType="linear"/>
                    <KeyFrameDouble value="6.2831855" interpolationType="linear" frame="120"/>
                </KeyedProperty>
            </KeyedObject>
        </LinearAnimation>
    </Artboard>
</Rive>
```

Every line is load-bearing:

- `defaultStateMachineId` — without it the artboard draws and plays the first timeline,
  but receives no pointer input and applies no data binds. Half alive.
- `Shape` holds position and transform; the geometry child holds size; `Fill` needs a
  `SolidColor` or gradient child or it draws nothing.
- `AnyState`, `ExitState`, `EntryState` — all three on every layer, even unused, or the
  layer does not import. The `EntryState` transition is what starts anything.
- `KeyedObject.objectId` is one of the few references written by hand: animations live
  beside the objects they animate.
- `rive.yaml` needs only `name:`. `main:` picks the default artboard when there are
  several.

## The keys you will actually key

| Property | key | Unit / keyframe |
|---|---|---|
| `x`, `y` | 13, 14 | artboard units, `KeyFrameDouble` |
| `rotation` | 15 | **radians** (full turn `6.2831855`) |
| `scaleX`, `scaleY` | 16, 17 | factor, `1` is 100% |
| `opacity` | 18 | `0`–`1`, multiplies down the tree |
| `SolidColor.colorValue` | 37 | `KeyFrameColor`, ARGB hex |
| `Solo.activeComponentId` | 296 | `KeyFrameId`, `hold` only |

For anything else: `rive schema Rectangle --animatable`. Never guess a key.

## Keyframes

```xml
<KeyedProperty propertyKey="13">
    <KeyFrameDouble value="0" frame="0" interpolationType="cubic">
        <CubicEaseInterpolator x1="0.42" y1="0" x2="0.58" y2="1"/>
    </KeyFrameDouble>
    <KeyFrameDouble value="100" frame="60" interpolationType="linear"/>
</KeyedProperty>
```

- The ease on a keyframe shapes the segment **leaving** it. The last keyframe's
  interpolation is never read.
- `interpolationType` defaults to `hold`. A keyframe without it snaps — the usual
  reason a timeline plays like a slideshow.
- `cubic` needs a nested `CubicEaseInterpolator` (the four CSS `cubic-bezier()`
  numbers); without one it builds clean and eases nothing. `elastic` needs an
  `ElasticInterpolator`. `cubicValue` shapes the value, not the time.
- The keyframe element must match the property type: `KeyFrameDouble` for `double`,
  `KeyFrameColor` for `Color`, `KeyFrameBool`, `KeyFrameUint` (enums), `KeyFrameString`,
  `KeyFrameId`. A mismatch builds clean and never writes the value.
- `LinearAnimation`: `fps` (default 60) and `duration` in **frames**; `loopValue`
  defaults to `oneShot` — write `loop` or `pingPong`. A `loop` pops unless the last
  frame holds the first frame's value; `pingPong` is seamless by construction.
- `StateTransition.duration` is **milliseconds**, and `exitTimeIsPercetange` is
  misspelled in the format itself — write the typo.

## Values

- Colours: ARGB hex, no `#`. `FFFF5A3C` is opaque orange.
- Booleans `"true"`/`"false"`; enums by name (checked — a typo lists the accepted
  values); rotation radians.
- Ids are `client:object` pairs (`0:12`), unique across the whole document. Elements
  nothing references need none; the build writes ids back into your `.rml` on the first
  run, which is a large diff worth its own commit.
- Nesting sets references: a `Component` inside a container gets `parentId`, a
  `KeyedObject` inside an animation gets `animationId`, a `StateTransition` inside a
  state gets `stateFromId`, an interpolator inside a keyframe sets the keyframe's
  `interpolatorId`. `rive docs format` has the two tables.

## Draw order and transforms

- **The first sibling declared paints on top** — the opposite of HTML and SVG. A shape
  you cannot see is almost always behind one declared earlier.
- Within one shape, paints go the other way: the last `Fill`/`Stroke` declared is on top.
- `Node` is the group: rotate it and its children swing around its origin. Wrap a shape
  in a `Node` placed at the pivot rather than offsetting the shape.
- `originX`/`originY` are normalised (`0.5` centres). Setting them on the artboard
  shifts the whole coordinate space; leave the artboard's at `0`.
- Custom geometry is a `PointsPath` of `StraightVertex` (with optional `radius`),
  `CubicMirroredVertex` (`rotation`/`distance`), `CubicDetachedVertex`
  (`inRotation`/`inDistance`/`outRotation`/`outDistance`) or `CubicAsymmetricVertex`.
  Close it with `isClosed="true"`. `lottie2rml.py` writes these; do not hand-type them.

## Builds clean, still wrong

Everything here passes `--verify`. Most also pass `inspect`.

1. Artboard without `defaultStateMachineId`: no input, no data binds.
2. `EntryState` with no `StateTransition`: the machine starts nowhere.
3. A state with no way back: the control works exactly once. Author both directions.
4. Keyframe without `interpolationType`: hold. Animation without `loopValue`: once.
5. `cubic` without an interpolator child: no ease.
6. Wrong keyframe element for the property type: the value is never written.
7. Rotation in degrees: spins fifty-seven times.
8. `Fill` with no paint child; `Feather` inside a `Fill` (renders nothing; feather
   strokes, or use a radial gradient with a transparent outer stop).
9. Listener with no `targetId`, or targeting the artboard: pointer input is not offered
   on the artboard itself — give it a background shape and target that. A transparent
   fill is still hit-testable; every listener under the pointer fires unless something
   on top is `isTargetOpaque`.
10. `NestedArtboard` pointing at an artboard that is not `isComponent="true"` with a
    `ComponentAsset` entry: malformed, and nothing reports it.
11. States and artboards all at `x="0" y="0"`: fine at runtime, a stacked mess in the
    editor. Space them out.
12. `--screenshot` with no `--advance` captures the rest pose, not the animation's first
    frame. Preview from `--advance=1`.
13. View model and property names are validated only by the editor: `camelCase`, no
    spaces, not a Luau keyword (`type`, `end`, `function`…).
14. `nameBased="true"` on a bind: builds clean, resolves nothing here. Bind paths you
    author are absolute (`sourcePathIds="0:40-0:45"`).
15. A missing asset file (`file="Font.ttf"`): nothing reports it; the text renders as
    nothing.

## Checks worth running

```bash
rive inspect . --json | jq .problems                                   # must be []
rive inspect . --json | jq '[..|objects|select(.type=="KeyedProperty")|.propertyKey]'   # what is animated
rive inspect . --json | jq '[..|objects|select((.type//"")=="StateTransition")|{to:.stateToId,duration}]'
rive inspect . --json | jq '{
  machines:  [..|objects|select((.type//"")=="StateMachine")]|length,
  layers:    [..|objects|select((.type//"")=="StateMachineLayer")]|length,
  inputs:    [..|objects|select((.type//"")|test("^StateMachine(Bool|Number|Trigger)$"))]|length,
  listeners: [..|objects|select((.type//"")|startswith("StateMachineListener"))]|length}'
rive inspect . --json | jq '[..|objects|select((.type//"")|startswith("KeyFrame"))
  |select(.enums.interpolationType=="cubic")
  |select(([.children[]?|select((.type//"")|test("Interpolator$"))]|length)==0)|{frame,type}]'   # cubic without a curve: want []
grep -Eoh '<(AnyState|ExitState|EntryState|AnimationState)[^>]*' *.rml | grep -v 'x="'      # states at the origin
```

An object count that goes down between passes means an edit truncated the tree:
`rive inspect . --json | jq '[..|objects]|length'`.
