# The Animation Toolbox & Decision Matrix

> "Pick by the job. Combine for the feeling."
> — John Kim (Meta Senior Staff Engineer)

Functionality gets an app working; **taste, craft, and delight** are what separate high-tier software from generic AI slop. When steering an AI assistant or designing motion, never just say *"add animations"*. Pick the exact archetype for the job, and layer techniques together to create depth.

---

## 1. The 11 Animation Archetypes

| Archetype | Best For | When to Pick | Tradeoffs & Limits |
|---|---|---|---|
| **1. Keyframes** | Choreograph a sequence | Precise timeline control: X/Y travel, scale pop, opacity fades, color shifts across 0s–2.4s. | Rigid timing; does not naturally adapt if interrupted midway unless blended. |
| **2. Springs** | Make UI feel responsive | Buttons, toggles, sheet settling, modals. Natural deceleration with mass, stiffness, and damping. | Harder to choreograph multi-step timelines; best for point A → point B. |
| **3. Gestures** | Follow a finger or scroll | Drag-and-drop, swipe-to-dismiss, carousel scrubbing, pull-to-refresh. | Requires continuous input updates (pointer/touch/gyroscope) at 60/120 FPS. |
| **4. Physics** | Let forces drive motion | Dynamic gravity, momentum, collisions, gyroscope tilt (e.g. ball rolling inside bounds). | Non-deterministic; computational overhead; requires boundary and collision tuning. |
| **5. SVG Paths** | Draw, morph, follow a line | Dynamic vector contours, organic shape morphing, line-drawing along a spline. | Morphing requires matching vertex counts or smooth Bézier interpolation. |
| **6. Layout Transitions** | Reorder, expand, connect | Grid-to-list reordering, card expansion, item insertion (FLIP / View Transitions). | Native platform support (CSS `view-transition`, SwiftUI `matchedGeometryEffect`). |
| **7. Rive / Lottie** | Embed interactive vector motion | **Rive:** State machines, real-time inputs, nested artboards, procedural rigging.<br>**Lottie:** Baked After Effects vector playback. | Rive files are tiny (<1 KB compiled), but state transitions must be authored cleanly. |
| **8. Skeletal Rigs** | Pose a connected character | Characters with bones, hierarchical limbs, ragdoll physics, Inverse Kinematics (IK). | Higher authoring complexity; overkill for simple icon or control UI. |
| **9. Flipbook / Video** | Play finished frames | Hand-drawn frame-by-frame animation, complex 3D renders, realistic textures. | High file weight; immutable at runtime (cannot dynamically change colors or paths). |
| **10. Particles** | Celebrate with many pieces | Confetti bursts, starbursts, coin explosions, landing debris on achievement or snap. | Usually transient; do not collide with UI elements unless linked to a physics engine. |
| **11. Shaders** | Transform the pixels | GPU-driven effects: glassy refractions, organic liquid warps, dynamic blur, caustic light. | Requires GPU pipeline (GLSL / Metal / WGSL); high authoring barrier. |

---

## 2. The Core Principle: Layered Composition ("Combine for the Feeling")

The secret of top-tier apps (like Apple or Meta) is that **no animation technique operates in isolation**. Top craft comes from layering 3 to 4 techniques simultaneously:

### Recipe A: The Cozy Hero Landing (e.g. Puzzle Game Hero)
1. **Rive Character State Machine**: Idle breathing loop + expressive eye blinks + contextual prop animation (drinking coffee).
2. **SVG Path Morphing Mask**: Organic, slowly undulating vector background mask behind characters.
3. **Parallax Depth Layering**: Foreground characters + background elements layered with Z-depth and subtle scale contrast.
4. **Native Gesture / Tilt Sway**: Host platform (SwiftUI / CSS) applies subtle angular tilt to characters based on device gyroscope or cursor position.

### Recipe B: The Tactile Snapping Interaction (e.g. Puzzle Piece Drop / Like Button)
1. **Gesture Drag (Host)**: 1:1 finger tracking during drag.
2. **Spring Settle (Host + Rive)**: On release, piece snaps into slot with a velocity-preserving spring bounce rather than plopping down dead.
3. **State Machine Trigger (Rive)**: Snap fires a Rive Trigger input, causing character to react (smile, cheer).
4. **Particle Burst (Host)**: A confetti or star particle emitter fires at the drop coordinates.
5. **Layout Transition (Host)**: Surrounding tiles slide into place via FLIP / layout animation.

---

## 3. The State Machine Rest Invariant (Game Engine Pattern for UI)

In game architecture and interactive UI, every character or stateful widget must obey the **Rest Invariant**:

```
[ EntryState ] ──► [ Resting / Idle State ]
                         │         ▲
                 Trigger │         │ enableExitTime (100%)
                         ▼         │ or Return Condition
                     [ Action State ]
               (Drink coffee / Pop / Bounce)
```

