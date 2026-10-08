#!/usr/bin/env node
/**
 * Build the README's GIFs from the compiled examples, in the real Rive runtime.
 *
 *   node scripts/make-gifs.mjs                every example, then the hero boards
 *   node scripts/make-gifs.mjs like-heart     one example
 *   node scripts/make-gifs.mjs --boards       only the hero boards and the social card
 *
 * Needs ffmpeg on PATH, a local Chrome (or CHROME_PATH), and `npm install`.
 *
 * Each GIF is a scripted session against the state machine, not a timeline export:
 * the script sets inputs (or presses the pointer, for files with listeners) at fixed
 * times, the runtime advances on a fixed clock, and the chip in the corner shows the
 * input as the app would set it. If an input is not wired to anything, the GIF shows
 * that too, because nothing moves.
 */
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { extname, join, dirname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const ASSETS = join(ROOT, 'assets');
const FPS = 30;
const GROUND = '#F3EEE6';

// t in seconds. `set` writes an input, `fire` fires a trigger, `click` presses the
// pointer at artboard coordinates (only meaningful when the file has a listener).
const DEMOS = {
  'toggle-switch': {
    seconds: 3.2, cursor: true,
    events: [{ t: 0.8, click: [120, 80] }, { t: 2.2, click: [120, 80] }],
    chip: 'tap',
  },
  'like-heart': {
    seconds: 3.0,
    events: [{ t: 0.6, set: ['liked', true] }, { t: 2.2, set: ['liked', false] }],
  },
  'success-check': {
    seconds: 2.4,
    events: [{ t: 0.5, fire: 'fire' }],
  },
  'rating-star': {
    seconds: 2.6,
    events: [{ t: 0.5, set: ['rating', 1] }, { t: 2.0, set: ['rating', 0] }],
  },
  'tab-bar-item': {
    seconds: 2.6,
    events: [{ t: 0.5, set: ['active', true] }, { t: 0.5, fire: 'tap' }, { t: 1.9, set: ['active', false] }],
  },
  'audio-equalizer': {
    seconds: 3.0,
    events: [{ t: 2.0, set: ['isPlaying', false] }],
  },
  'progress-ring': {
    seconds: 2.4,
    ramp: { input: 'progress', from: 0, to: 100, start: 0.2, end: 1.8 },
  },
  'spinner-loader': { seconds: 2.0, events: [] },
};

const HERO = ['toggle-switch', 'like-heart', 'success-check', 'progress-ring',
  'tab-bar-item', 'rating-star', 'audio-equalizer', 'spinner-loader'];

const MIME = { '.html': 'text/html', '.mjs': 'text/javascript', '.js': 'text/javascript',
  '.wasm': 'application/wasm', '.riv': 'application/octet-stream' };

function serve() {
  const server = createServer((req, res) => {
    const path = normalize(join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname)));
    if (!path.startsWith(ROOT) || !existsSync(path) || statSync(path).isDirectory()) {
      console.error(`  404 ${req.url}`);
      res.writeHead(404).end();
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[extname(path)] || 'application/octet-stream' });
    res.end(readFileSync(path));
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

function resolveChrome() {
  return [process.env.CHROME_PATH,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ].find((p) => p && existsSync(p));
}

const PAGE = (cells, { cols, size, gap, pad, radius, frame }) => `<!doctype html><html><head><meta charset="utf-8"><link rel="icon" href="data:,"><style>
  html,body{margin:0;background:${frame}}
  .board{display:grid;grid-template-columns:repeat(${cols},${size}px);gap:${gap}px;padding:${pad}px;width:max-content;background:${frame}}
  .cell{position:relative;width:${size}px;height:${size}px;border-radius:${radius}px;overflow:hidden;background:${GROUND}}
  canvas{position:absolute;inset:0;width:${size}px;height:${size}px}
  .chip{position:absolute;left:12px;bottom:11px;display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:7px;
    background:rgba(30,27,24,.06);color:#5E5750;font:600 10.5px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.02em;
    transition:none;font-variant-numeric:tabular-nums}
  .chip i{width:7px;height:7px;border-radius:50%;background:#C2BCB4}
  .chip.hot i{background:#C8522B}
  .cursor{position:absolute;left:0;top:0;width:22px;height:22px;pointer-events:none;opacity:0}
</style></head><body><div class="board">${cells.map((c, i) => `<div class="cell">
  <canvas id="c${i}" width="${size * 2}" height="${size * 2}"></canvas>
  <div class="chip" id="chip${i}" style="display:none"><i></i><span></span></div>
  <svg class="cursor" id="cur${i}" viewBox="0 0 24 24"><path d="M5 3l14 8-6 1.6L10 19z" fill="#1E1B18" stroke="#F3EEE6" stroke-width="1.6" stroke-linejoin="round"/></svg>
</div>`).join('')}</div>
<script type="module">
  import RiveCanvas from '/node_modules/@rive-app/canvas-advanced/canvas_advanced.mjs';
  const rive = await RiveCanvas({ locateFile: () => '/node_modules/@rive-app/canvas-advanced/rive.wasm' });
  window.cells = await Promise.all(${JSON.stringify(cells.map((c) => c.riv))}.map(async (url, i) => {
    const canvas = document.getElementById('c' + i);
    const renderer = rive.makeRenderer(canvas);
    const file = await rive.load(new Uint8Array(await (await fetch(url)).arrayBuffer()));
    const artboard = file.defaultArtboard();
    const sm = new rive.StateMachineInstance(artboard.stateMachineByIndex(0), artboard);
    const inputs = {};
    for (let k = 0; k < sm.inputCount(); k++) { const inp = sm.input(k); inputs[inp.name] = inp; }
    const b = artboard.bounds;
    const scale = Math.min(canvas.width / (b.maxX - b.minX), canvas.height / (b.maxY - b.minY));
    const ox = (canvas.width - (b.maxX - b.minX) * scale) / 2, oy = (canvas.height - (b.maxY - b.minY) * scale) / 2;
    return { canvas, renderer, artboard, sm, inputs, scale, ox, oy, b };
  }));
  const typed = (inp) => inp.type === rive.SMIInput.bool ? inp.asBool() : inp.type === rive.SMIInput.number ? inp.asNumber() : inp.asTrigger();
  window.step = (i, dt, actions) => {
    const c = window.cells[i];
    for (const a of actions) {
      if (a.set) { const inp = c.inputs[a.set[0]]; if (!inp) throw new Error('no input ' + a.set[0]); typed(inp).value = a.set[1]; }
      if (a.fire) { const inp = c.inputs[a.fire]; if (!inp) throw new Error('no input ' + a.fire); typed(inp).fire(); }
      if (a.click) { c.sm.pointerDown(a.click[0], a.click[1], 0); c.sm.pointerUp(a.click[0], a.click[1], 0); }
    }
    c.sm.advanceAndApply(dt);
    c.renderer.clear();
    c.renderer.save();
    c.renderer.align(rive.Fit.contain, rive.Alignment.center,
      { minX: 0, minY: 0, maxX: c.canvas.width, maxY: c.canvas.height }, c.artboard.bounds);
    c.artboard.draw(c.renderer);
    c.renderer.restore();
    rive.resolveAnimationFrame();
  };
  // artboard coordinates to CSS pixels inside the cell
  window.toCss = (i, x, y) => { const c = window.cells[i]; return [(c.ox + (x - c.b.minX) * c.scale) / 2, (c.oy + (y - c.b.minY) * c.scale) / 2]; };
  window.ready = true;
</script></body></html>`;

function riv(name) {
  return `/examples/${name}/build/${name}.riv`;
}

/** Everything a cell shows at time t: the runtime actions due, the chip, the cursor. */
function plan(name) {
  const demo = DEMOS[name];
  if (!demo) throw new Error(`no demo script for ${name}`);
  const events = demo.events || [];
  const fired = (t, dt) => events.filter((e) => e.t >= t && e.t < t + dt);
  return {
    name, riv: riv(name), seconds: demo.seconds,
    actions(t, dt) {
      const due = fired(t, dt).map(({ t: _, ...a }) => a);
      if (demo.ramp) {
        const { input, from, to, start, end } = demo.ramp;
        const k = Math.min(1, Math.max(0, (t - start) / (end - start)));
        due.push({ set: [input, from + (to - from) * (1 - (1 - k) ** 3)] });
      }
      return due;
    },
    chip(t) {
      if (demo.ramp) {
        const { input, from, to, start, end } = demo.ramp;
        const k = Math.min(1, Math.max(0, (t - start) / (end - start)));
        return { text: `${input} ${String(Math.round(from + (to - from) * (1 - (1 - k) ** 3))).padStart(3, ' ')}`, hot: k > 0 && k < 1 };
      }
      const past = events.filter((e) => e.t <= t);
      const trig = events.filter((e) => (e.fire || e.click) && t >= e.t && t < e.t + 0.35);
      const sets = {};
      for (const e of past) if (e.set) sets[e.set[0]] = e.set[1];
      const bools = events.filter((e) => e.set).map((e) => e.set[0]);
      const label = demo.chip || [...new Set(bools)][0] || events.find((e) => e.fire)?.fire;
      if (!label) return null;
      if (label in sets || bools.includes(label)) {
        const v = label in sets ? sets[label] : initial(name, label);
        return { text: `${label} ${v}`, hot: events.some((e) => e.set && e.set[0] === label && t >= e.t && t < e.t + 0.35) };
      }
      return { text: label, hot: trig.length > 0 };
    },
    cursor(t) {
      if (!demo.cursor) return null;
      const clicks = events.filter((e) => e.click);
      const [x, y] = clicks[0].click;
      const first = clicks[0].t;
      // glide in from the lower right, rest on the target, press on each click
      const k = Math.min(1, Math.max(0, (t - (first - 0.6)) / 0.5));
      const ease = 1 - (1 - k) ** 3;
      const press = clicks.some((e) => t >= e.t - 0.05 && t < e.t + 0.12);
      return { x: x + 60 * (1 - ease), y: y + 50 * (1 - ease), o: k > 0 ? 1 : 0, s: press ? 0.86 : 1 };
    },
  };
}

const INITIAL = {};
function initial(name, input) {
  return INITIAL[`${name}:${input}`];
}

function readInitials() {
  for (const name of Object.keys(DEMOS)) {
    const rml = readFileSync(join(ROOT, 'examples', name, 'scene.rml'), 'utf8');
    for (const m of rml.matchAll(/<StateMachine(Bool|Number)\s+name="([^"]+)"[^>]*?(?:value="([^"]*)")?\s*\/>/g)) {
      const raw = m[3] ?? (m[1] === 'Bool' ? 'false' : '0');
      INITIAL[`${name}:${m[2]}`] = m[1] === 'Bool' ? raw === 'true' : Number(raw);
    }
  }
}

