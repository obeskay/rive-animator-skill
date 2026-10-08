# Universal Framework Wiring Guide for Rive

Rive runtimes are available natively across every major frontend platform.
Use `python3 scripts/rive_lint.py file.riv --framework <platform>` to generate the exact wiring for your binary.

---

## Supported Frameworks & Matrix

| Platform | Package | State Machine API | Pointer Events | Data Binding |
|---|---|---|---|---|
| **React** | `@rive-app/react-canvas` | `useStateMachineInput()` | Automatic via canvas | `autoBind: true` |
| **Vue 3** | `@rive-app/canvas` | `r.stateMachineInputs()` | Automatic via canvas | `autoBind: true` |
| **Svelte** | `@rive-app/canvas` | `r.stateMachineInputs()` | Automatic via canvas | `autoBind: true` |
| **Vanilla Web** | `@rive-app/canvas` | `r.stateMachineInputs()` | Automatic via canvas | Supported |
| **Flutter** | `rive` | `StateMachineController.findInput()` | Built-in | Supported |
| **SwiftUI (iOS/macOS)** | `RiveRuntime` | `RiveViewModel.setInput()` | Built-in | Supported |
| **Android (Kotlin)** | `app.rive:rive-android` | `RiveAnimationView.setBooleanState()` | Built-in | Supported |
| **React Native** | `@rive-app/react-native` | `riveRef.current.setInputState()` | Touch handlers | Supported |

---

## 1. React (`@rive-app/react-canvas`)

```bash
npm install @rive-app/react-canvas
```

```tsx
import { useEffect } from 'react';
import { useRive, useStateMachineInput, Layout, Fit, Alignment } from '@rive-app/react-canvas';

export default function InteractiveComponent({ isOn, progress }: { isOn: boolean; progress: number }) {
  const { rive, RiveComponent } = useRive({
    src: '/component.riv',
    stateMachines: 'State Machine 1',
    autoplay: true,
    layout: new Layout({ fit: Fit.Contain, alignment: Alignment.Center }),
  });

  const toggleInput = useStateMachineInput(rive, 'State Machine 1', 'isOn');
  const progressInput = useStateMachineInput(rive, 'State Machine 1', 'progress');
  const fireTrigger = useStateMachineInput(rive, 'State Machine 1', 'fire');

  useEffect(() => {
    if (toggleInput) toggleInput.value = isOn;
  }, [toggleInput, isOn]);

  useEffect(() => {
    if (progressInput) progressInput.value = progress;
  }, [progressInput, progress]);

  return (
    <div className="w-48 h-48">
      <RiveComponent onClick={() => fireTrigger?.fire()} />
    </div>
  );
}
```

---

## 2. Vue 3 (`@rive-app/canvas`)

```bash
npm install @rive-app/canvas
```

```html
<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { Rive, Layout, Fit, Alignment } from '@rive-app/canvas';

const canvasRef = ref(null);
let riveInstance = null;
let toggleInput = null;

onMounted(() => {
  riveInstance = new Rive({
    src: '/component.riv',
    canvas: canvasRef.value,
    autoplay: true,
    stateMachines: 'State Machine 1',
    layout: new Layout({ fit: Fit.Contain, alignment: Alignment.Center }),
    onLoad: () => {
      riveInstance.resizeDrawingSurfaceToCanvas();
      const inputs = riveInstance.stateMachineInputs('State Machine 1');
      toggleInput = inputs.find(i => i.name === 'isOn');
    },
  });
});

onBeforeUnmount(() => {
  if (riveInstance) riveInstance.cleanup();
});
</script>

<template>
  <div style="width: 200px; height: 200px;">
    <canvas ref="canvasRef" width="200" height="200" style="width: 100%; height: 100%;"></canvas>
  </div>
</template>
```

---

## 3. Svelte (`@rive-app/canvas`)

```bash
npm install @rive-app/canvas
```

```html
<script>
  import { onMount } from 'svelte';
  import { Rive, Layout, Fit, Alignment } from '@rive-app/canvas';

  let canvas;
  let rive;
  let toggleInput;

  onMount(() => {
    rive = new Rive({
      src: '/component.riv',
      canvas,
      autoplay: true,
      stateMachines: 'State Machine 1',
      layout: new Layout({ fit: Fit.Contain, alignment: Alignment.Center }),
      onLoad: () => {
        rive.resizeDrawingSurfaceToCanvas();
        toggleInput = rive.stateMachineInputs('State Machine 1').find(i => i.name === 'isOn');
      }
    });

    return () => {
      if (rive) rive.cleanup();
    };
  });
</script>

<canvas bind:this={canvas} width="200" height="200"></canvas>
```