### The Rules of the Rest Invariant:
1. **Never create a one-way trap**: A state that has an entrance transition must always have a return path to the Resting state.
2. **Resting is alive, not static**: The resting state is an idle loop (subtle breathing, gentle hover, waiting pose) — not a frozen 0-frame dead graphic.
3. **Use `enableExitTime="true"` for discrete actions**: When an action plays (e.g. drinking coffee, putting on a hat, celebrating), set `exitTime="100%"` on the transition back to Rest so it completes its full arc and smoothly settles.
4. **Author the round-trip**: Test that after two taps or interaction cycles, the component is in the exact identical visual state as frame 0.

---

## 4. The 5-Beat Keyframe Choreography for AI Prompting

When prompting an AI assistant (Codex, Claude, Gemini) or authoring keyframes in RML, break actions into **5 discrete beats**:

| Beat | Name | Purpose | Example (Putting on a Hat / Tapping a Button) |
|---|---|---|---|
| **1** | **Rest** | Baseline neutral state. | Character idle holding coffee at side; button at 1.0 scale. |
| **2** | **Anticipation** | Wind-up in the opposite direction. | Character crouches down 5 px before raising arm; button scales down to 0.94. |
| **3** | **Action Apex** | Peak displacement and expression. | Hat placed firmly on head, eyes squint; button fills with accent color. |
| **4** | **Settle / Overshoot** | Elastic dampening past the target. | Arm settles back, hat wiggles slightly; button rebounds to 1.03. |
| **5** | **Return to Rest** | Clean resolution back to baseline. | Arm returns to side; button rests at 1.0 scale, ready for next input. |

---

## 5. Visual Edge-Case QA Matrix (Catching AI Blindspots)

AI models are blind to physical and spatial subtleties. Use this matrix to inspect every rendered animation before shipping:

| Defect | Visual Symptom | Root Cause | Fix |
|---|---|---|---|
| **Artboard Clipping** | Prop or limb cuts off flat at the top/sides during motion. | Bounding box too small for the action's apex. | Increase Artboard `width`/`height` or adjust `originX`/`originY` and scale. |
| **Latching State** | Component reacts on first tap, but stays stuck and never returns. | Missing return transition from Action state to Rest state. | Add return `<StateTransition stateToId="..." enableExitTime="true" exitTime="100"/>`. |
| **Jagged Morphing** | Crooked, jarring bumps when an SVG path deforms. | Mismatched vector vertices or sharp handles without tangent smoothing. | Use `<CubicDetachedVertex>` with aligned control points `inX/inY/outX/outY`. |
| **Aggressive Overshoot** | UI control wiggles excessively like jello. | Spring damping too low or playful cubic ease used on a standard control. | Switch to standard `out` curve (`0.23 1 0.32 1`) with zero overshoot. |
| **Off-by-One Input** | Rive component renders but never reacts to host clicks. | Mismatched input name between host code and Rive binary. | Run `python3 scripts/rive_lint.py file.riv` to get the exact string identifiers. |

---

## 6. Host Composition Code Patterns

### Continuous Gesture & Tilt Streaming (React / Web)
Stream pointer or gyroscope position continuously into Rive `StateMachineNumber` inputs (`tiltX`, `tiltY`):

```tsx
import { useRive, useStateMachineInput } from '@rive-app/react-canvas';
import { useEffect, useRef } from 'react';

export function InteractiveCharacter() {
  const { rive, RiveComponent } = useRive({
    src: '/character.riv',
    stateMachines: 'State Machine 1',
    autoplay: true,
  });

  const tiltX = useStateMachineInput(rive, 'State Machine 1', 'tiltX');
  const tiltY = useStateMachineInput(rive, 'State Machine 1', 'tiltY');

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!tiltX || !tiltY) return;
    const rect = e.currentTarget.getBoundingClientRect();
    // Normalize to -1.0 .. 1.0 range
    const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const normY = ((e.clientY - rect.top) / rect.height) * 2 - 1;
    tiltX.value = normX * 100; // Drive Rive input
    tiltY.value = normY * 100;
  };

  return (
    <div onPointerMove={handlePointerMove} className="character-stage">
      <RiveComponent />
    </div>
  );
}
```

### Milestone Celebration (Rive State Event → Host Confetti)
Trigger native particle celebrations when a Rive state machine fires an achievement event:

```tsx
import confetti from 'canvas-confetti';
import { useRive } from '@rive-app/react-canvas';
import { useEffect } from 'react';

export function QuestCard() {
  const { rive, RiveComponent } = useRive({
    src: '/quest.riv',
    stateMachines: 'State Machine 1',
    autoplay: true,
  });

  useEffect(() => {
    if (!rive) return;
    const onRiveEvent = (event: any) => {
      if (event.data?.name === 'QuestComplete') {
        confetti({ particleCount: 60, spread: 70, origin: { y: 0.7 } });
      }
    };
    rive.on('event', onRiveEvent);
    return () => rive.off('event', onRiveEvent);
  }, [rive]);

  return <RiveComponent />;
}
```
