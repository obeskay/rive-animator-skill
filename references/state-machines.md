# State machines: what the file declares, what the host calls

A `LinearAnimation` is a fixed timeline. A state machine decides which timeline plays
and when, driven by inputs the host sets, by pointer listeners, or by data. Every
mechanism below has two halves: the RML that declares it and the runtime call that
drives it. `rive docs state-machines` has the full grammar.

## Inputs (what `useStateMachineInput` consumes)

Declared on the machine, referenced by id from conditions:

```xml
<StateMachine name="State Machine 1" id="0:7">
    <StateMachineBool name="hovered" id="0:40"/>
    <StateMachineNumber name="progress" value="0" id="0:41"/>
    <StateMachineTrigger name="pressed" id="0:42"/>

    <StateMachineLayer name="Layer 1" id="0:8">
        <AnyState x="400" y="0"/>
        <ExitState x="480" y="0"/>
        <EntryState x="0" y="16"><StateTransition stateToId="0:12"/></EntryState>

        <AnimationState animationId="0:20" x="160" y="0" id="0:12">
            <StateTransition stateToId="0:13" duration="150">
                <TransitionBoolCondition inputId="0:40" opValue="equal"/>
            </StateTransition>
            <StateTransition stateToId="0:14">
                <TransitionNumberCondition inputId="0:41" opValue="greaterThan" value="80"/>
            </StateTransition>
        </AnimationState>
        <AnimationState animationId="0:21" x="320" y="0" id="0:13"/>
        <AnimationState animationId="0:22" x="320" y="120" id="0:14"/>
    </StateMachineLayer>
</StateMachine>
```

| Condition | Input | Compares |
|---|---|---|
| `TransitionBoolCondition` | `StateMachineBool` | `equal` fires when true, `notEqual` when false; there is no `value` |
| `TransitionNumberCondition` | `StateMachineNumber` | against its `value` with `equal`, `notEqual`, `lessThan`, `lessThanOrEqual`, `greaterThan`, `greaterThanOrEqual` |
| `TransitionTriggerCondition` | `StateMachineTrigger` | fired since the last check |

Host side:

```ts
const hovered = useStateMachineInput(rive, 'State Machine 1', 'hovered');   // Boolean
const progress = useStateMachineInput(rive, 'State Machine 1', 'progress'); // Number
const pressed = useStateMachineInput(rive, 'State Machine 1', 'pressed');   // Trigger
hovered.value = true; progress.value = 80; pressed.fire();
// plain runtime:
rive.stateMachineInputs('State Machine 1').find((i) => i.name === 'pressed')?.fire();
// an input inside a nested artboard, by path:
rive.setNumberStateAtPath('progress', 80, 'Gauge');
```

The CLI docs call inputs deprecated in favour of view model properties, and for new
data-driven work they are right. Inputs remain the right choice for a machine that lives
inside a nestable component (a nested artboard inherits its parent's data context, so a
view-model-driven machine goes quiet the moment the component is placed), and they are
what every existing editor file uses. `rive_lint.py` lists them by exact name.

## Listeners (the file handles the pointer itself)

```xml
<StateMachineListenerSingle targetId="0:14" listenerTypeValue="enter" name="In">
    <ListenerBoolChange inputId="0:40" value="1"/>
</StateMachineListenerSingle>
<StateMachineListenerSingle targetId="0:14" listenerTypeValue="click" name="Tap">
    <ListenerTriggerChange inputId="0:42"/>
</StateMachineListenerSingle>
```

`listenerTypeValue` is one of `enter`, `exit`, `down`, `up`, `move`, `click`, `drag`
and more (`rive schema StateMachineListenerSingle`). `targetId` is the drawable whose hit
area is watched; the artboard itself is not a target — give it a background shape.
`ListenerAlignTarget` moves a node with the pointer (drag handles); `ListenerFireEvent`
notifies the host; `ListenerViewModelChange` writes a view model property.

Host side: nothing. The web runtime attaches pointer handlers to the canvas when the
machine has listeners. Do not also set the same input from React `onMouseEnter`; two
writers fight. To turn the built-in handling off: `shouldDisableRiveListeners: true`.
On touch devices, `isTouchScrollEnabled: true` lets the page still scroll over the
canvas.

## Layers

Layers in one machine run simultaneously, each holding its own state. One layer per
thing that can be in a state on its own: hover on one, selection on another, an idle
pulse on a third. Inputs are declared once on the machine and visible to every layer.
If two layers key the same property, the later layer wins.

