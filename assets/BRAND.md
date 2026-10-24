# Brand: rive-animator

Paper and ink. The images sit directly on GitHub's own canvas (white, or `#0D1117` in dark
mode), so nothing is boxed and nothing glows. Life comes from motion, not from effects.

| Token | Hex | Use |
|---|---|---|
| Ink | `#1F1C19` | Wordmark on light, eyes, mouth |
| Paper | `#F4F1EA` | Wordmark on dark |
| Cell | `#F6F3EE` / `#151A21` | Recipe tiles, light / dark |
| Ember | `#E4572E` | The accent: the wordmark's block, the mascot, active states |
| Amber | `#F2A93B` | Rating, badges, sparks |
| Sage | `#6F8F72` | Success, toggled on, the sprout |
| Stone | `#8E877E` | Inactive states; at 22–25% alpha, tracks and the shadow (it reads on both canvases) |

Wordmark: `rive-animator` in Helvetica Neue Bold, `-0.045em` tracking, followed by a drawn ember
block with continuous-curvature corners, never a typed period. Tiles use `corner-shape:
superellipse(1.6)`.

Mascot: `examples/living-mascot`, a coral gumdrop with a sprout. It is the hero, the social card
and the worked example of `references/living-motion.md`.

## Regenerating

```bash
npm run build:examples        # compiles every recipe, regenerating the mascot from build.py
node scripts/make-gifs.mjs    # hero.gif, hero-dark.gif, recipes.gif, recipes-dark.gif, social.png
node scripts/make-gifs.mjs --sheet   # also contact sheets in build/sheets/ to read before committing
```

`social.png` is GitHub's social preview (1280×640): upload it in the repository settings.