async function board(browser, base, names, out, layout) {
  const cells = names.map(plan);
  const seconds = layout.seconds ?? Math.max(...cells.map((c) => c.seconds));
  const page = await browser.newPage();
  const rows = Math.ceil(cells.length / layout.cols);
  await page.setViewport({
    width: layout.cols * layout.size + (layout.cols - 1) * layout.gap + 2 * layout.pad,
    height: rows * layout.size + (rows - 1) * layout.gap + 2 * layout.pad,
    deviceScaleFactor: 2,
  });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  const html = join(ROOT, `.gif-board-${process.pid}.html`);
  writeFileSync(html, PAGE(cells, layout));
  const tmp = mkdtempSync(join(tmpdir(), 'rive-gif-'));
  try {
    await page.goto(`${base}/${html.slice(ROOT.length + 1)}`, { waitUntil: 'load' });
    await page.waitForFunction('window.ready === true', { timeout: 15000 }).catch(() => {
      throw new Error(`runtime did not load: ${errors.join(' | ') || 'timeout'}`);
    });
    const dt = 1 / FPS;
    const count = Math.round(seconds * FPS);
    const element = await page.$('.board');
    for (let f = 0; f < count; f += 1) {
      const t = f * dt;
      await page.evaluate((frame) => {
        frame.forEach((cell, i) => {
          window.step(i, cell.dt, cell.actions);
          const chip = document.getElementById('chip' + i);
          if (cell.chip) {
            chip.style.display = 'flex';
            chip.querySelector('span').textContent = cell.chip.text;
            chip.classList.toggle('hot', cell.chip.hot);
          }
          const cur = document.getElementById('cur' + i);
          if (cell.cursor) {
            const [x, y] = window.toCss(i, cell.cursor.x, cell.cursor.y);
            cur.style.opacity = cell.cursor.o;
            cur.style.transform = `translate(${x - 4}px, ${y - 3}px) scale(${cell.cursor.s})`;
          }
        });
      }, cells.map((c) => ({
        dt: t === 0 ? 0 : dt,
        actions: c.actions(t, dt),
        chip: c.chip(t),
        cursor: c.cursor(t),
      })));
      if (errors.length) throw new Error(errors.join(' | '));
      await element.screenshot({ path: join(tmp, `f-${String(f).padStart(4, '0')}.png`) });
    }
    execFileSync('ffmpeg', [
      '-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', join(tmp, 'f-%04d.png'),
      '-vf', `scale=${layout.outWidth}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=${layout.colors}:stats_mode=diff[p];` +
        '[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle',
      '-loop', '0', out,
    ], { stdio: ['ignore', 'pipe', 'pipe'] });
    const kb = Math.round(statSync(out).size / 1024);
    console.log(`  ${out.slice(ROOT.length + 1).padEnd(30)} ${String(count).padStart(3)} frames  ${kb} KB`);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
    rmSync(html, { force: true });
    await page.close();
  }
}