A layer with no inputs, no listeners and no conditions plays its animation forever —
the whole recipe for a spinner or a breathing dot, provided the animation carries
`loopValue="loop"`.

## Blend states

`BlendState1DInput` mixes animations along one number input; `BlendStateDirect` gives
each animation its own weight; `BlendState1DViewModel` takes the axis from a bound
property.

```xml
<StateMachineNumber name="speed" id="0:60"/>
<BlendState1DInput inputId="0:60" x="160" y="0" id="0:70">
    <BlendAnimation1D animationId="0:71" value="0"/>
    <BlendAnimation1D animationId="0:72" value="50"/>
    <BlendAnimation1D animationId="0:73" value="100"/>
</BlendState1DInput>
```

Weights run 0–100, not 0–1; children must be in ascending `value`; every blended
property must be keyed in every pose or the blend jumps. A `Joystick` is the other
2-D tool: it scrubs two timelines from an `x`/`y` pair (−1..1) — how a face follows the
cursor. `rive docs easing`.

## Events (the file talks to the host)

```xml
<Event name="ding" id="0:60"/>
<AnimationState animationId="0:20" id="0:12">
    <StateMachineFireEvent eventId="0:60" occursValue="atEnd"/>
</AnimationState>
<StateMachineListenerSingle targetId="0:14" listenerTypeValue="click" name="Next">
    <ListenerFireEvent eventId="0:60"/>
</StateMachineListenerSingle>
```

`Event` reports; `OpenUrlEvent` opens its `url`; `AudioEvent` plays an `AudioAsset`.
Custom properties nested in an `Event` ride along as payload.

```ts
import { EventType, RiveEventType } from '@rive-app/react-canvas';
rive.on(EventType.RiveEvent, (e) => {
  const data = e.data as { name: string; type?: number; properties?: Record<string, unknown> };
  if (data.name === 'ding') onDing(data.properties);
});
// OpenUrl events only open automatically with automaticallyHandleEvents: true.
```

## View models and data binding (the modern host interface)

```xml
<ViewModel defaultInstanceId="0:41" name="Battery" id="0:40">
    <ViewModelPropertyNumber name="level" id="0:45"/>
    <ViewModelPropertyBoolean name="charging" id="0:46"/>
    <ViewModelInstance exports="true" name="Default" id="0:41">
        <ViewModelInstanceNumber propertyValue="50" viewModelPropertyId="0:45"/>
        <ViewModelInstanceBoolean propertyValue="false" viewModelPropertyId="0:46"/>
    </ViewModelInstance>
</ViewModel>

<Artboard viewModelId="0:40" defaultStateMachineId="0:7" ...>
    <Shape ...>
        <Rectangle width="120" height="20" name="Bar">
            <DataBindContext sourcePathIds="0:40-0:45" propertyKey="20"/>   <!-- Rectangle.width -->
        </Rectangle>
    </Shape>
</Artboard>
```

Bind the property that exists on the target (`width` is on `Rectangle`, not `Shape`);
paths are absolute; a dangling path compiles and does nothing (`inspect` reports it as
`unresolved-bind-path`). A transition reads a property with
`TransitionViewModelCondition`; a listener writes one with `ListenerViewModelChange`.
`rive docs data` covers converters, enums and lists.

```ts
const { rive } = useRive({ src: '/battery.riv', stateMachines: 'State Machine 1', autoplay: true, autoBind: true });
rive?.viewModelInstance?.number('level')?.value = 80;
rive?.viewModelInstance?.boolean('charging')?.value = true;
rive?.viewModelInstance?.trigger('refresh')?.trigger();
// React hooks in @rive-app/react-canvas 4.x:
const vm = useViewModel(rive, { useDefault: true });
const vmi = useViewModelInstance(vm, { useDefault: true, rive });
const { value: level, setValue: setLevel } = useViewModelInstanceNumber('level', vmi);
```

`rive_lint.py` prints every view model with its property names and types, which is the
list of paths the host may use.

## Checking that it behaves

Structure is not behaviour. Count what exists, then click it:

```bash
rive inspect . --json | jq .problems
rive <dir> --screenshot=rest.png
rive <dir> --screenshot=on.png  --pointer=click@120,60 --advance=20
rive <dir> --screenshot=off.png --pointer=click@120,60 --pointer=move@400,400 --pointer=click@120,60 --advance=20
```

`rest` and `on` must differ, or the control does nothing; `off` must match `rest`, or
it only works one way — the single most common state machine bug, invisible to every
static check. Put a filler gesture between two clicks on the same target: a value a
listener writes is not visible to the next listener until a frame has passed.
