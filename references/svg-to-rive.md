# SVG to Rive

Two routes. The scripted one is reproducible and leaves an RML file you can animate in
text; the editor one gives you bones, meshes and a designer-friendly file.

## Route 1: svg2lottie → lottie2rml → rive

```bash
python3 ~/.claude/skills/lottie-animator/scripts/svg2lottie.py mascot.svg -o build/mascot.json --size 512
python3 scripts/lottie2rml.py build/mascot.json -o rive-mascot/scene.rml
printf 'name: rive-mascot\n' > rive-mascot/rive.yaml
rive rive-mascot --verify
rive inspect rive-mascot --json | jq .problems
mkdir -p rive-mascot/build && rive rive-mascot --screenshot=rive-mascot/build/still.png
```

Then Read the PNG next to the SVG. Verified on the lottie-animator repository's
`logo.svg` (gradient fill + stroke) and `rocket-icon.svg` (four stroked paths): the
Rive screenshot matches the Lottie render.

What comes out:

| Lottie | RML |
|---|---|
| shape layer | `<Node x y rotation scaleX scaleY opacity>` — the layer's anchor is subtracted from everything inside, so the node's origin is the pivot |
| group with paths | `<Shape>` with the group's transform |
| group holding groups | `<Node>` holding child Shapes, in the same order (first on top, same as Lottie) |
| path `sh` | `<PointsPath isClosed>` of `StraightVertex` / `CubicDetachedVertex` (handle angle and length from the Lottie tangents) |
| `rc`, `el`, `sr` | `Rectangle` (with `cornerRadiusTL`), `Ellipse`, `Star` / `Polygon`, all `originX/Y="0.5"` |
| `fl`, `st` | `Fill` / `Stroke` with `SolidColor` (`colorValue` ARGB, opacity folded into alpha; `fillRule`, `cap`, `join`, `thickness`) |
| `gf`, `gs` | `LinearGradient` / `RadialGradient` with `GradientStop`s, in shape-local space |
| `tm` | `TrimPath` inside each `Stroke` (`start`/`end` as fractions, `offset` from degrees) |
| `rd` | `radius` on straight vertices, `cornerRadiusTL` on rectangles |
| layer `parent` | nesting — the child Node inside the parent Node |
| animated property | its first keyframe, and a warning naming the path |
| `rp`, `mm`, `op`, dashes, precomps, images, text, masks | not converted; a warning each |

Every Shape and Node gets an `id="0:N"`, so animating a converted shape is one
`KeyedObject`:

```xml
<LinearAnimation loopValue="loop" duration="120" name="Bob" id="0:90">
    <KeyedObject objectId="0:4">                       <!-- the Shape's id from scene.rml -->
        <KeyedProperty propertyKey="14">               <!-- y -->
            <KeyFrameDouble value="0"   frame="0"   interpolationType="cubic">
                <CubicEaseInterpolator x1="0.42" y1="0" x2="0.58" y2="1"/>
            </KeyFrameDouble>
            <KeyFrameDouble value="-12" frame="60"  interpolationType="cubic">
                <CubicEaseInterpolator x1="0.42" y1="0" x2="0.58" y2="1"/>
            </KeyFrameDouble>
            <KeyFrameDouble value="0"   frame="120" interpolationType="linear"/>
        </KeyedProperty>
    </KeyedObject>
</LinearAnimation>
```

Point the placeholder `AnimationState` at it (or add a state) and rebuild. Keyed values
are relative to the converted transform, so `y="0"` is where the shape already sits.

Before converting, flatten what the pipeline warns about in the source: expand `<use>`,
outline text, apply `clipPath`/`mask` by editing the art. `svg2lottie.py` reports each.

Hygiene that pays off later: name the SVG groups (`head`, `eye_l`, `arm_r`) — the
names travel through both tools and become the Node and Shape names you animate by.
Put a pivot where a designer would (a shoulder, a base) by grouping the part so its
group centre lands there; the layer's anchor becomes the Node origin.

## Route 2: the editor

The Rive editor imports SVG directly, keeps the groups as nodes, and is the only place
to add **bones, meshes and skinning** for organic deformation (`rive docs rigging`
covers the RML side once the rig exists). A free personal account exports `.riv`. From
there, `rive create demo --from-rev=demo.rev` turns an editor save into a project, so a
file rigged in the editor can still be finished in RML — and `rive_lint.py` reads the
exported `.riv` either way.

## Weight

A `.riv` is a compact binary; a converted icon is a few hundred bytes to a few KB. What
makes files heavy is embedded fonts (800 KB for a full Inter) and bitmaps.
`rive_lint.py` lists both with sizes (`RV008`); keep art vector, subset fonts, and host
large images on the Rive CDN.
