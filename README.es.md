<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.gif">
  <img src="assets/hero.gif" alt="Una mascota coral con un brote respira, parpadea y mira el nombre rive-animator; llega un cursor, sus ojos lo siguen, un clic la hace agacharse, saltar y aterrizar contenta, y lo despide con la mirada" width="100%">
</picture>

Archivos de Rive que funcionan antes de salir a producción y que se sienten vivos cuando salen. Un kit code-first para agentes de IA y desarrolladores: nueve recetas grabadas en el runtime real, un horneador de movimiento, conversor de SVG y Lottie, un linter para las trampas que compilan limpio y wiring listo para copiar en ocho plataformas.

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-black)](https://code.claude.com/docs)
[![Antigravity](https://img.shields.io/badge/Antigravity-Skill-black)](https://antigravity.google)
[![Rive](https://img.shields.io/badge/Rive-Format_7.3-black)](https://rive.app)
[![Tests](https://img.shields.io/badge/tests-25_passed-black)](tests/)

[English](README.md) · Español · [中文](README.zh-CN.md)

</div>

## Por qué

Un `.riv` es un programa compilado, no una imagen, y cuando falla no avisa. Compila y carga con una entrada que nadie lee, un estado sin regreso, una pose a la que salta de golpe, un loop que brinca en la costura o una rotación en grados que da cincuenta y siete vueltas. O funciona y se siente muerto: todo se mueve al mismo tiempo, cada pose frena en seco, los colores se cambian en vez de mezclarse y nada respira entre una acción y otra.

`rive-animator` detecta con su linter casi todo lo primero antes de tocar código de producción, renderiza lo demás (un estado sin regreso solo se ve al dar dos clics) y le da a tu agente un método para lo segundo.

## Recetas

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/recipes-dark.gif">
  <img src="assets/recipes.gif" alt="Ocho componentes de Rive movidos por sus entradas: un switch, un corazón con chispas, una palomita de éxito, un anillo de progreso que se vuelve verde al 100, una campana que se mece, una estrella que gira y se llena, un ecualizador y un spinner" width="100%">
</picture>

Cada cuadro es el runtime real `@rive-app/canvas-advanced` movido por entradas con guion; la etiqueta muestra la entrada tal como la pondría tu app.

| Receta | Entradas | Qué enseña |
|---|---|---|
| [Mascota viva](examples/living-mascot/build.py) | `lookX` número, `poke` trigger | Cuatro capas a la vez: respiración, parpadeos, mirada por blend y un salto con squash, stretch y follow-through |
| [Switch](examples/toggle-switch/scene.rml) | `tap` trigger, listener de clic | Estados de pose con mezcla de 240 ms; la perilla se estira con su recorrido |
| [Botón de like](examples/like-heart/scene.rml) | `liked` booleano | Anticipación, pop y asentamiento en un solo `flow`; chispas sembradas; salida más rápida |
| [Palomita de éxito](examples/success-check/scene.rml) | `fire` trigger | Entra desde 0.92 con opacidad y la palomita se dibuja; un segundo disparo regresa a reposo |
| [Anillo de progreso](examples/progress-ring/scene.rml) | `progress` número, 0–100 | Un blend state sobre el valor; completar es su propia capa |
| [Campana de tab bar](examples/tab-bar-item/scene.rml) | `active` booleano, `tap` trigger | Se mece desde la bisagra y el badajo la sigue un instante después |
| [Estrella de rating](examples/rating-star/scene.rml) | `rating` número | De contorno a relleno, un giro de 72° que nunca se rebobina, chispas en sus puntas |
| [Ecualizador](examples/audio-equalizer/scene.rml) | `isPlaying` booleano | Cinco barras con pares de ondas sembradas que nunca se sincronizan |
| [Spinner](examples/spinner-loader/scene.rml) | ninguna | Una persecución de trim que cierra su loop en tres ciclos |

## Que se sienta vivo

El método de movimiento es [rossark-motion-skill](https://github.com/rossark0/rossark-motion-skill) traducido a RML, en [references/living-motion.md](references/living-motion.md): nada se teletransporta, amplitudes chicas sobre dos curvas fuertes, piezas que giran en su pivote real, follow-through por retraso en vez de resortes, variedad sembrada y una acción principal con loops de reposo que nunca se detienen.

Rive suaviza cada segmento de keyframes por separado, así que una cadena de poses frena en cada key. `scripts/motion_keys.py` lo resuelve: `flow` pasa por cada pose sin detenerse ni pasarse, escrito como segmentos Hermite exactos con `cubicValue` (medidos contra el renderer con un cuarto de pixel de error), y `bake` convierte respiración, vaivén y follow-through en keyframes que cierran su loop.

```bash
python3 scripts/motion_keys.py flow 0:1 9:0.86 15:1.1 44:0.8 52:1.04 76:1   # agacharse, estirarse, aplastarse, asentarse
python3 scripts/motion_keys.py track 0:1 7:0.1 9:0.1 20:1:out               # un parpadeo de 7 / 2 / 11 cuadros
python3 scripts/motion_keys.py wave --base 1 --amp 0.016 --period 120 --length 240
```

## Qué pedirle a tu asistente

| Dile | Qué pasa |
|---|---|
| *"Hazme una mascota en Rive que respire, parpadee y salte al darle clic"* | Parte de `living-mascot`, deja cada número en tokens y revisa hojas de contacto antes de darlo por terminado |
| *"Este switch salta de golpe entre estados"* | Busca `RML012`, agrega mezcla a las transiciones de pose y mezcla el color |
| *"Convierte este logo SVG en un artboard interactivo de Rive"* | Corre `svg2rml.py`, agrega máquina de estados y verifica con el CLI de Rive |
| *"Mi animación de Rive se dibuja pero ignora los clics"* | Corre `rive_lint.py`, encuentra el listener que falta o la entrada muerta e imprime el wiring exacto |
| *"Dame el wiring de Flutter para mascot.riv"* | `rive_lint.py mascot.riv -f flutter` |

## Herramientas

Python 3.8+, solo biblioteca estándar.

| Script | Hace |
|---|---|
| `scripts/motion_keys.py` | Hornea canales `track`, `flow` y `wave` como keyframes de RML |
| `scripts/rml_lint.py` | Revisión previa: grados, keys de color, entradas muertas, saltos a poses, costuras de loop |
| `scripts/rive_lint.py` | Lee un `.riv`: artboards, máquinas, entradas, listeners, defectos y wiring para 8 plataformas |
| `scripts/svg2rml.py` / `lottie2rml.py` | SVG o Lottie a RML con vértices cúbicos separados |
| `scripts/make-gifs.mjs` | Graba las imágenes del README en el runtime real a 50 fps, loops sin costura, claro y oscuro |

Wiring: React (`@rive-app/react-canvas`), Vue 3, Svelte, Web Canvas, Flutter, SwiftUI, Android Kotlin y React Native. Ver [references/universal-framework-wiring.md](references/universal-framework-wiring.md).

## Registro de defectos

| Código | Atrapa | Arreglo |
|---|---|---|
| `RML011` | Una entrada declarada que ninguna condición, listener o blend lee | Conéctala o bórrala |
| `RML012` | Una transición a una pose de un cuadro sin mezcla: salta | `duration="160"`–`"300"` y un interpolador cúbico |
| `RML013` | Un `loop` cuyo último key no es igual al primero: brinca | Cierra el loop o usa `pingPong` |
| `RML004` | Rotación en grados | Radianes: una vuelta es `6.2831853` |
| `RML007` / `RML008` | Un fill sin pintura; un double sobre un color | Agrega `<SolidColor>`; usa `KeyFrameColor` |
| `RV001`–`RV012` | Defectos del binario: archivo truncado, sin artboard, 0×0, sin capas, nombres duplicados o con espacios | Ver [references/defect-ledger.md](references/defect-ledger.md) |

## Instalación

```bash
claude plugin add obeskay/rive-animator-skill                                            # Claude Code
git clone https://github.com/obeskay/rive-animator-skill.git ~/.gemini/config/skills/rive-animator   # Antigravity
```

Para trabajar en él:

```bash
git clone https://github.com/obeskay/rive-animator-skill.git && cd rive-animator-skill
npm install && npm test
npm run build:examples && npm run gifs   # requiere el CLI de Rive, ffmpeg y Chrome
```

## Licencia

MIT © [ov (obeskay)](https://github.com/obeskay). El método de movimiento da crédito a [rossark0/rossark-motion-skill](https://github.com/rossark0/rossark-motion-skill) (MIT).