---

## 4. Vanilla JavaScript / Web Components (`@rive-app/canvas`)

```html
<canvas id="rive-canvas" width="400" height="400" style="width: 200px; height: 200px;"></canvas>

<script type="module">
  import { Rive, Layout, Fit, Alignment } from '@rive-app/canvas';

  const canvas = document.getElementById('rive-canvas');
  const r = new Rive({
    src: '/component.riv',
    canvas: canvas,
    autoplay: true,
    stateMachines: 'State Machine 1',
    layout: new Layout({ fit: Fit.Contain, alignment: Alignment.Center }),
    onLoad: () => {
      r.resizeDrawingSurfaceToCanvas();
      const inputs = r.stateMachineInputs('State Machine 1');
      const toggle = inputs.find(i => i.name === 'isOn');
      
      // Update inputs anytime:
      // toggle.value = true;
    },
  });
</script>
```

---

## 5. Flutter (`rive`)

```yaml
dependencies:
  rive: ^0.13.0
```

```dart
import 'package:flutter/material.dart';
import 'package:rive/rive.dart';

class InteractiveRiveWidget extends StatefulWidget {
  const InteractiveRiveWidget({super.key});

  @override
  State<InteractiveRiveWidget> createState() => _InteractiveRiveWidgetState();
}

class _InteractiveRiveWidgetState extends State<InteractiveRiveWidget> {
  SMIBool? _isOn;
  SMITrigger? _fire;

  void _onRiveInit(Artboard artboard) {
    final controller = StateMachineController.fromArtboard(artboard, 'State Machine 1');
    if (controller != null) {
      artboard.addController(controller);
      _isOn = controller.findInput<bool>('isOn') as SMIBool?;
      _fire = controller.findInput('fire') as SMITrigger?;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        if (_isOn != null) _isOn!.value = !_isOn!.value;
        _fire?.fire();
      },
      child: SizedBox(
        width: 200,
        height: 200,
        child: RiveAnimation.asset(
          'assets/component.riv',
          onInit: _onRiveInit,
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}
```

---

## 6. iOS / macOS SwiftUI (`RiveRuntime`)

Add Swift package: `https://github.com/rive-app/rive-ios`

```swift
import SwiftUI
import RiveRuntime

struct RiveInteractiveView: View {
    @StateObject private var rive = RiveViewModel(
        fileName: "component",
        stateMachineName: "State Machine 1",
        autoPlay: true
    )

    var body: some View {
        rive.view()
            .frame(width: 200, height: 200)
            .onTapGesture {
                rive.setInput("isOn", value: true)
                rive.triggerInput("fire")
            }
    }
}
```

---

## 7. Android Kotlin (`app.rive:rive-android`)

```gradle
dependencies {
    implementation 'app.rive:rive-android:9.0.0'
}
```

In layout XML:
```xml
<app.rive.runtime.kotlin.RiveAnimationView
    android:id="@+id/riveView"
    android:layout_width="200dp"
    android:layout_height="200dp"
    app:riveResource="@raw/component"
    app:riveStateMachine="State Machine 1"
    app:riveAutoPlay="true" />
```

In Activity / Fragment:
```kotlin
val riveView = findViewById<RiveAnimationView>(R.id.riveView)

// Set Boolean
riveView.setBooleanState("State Machine 1", "isOn", true)

// Set Number
riveView.setNumberState("State Machine 1", "progress", 75f)

// Fire Trigger
riveView.fireState("State Machine 1", "fire")
```

---

## 8. React Native (`@rive-app/react-native`)

```bash
npm install @rive-app/react-native
```

```tsx
import React, { useRef } from 'react';
import { View, TouchableOpacity } from 'react-native';
import Rive, { RiveRef } from '@rive-app/react-native';

export default function RiveComponent() {
  const riveRef = useRef<RiveRef>(null);

  const handlePress = () => {
    riveRef.current?.fireState('State Machine 1', 'fire');
    riveRef.current?.setInputState('State Machine 1', 'isOn', true);
  };

  return (
    <TouchableOpacity onPress={handlePress}>
      <Rive
        ref={riveRef}
        resourceName="component"
        stateMachineName="State Machine 1"
        autoplay={true}
        style={{ width: 200, height: 200 }}
      />
    </TouchableOpacity>
  );
}
```
