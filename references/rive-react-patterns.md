# React and web-runtime integration

`@rive-app/react-canvas` wraps `@rive-app/canvas`. Both are on npm and both ship the
WASM inline, so `src: '/file.riv'` from `public/` is all a Next.js or Vite app needs.
Every name below — state machine, input, text run, artboard — must come from
`rive_lint.py` output, not memory.

## The hook component

```tsx
import { useEffect } from 'react';
import { useRive, useStateMachineInput, Layout, Fit, Alignment } from '@rive-app/react-canvas';

export default function Cart({ percent }: { percent: number }) {
  const { rive, RiveComponent } = useRive({
    src: '/canasta.riv',
    stateMachines: 'State Machine 1',
    autoplay: true,
    layout: new Layout({ fit: Fit.Contain, alignment: Alignment.Center }),
  });
  const progress = useStateMachineInput(rive, 'State Machine 1', 'porcentajeEnvioGratis');

  useEffect(() => {
    if (progress) progress.value = percent;   // null until the file has loaded
  }, [progress, percent]);

  return (
    <div className="flex h-full w-full items-center justify-center select-none">
      <RiveComponent className="h-full w-full max-w-[400px] max-h-[400px]" />
    </div>
  );
}
```

`useStateMachineInput(rive, machine, input, initialValue?)` returns `null` until load
and re-resolves when `rive` changes. The hook owns the instance lifecycle: it creates
on mount, resizes with the container, and cleans up on unmount. Do not `new Rive()`
inside an effect alongside it.

Several artboards in one file: `artboard: 'Circular'`. Several animations without a
machine: `animations: ['Idle']` — but then nothing reacts; if `rive_lint.py` shows a
state machine, use it.

## Sizing and sharpness

- The canvas takes its size from its container. A container with no CSS height (a
  flex child, an unsized grid cell) gives a 0×0 canvas and a blank screen with no
  error. `h-64 w-64`, `aspect-square`, or an explicit height on the parent.
- react-canvas scales the drawing surface to the device pixel ratio once the container
  has a size. Never set `width`/`height` attributes on the canvas yourself.
- `Layout` decides how the artboard fits the canvas: `Fit.Contain` letterboxes,
  `Fit.Cover` crops, `Fit.Layout` reflows an artboard built with layouts to the canvas
  size (the responsive case). Content clipped at the edges is an artboard smaller than
  its own motion; grow the artboard or switch the fit.

## The plain runtime (no React, or React without the hook)

```ts
import { Rive, Layout, Fit, Alignment, EventType } from '@rive-app/canvas';

const canvas = document.querySelector<HTMLCanvasElement>('#loader')!;
const rive = new Rive({
  src: 'https://cdn.example.com/Agente_con_IA_loader.riv',
  canvas,
  artboard: 'exported_frame',
  stateMachines: 'default',
  autoplay: true,
  layout: new Layout({ fit: Fit.Contain, alignment: Alignment.Center }),
  onLoad: () => rive.resizeDrawingSurfaceToCanvas(),   // DPR; call again on resize
  onLoadError: (e) => console.warn('rive', e),
});

const inputs = rive.stateMachineInputs('default');
inputs.find((i) => i.name === 'loading')!.value = true;
inputs.find((i) => i.name === 'woosh')!.fire();

// on unmount
rive.cleanup();
```

In a Next.js client component, `dynamic import('@rive-app/canvas')` inside an effect
keeps the WASM out of the server bundle; render a CSS fallback until `onLoad`. Keep the
instance in a ref and call `cleanup()` in the effect's return.

## Listeners, events, text, data

- **Listeners.** If the file has them (rive_lint prints `listeners: …`), the runtime
  handles hover/click on the canvas. Do not also mirror the same input from DOM events.
  `shouldDisableRiveListeners: true` turns the built-in handling off;
  `isTouchScrollEnabled: true` keeps the page scrollable over the canvas on touch.
- **Events.** `rive.on(EventType.RiveEvent, (e) => e.data)` — `data.name` is the event's
  name, `data.properties` its custom payload. `OpenUrlEvent`s only open by themselves
  with `automaticallyHandleEvents: true`.
- **Text.** `rive.setTextRunValue('title', 'Hola')`; inside a nested artboard,
  `rive.setTextRunValueAtPath('title', 'Hola', 'Card')`. The run must have a name in the
  file (rive_lint lists them).
- **Data binding.** `useRive({ ..., autoBind: true })` binds the default view model
  instance; then `rive.viewModelInstance?.number('level')!.value = 80`,
  `.string(...)`, `.boolean(...)`, `.color(...)`, `.enum(...)`, `.trigger(...).trigger()`,
  `.viewModel('battery')` for nesting. Hooks: `useViewModel(rive, { useDefault: true })`,
  `useViewModelInstance(vm, { useDefault: true, rive })`, `useViewModelInstanceNumber('level', vmi)` (returns `{ value, setValue }`)
  and its siblings (`String`, `Boolean`, `Color`, `Enum`, `Trigger`).
- **One file, many instances.** `const { riveFile, status } = useRiveFile({ src })` loads
  the bytes once; pass `riveFile` to each `useRive`.

## Cursor tracking through Number inputs

```tsx
const mouseX = useStateMachineInput(rive, 'State Machine 1', 'mouseX');
const mouseY = useStateMachineInput(rive, 'State Machine 1', 'mouseY');

const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
  const r = e.currentTarget.getBoundingClientRect();
  if (mouseX) mouseX.value = ((e.clientX - r.left) / r.width) * 100;   // whatever range the file expects
  if (mouseY) mouseY.value = ((e.clientY - r.top) / r.height) * 100;
};
```

Check the range in the file: a blend axis runs 0–100, a joystick −1..1. rive_lint prints
the default value, which usually reveals the scale.

## Performance

- Pause off-screen instances: `rive.pause()` in an `IntersectionObserver` callback,
  `rive.play()` when visible. The runtime otherwise advances every frame.
- Prefer one artboard with layers over several canvases; each canvas is its own render
  loop.
- Large `.riv`? rive_lint lists embedded fonts and images with sizes. Subset the font,
  downscale the bitmap, or host it on the Rive CDN (`enableRiveAssetCDN` is on by
  default; `assetLoader` for your own hosting).
