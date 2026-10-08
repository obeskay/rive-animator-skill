# Brand: rive-animator

Interactive vector state machines are small programs running on real canvas runtimes, not static pictures.

The visual identity embodies this: glowing electric cyan (`#00d2ff`) and violet bezier curves, interconnected reactive state machine nodes, precision tangent handles, and deep graphite obsidian space (`#08080a`).

## Palette

| Token | Hex | Use |
|---|---|---|
| Ink | `#08080a` | Background. Near-black graphite, never pure `#000`. |
| Paper | `#f4f2ee` | Wordmark and primary text. Warm off-white. |
| Cyan Pulse | `#00d2ff` | Primary accent dot, glowing state transitions. |
| Violet Lattice | `#8b5cf6` | State node clusters and secondary glow. |
| Muted | `#c2bcb4` | Tagline text. |
| Faint | `#00d2ff` (0.85) | Monospace footnote. |

## Wordmark

`rive-animator` set in Helvetica Neue Bold at `-0.045em` tracking, followed by a **drawn glowing rounded cyan block** (`#00d2ff`), never a typed period.

## Regenerating Banners

```bash
node assets/banner.mjs assets/build

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1200,400 --screenshot=assets/banner-en.jpg "file://$PWD/assets/build/banner-en.html"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1200,400 --screenshot=assets/banner-es.jpg "file://$PWD/assets/build/banner-es.html"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1200,400 --screenshot=assets/banner-zh.jpg "file://$PWD/assets/build/banner-zh.html"
```