async function main() {
  const args = process.argv.slice(2);
  const boardsOnly = args.includes('--boards');
  const only = args.find((a) => !a.startsWith('--'));
  if (only && !DEMOS[only]) throw new Error(`no demo script for ${only}; add one to DEMOS`);
  for (const name of Object.keys(DEMOS)) {
    if (!existsSync(join(ROOT, riv(name)))) throw new Error(`missing ${riv(name)}; run npm run build:examples`);
  }
  readInitials();

  const executablePath = resolveChrome();
  if (!executablePath) throw new Error('no Chrome found; set CHROME_PATH');
  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await puppeteer.launch({ executablePath, headless: 'shell', args: ['--force-color-profile=srgb'] });
  try {
    if (!boardsOnly) {
      console.log('examples');
      for (const name of only ? [only] : Object.keys(DEMOS)) {
        await board(browser, base, [name], join(ASSETS, `${name}.gif`),
          { cols: 1, size: 240, gap: 0, pad: 0, radius: 0, frame: GROUND, outWidth: 240, colors: 96 });
      }
    }
    if (only) return;
    console.log('boards');
    // framed for GitHub's light and dark canvases; the README picks one with <picture>
    for (const [file, frame] of [['hero.gif', '#FFFFFF'], ['hero-dark.gif', '#0D1117']]) {
      await board(browser, base, HERO, join(ASSETS, file),
        { cols: 4, size: 200, gap: 12, pad: 12, radius: 18, frame, outWidth: 872, colors: 160, seconds: 4 });
    }
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch((error) => {
  console.error(`make-gifs: ${error.message}`);
  process.exit(1);
});
