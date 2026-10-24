#!/usr/bin/env node
/**
 * Build the README's animated images from the compiled examples, in the real Rive runtime.
 *
 *   node scripts/make-gifs.mjs              hero + recipe board, light and dark, and the social card
 *   node scripts/make-gifs.mjs hero         only the hero
 *   node scripts/make-gifs.mjs recipes      only the recipe board
 *   node scripts/make-gifs.mjs --sheet      also write a contact sheet of every GIF to build/sheets/
 *
 * Needs ffmpeg on PATH, a local Chrome (or CHROME_PATH), `npm install`, and `npm run build:examples`.
 *
 * Every image is a scripted session against the state machines, not a timeline export: the
 * script sets inputs, moves a cursor and clicks at fixed times, and the runtime advances on a
 * fixed 50 fps clock (the fastest rate a GIF plays reliably). Every session ends in the state it
 * started in, so the GIF loops without a seam. An input wired to nothing shows: nothing moves.
 */
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { extname, join, dirname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const ASSETS = join(ROOT, 'assets');
const FPS = 50;

// framed for GitHub's own canvases, so nothing sits in a box: the README picks one with <picture>
const THEMES = {
  light: { page: '#FFFFFF', cell: '#F6F3EE', ink: '#1F1C19', muted: '#7A736B', chip: 'rgba(31,28,25,.055)', dot: '#CFC8BF' },
  dark: { page: '#0D1117', cell: '#151A21', ink: '#F4F1EA', muted: '#8E877E', chip: 'rgba(244,241,234,.06)', dot: '#3B3F45' },
};
const HOT = '#E4572E';

// ---------------------------------------------------------------- the scripts
const smooth = (p) => (p <= 0 ? 0 : p >= 1 ? 1 : p * p * (3 - 2 * p));
const seg = (t, a, b) => smooth((t - a) / (b - a));
const arrive = (p) => 1 - (1 - Math.min(1, Math.max(0, p))) ** 3;

// Recipes share one 4-second clock. t in seconds. `set` writes an input, `fire` fires a
// trigger, `click` presses the pointer at artboard coordinates (for files with listeners).
const RECIPES = {
  'toggle-switch': { events: [{ t: 0.7, click: [120, 80] }, { t: 2.5, click: [120, 80] }], chip: 'tap', cursor: [120, 80] },
  'like-heart': { events: [{ t: 0.6, set: ['liked', true] }, { t: 2.6, set: ['liked', false] }] },
  'success-check': { events: [{ t: 0.5, fire: 'fire' }, { t: 2.9, fire: 'fire' }] },
  'progress-ring': {
    value(t) { return 100 * (seg(t, 0.3, 2.0) - seg(t, 3.0, 3.6)); },
    input: 'progress',
  },
  'tab-bar-item': { events: [{ t: 0.6, set: ['active', true] }, { t: 0.6, fire: 'tap' }, { t: 2.8, set: ['active', false] }] },
  'rating-star': { events: [{ t: 0.7, set: ['rating', 1] }, { t: 2.8, set: ['rating', 0] }] },
  'audio-equalizer': { preroll: ['isPlaying', false], events: [{ t: 0.4, set: ['isPlaying', true] }, { t: 2.9, set: ['isPlaying', false] }] },
  'spinner-loader': { events: [] },
};
const RECIPE_SECONDS = 4;

// The hero: one main action and its idle life. The mascot glances at the wordmark, the cursor
// arrives already moving from beyond the edge, the eyes follow it, a click makes it hop, the
// cursor leaves and the eyes see it out. 8 s = two idle loops and one blink loop.
const HERO_SECONDS = 8;
const HERO = { w: 960, h: 320, mascot: { left: 620, top: 12, w: 320, h: 300 }, poke: [206, 222] };

function heroCursor(t) {
  const target = toPage(HERO.poke);
  const enter = arrive((t - 2.5) / 1.0);
  const leave = seg(t, 5.6, 6.6) ** 1.6;
  const from = { x: HERO.w + 40, y: HERO.h + 30 };
  const exit = { x: HERO.w + 60, y: 90 };
  let x = from.x + (target.x - from.x) * enter;
  let y = from.y + (target.y - from.y) * enter;
  x += (exit.x - target.x) * leave;
  y += (exit.y - target.y) * leave;
  const press = t >= 3.86 && t < 3.98;
  return { x, y, o: t > 2.5 && t < 6.7 ? 1 : 0, s: press ? 0.86 : 1 };
}

function heroLook(t) {
  const glance = 50 - 34 * (seg(t, 0.5, 1.0) - seg(t, 2.1, 2.5));
  const c = heroCursor(t);
  const center = HERO.mascot.left + HERO.mascot.w / 2;
  const follow = 50 + 50 * Math.max(-1, Math.min(1, (c.x - center) / 170));
  const w = seg(t, 2.5, 2.9) * (1 - seg(t, 6.3, 7.1));
  return glance + (follow - glance) * w;
}

function toPage([ax, ay]) {
  const m = HERO.mascot;
  return { x: m.left + (ax / 320) * m.w, y: m.top + (ay / 300) * m.h };
}

// ---------------------------------------------------------------- the page
const CURSOR = `<svg class="cursor" viewBox="0 0 24 24"><path d="M5 3l14 8-6 1.6L10 19z" fill="#1F1C19" stroke="#FBF8F2" stroke-width="1.6" stroke-linejoin="round"/></svg>`;

const RUNTIME = (rivs) => `<script type="module">
  import RiveCanvas from '/node_modules/@rive-app/canvas-advanced/canvas_advanced.mjs';
  const rive = await RiveCanvas({ locateFile: () => '/node_modules/@rive-app/canvas-advanced/rive.wasm' });
  const typed = (inp) => inp.type === rive.SMIInput.bool ? inp.asBool() : inp.type === rive.SMIInput.number ? inp.asNumber() : inp.asTrigger();
  window.cells = await Promise.all(${JSON.stringify(rivs)}.map(async (url, i) => {
    const canvas = document.getElementById('c' + i);
    const renderer = rive.makeRenderer(canvas);
    const file = await rive.load(new Uint8Array(await (await fetch(url)).arrayBuffer()));
    const artboard = file.defaultArtboard();
    const sm = new rive.StateMachineInstance(artboard.stateMachineByIndex(0), artboard);
    const inputs = {};
    for (let k = 0; k < sm.inputCount(); k++) { const inp = sm.input(k); inputs[inp.name] = typed(inp); }
    return { canvas, renderer, artboard, sm, inputs };
  }));
  window.step = (i, dt, actions) => {
    const c = window.cells[i];
    for (const a of actions) {
      if (a.set) { if (!(a.set[0] in c.inputs)) throw new Error('no input ' + a.set[0]); c.inputs[a.set[0]].value = a.set[1]; }
      if (a.fire) { if (!(a.fire in c.inputs)) throw new Error('no input ' + a.fire); c.inputs[a.fire].fire(); }
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
  window.ready = true;
</script>`;

const BASE_CSS = (th) => `
  html,body{margin:0;background:${th.page};-webkit-font-smoothing:antialiased}
  canvas{position:absolute}
  .cursor{position:absolute;left:0;top:0;width:24px;height:24px;pointer-events:none;opacity:0;transform-origin:5px 3px}
  .chip{position:absolute;left:14px;bottom:13px;display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:8px;
    corner-shape:superellipse(1.6);background:${th.chip};color:${th.muted};
    font:600 10.5px/1 ui-monospace,"SF Mono",SFMono-Regular,Menlo,monospace;letter-spacing:.02em;font-variant-numeric:tabular-nums;white-space:pre}
  .chip i{width:6px;height:6px;border-radius:50%;background:${th.dot}}
  .chip.hot i{background:${HOT}}`;

function recipesPage(th) {
  const size = 216, gap = 14, cols = 4;
  const names = Object.keys(RECIPES);
  return {
    width: cols * size + (cols - 1) * gap,
    height: 2 * size + gap,
    rivs: names.map(riv),
    html: `<!doctype html><html><head><meta charset="utf-8"><link rel="icon" href="data:,"><style>${BASE_CSS(th)}
  .board{display:grid;grid-template-columns:repeat(${cols},${size}px);gap:${gap}px;width:max-content}
  .cell{position:relative;width:${size}px;height:${size}px;border-radius:30px;corner-shape:superellipse(1.6);overflow:hidden;background:${th.cell}}
  .cell canvas{inset:10px 10px 30px 10px;width:${size - 20}px;height:${size - 40}px}
</style></head><body><div class="board" id="stage">${names.map((n, i) => `<div class="cell" id="cell${i}">
  <canvas id="c${i}" width="${(size - 20) * 2}" height="${(size - 40) * 2}"></canvas>
  <div class="chip" id="chip${i}" style="display:none"><i></i><span></span></div>${RECIPES[n].cursor ? CURSOR.replace('class="cursor"', `class="cursor" id="cur${i}"`) : ''}
</div>`).join('')}</div>${RUNTIME(names.map(riv))}</body></html>`,
  };
}

function heroPage(th, scale = 1, height = HERO.h * scale) {
  const m = HERO.mascot;
  return {
    width: HERO.w * scale,
    height,
    rivs: [riv('living-mascot')],
    html: `<!doctype html><html><head><meta charset="utf-8"><link rel="icon" href="data:,"><style>${BASE_CSS(th)}
  #stage{position:relative;width:${HERO.w * scale}px;height:${height}px;overflow:hidden}
  #hero{position:absolute;left:0;top:${(height - HERO.h * scale) / 2}px;width:${HERO.w}px;height:${HERO.h}px;transform:scale(${scale});transform-origin:0 0}
  h1{position:absolute;left:64px;top:104px;margin:0;color:${th.ink};font:700 76px/1 "Helvetica Neue",Helvetica,Arial,sans-serif;
    letter-spacing:-.045em;display:flex;align-items:flex-end;gap:7px}
  h1 b{display:block;width:15px;height:15px;margin-bottom:9px;border-radius:5px;corner-shape:superellipse(1.6);background:${HOT}}
  p{position:absolute;left:66px;top:200px;margin:0;color:${th.muted};font:500 13px/1 ui-monospace,"SF Mono",Menlo,monospace;letter-spacing:.06em}
  #c0{left:${m.left}px;top:${m.top}px;width:${m.w}px;height:${m.h}px}
</style></head><body><div id="stage"><div id="hero"><h1>rive-animator<b></b></h1><p>.riv · rml · state machines</p>
  <canvas id="c0" width="${m.w * 2 * scale}" height="${m.h * 2 * scale}"></canvas>${CURSOR.replace('class="cursor"', 'class="cursor" id="cur0"')}
</div></div>${RUNTIME([riv('living-mascot')])}</body></html>`,
  };
}

function riv(name) {
  return `/examples/${name}/build/${name}.riv`;
}

// ---------------------------------------------------------------- per-frame plans
const INITIAL = {};
function readInitials(name) {
  const rml = readFileSync(join(ROOT, 'examples', name, 'scene.rml'), 'utf8');
  for (const m of rml.matchAll(/<StateMachine(Bool|Number)\b([^>]*)>/g)) {
    const attr = (key) => m[2].match(new RegExp(`\\b${key}="([^"]*)"`))?.[1];
    const raw = attr('value') ?? (m[1] === 'Bool' ? 'false' : '0');
    INITIAL[`${name}:${attr('name')}`] = m[1] === 'Bool' ? raw === 'true' : Number(raw);
  }
}

function recipeFrame(name, i, t, dt) {
  const r = RECIPES[name];
  const events = r.events || [];
  const actions = events.filter((e) => e.t >= t && e.t < t + dt).map(({ t: _, ...a }) => a);
  let chip = null;
  if (r.input) {
    const v = r.value(t);
    actions.push({ set: [r.input, v] });
    const moving = Math.abs(r.value(t + dt) - v) > 0.01;
    chip = { text: `${r.input} ${String(Math.round(v)).padStart(3, ' ')}`, hot: moving };
  } else {
    const sets = events.filter((e) => e.set);
    const label = r.chip || sets[0]?.set[0] || events.find((e) => e.fire)?.fire;
    if (label) {
      const recent = events.some((e) => (e.set?.[0] === label || e.fire === label || e.click) && t >= e.t && t < e.t + 0.3);
      if (sets.some((e) => e.set[0] === label)) {
        const past = sets.filter((e) => e.set[0] === label && e.t <= t);
        const start = r.preroll?.[0] === label ? r.preroll[1] : INITIAL[`${name}:${label}`];
        const v = past.length ? past[past.length - 1].set[1] : start;
        chip = { text: `${label} ${v}`, hot: recent };
      } else chip = { text: label, hot: recent };
    }
  }
  let cursor = null;
  if (r.cursor) {
    const clicks = events.filter((e) => e.click);
    const k = arrive((t - (clicks[0].t - 0.6)) / 0.5);
    const out = seg(t, clicks[clicks.length - 1].t + 0.45, clicks[clicks.length - 1].t + 1.15) ** 1.6;
    const press = clicks.some((e) => t >= e.t - 0.04 && t < e.t + 0.1);
    // artboard (240x160) to cell css: the canvas is 196x176 at (10,10), fit contain
    const s = Math.min(196 / 240, 176 / 160), ox = 10 + (196 - 240 * s) / 2, oy = 10 + (176 - 160 * s) / 2;
    const x = ox + r.cursor[0] * s, y = oy + r.cursor[1] * s;
    // it enters from beyond the cell's edge already moving, and leaves past it (the cell clips it)
    cursor = { x: x + 150 * (1 - k) + 160 * out, y: y + 150 * (1 - k) + 160 * out, o: 1, s: press ? 0.86 : 1 };
  }
  return { i, dt, actions, chip, cursor };
}

function heroFrame(t, dt) {
  const actions = [{ set: ['lookX', heroLook(t)] }];
  if (t <= 3.9 && t + dt > 3.9) actions.push({ click: HERO.poke });
  return { i: 0, dt, actions, chip: null, cursor: heroCursor(t) };
}

// ---------------------------------------------------------------- recording
const MIME = { '.html': 'text/html', '.mjs': 'text/javascript', '.js': 'text/javascript',
  '.wasm': 'application/wasm', '.riv': 'application/octet-stream' };

function serve(pages) {
  const server = createServer((req, res) => {
    const url = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (pages[url]) { res.writeHead(200, { 'Content-Type': 'text/html' }).end(pages[url].html); return; }
    const path = normalize(join(ROOT, url));
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

async function record(browser, base, pages, key, { seconds, frame, preroll = [], out, still, sheet }) {
  const spec = pages[key];
  const page = await browser.newPage();
  await page.setViewport({ width: spec.width, height: spec.height, deviceScaleFactor: 2 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  const tmp = mkdtempSync(join(tmpdir(), 'rive-gif-'));
  try {
    await page.goto(`${base}${key}`, { waitUntil: 'load' });
    await page.waitForFunction('window.ready === true', { timeout: 20000 }).catch(() => {
      throw new Error(`runtime did not load: ${errors.join(' | ') || 'timeout'}`);
    });
    await page.evaluate((pre) => pre.forEach(({ i, actions }) => {
      window.step(i, 0, actions);
      for (let k = 0; k < 60; k++) window.step(i, 1 / 60, []);
    }), preroll);
    const dt = 1 / FPS;
    const count = Math.round(seconds * FPS);
    const stage = await page.$('#stage');
    for (let f = 0; f < count; f += 1) {
      const t = f * dt;
      await page.evaluate((cells) => cells.forEach((c) => {
        window.step(c.i, c.dt, c.actions);
        const chip = document.getElementById('chip' + c.i);
        if (chip && c.chip) {
          chip.style.display = 'flex';
          chip.querySelector('span').textContent = c.chip.text;
          chip.classList.toggle('hot', c.chip.hot);
        }
        const cur = document.getElementById('cur' + c.i);
        if (cur && c.cursor) {
          cur.style.opacity = c.cursor.o;
          cur.style.transform = `translate(${c.cursor.x - 5}px, ${c.cursor.y - 3}px) scale(${c.cursor.s})`;
        }
      }), frame(t, f === 0 ? 0 : dt));
      if (errors.length) throw new Error(errors.join(' | '));
      if (!out && f !== still) continue;
      const png = join(tmp, `f-${String(f).padStart(4, '0')}.png`);
      await stage.screenshot({ path: png });
      if (f === still) writeFileSync(join(ASSETS, 'social.png'), readFileSync(png));
    }
    if (!out) return;
    execFileSync('ffmpeg', [
      '-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', join(tmp, 'f-%04d.png'),
      '-vf', `scale=${spec.width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160:stats_mode=diff[p];` +
        '[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle',
      '-loop', '0', out,
    ], { stdio: ['ignore', 'pipe', 'pipe'] });
    if (sheet) {
      mkdirSync(join(ROOT, 'build', 'sheets'), { recursive: true });
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', out, '-vf',
        `fps=5,scale=${Math.round(spec.width / 2.5)}:-1,tile=5x${Math.ceil((seconds * 5) / 5)}`, '-frames:v', '1',
        join(ROOT, 'build', 'sheets', out.split('/').pop().replace('.gif', '.png'))]);
    }
    const kb = Math.round(statSync(out).size / 1024);
    console.log(`  ${out.slice(ROOT.length + 1).padEnd(26)} ${String(count).padStart(3)} frames  ${spec.width}x${spec.height}  ${kb} KB`);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
    await page.close();
  }
}

async function main() {
  const args = process.argv.slice(2);
  const sheet = args.includes('--sheet');
  const only = args.find((a) => !a.startsWith('--'));
  if (only && !['hero', 'recipes'].includes(only)) throw new Error(`unknown target ${only}; use hero or recipes`);
  for (const name of [...Object.keys(RECIPES), 'living-mascot']) {
    if (!existsSync(join(ROOT, riv(name)))) throw new Error(`missing ${riv(name)}; run npm run build:examples`);
    readInitials(name);
  }
  const pages = {};
  for (const [theme, th] of Object.entries(THEMES)) {
    pages[`/recipes-${theme}.html`] = recipesPage(th);
    pages[`/hero-${theme}.html`] = heroPage(th);
  }
  pages['/social.html'] = heroPage(THEMES.light, 4 / 3, 640);   // GitHub's social preview is 1280x640

  const executablePath = resolveChrome();
  if (!executablePath) throw new Error('no Chrome found; set CHROME_PATH');
  const server = await serve(pages);
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await puppeteer.launch({ executablePath, headless: 'shell', args: ['--force-color-profile=srgb'] });
  const names = Object.keys(RECIPES);
  try {
    for (const theme of Object.keys(THEMES)) {
      const suffix = theme === 'dark' ? '-dark' : '';
      if (!only || only === 'hero') {
        await record(browser, base, pages, `/hero-${theme}.html`, {
          seconds: HERO_SECONDS, frame: (t, dt) => [heroFrame(t, dt)], out: join(ASSETS, `hero${suffix}.gif`), sheet,
        });
      }
      if (!only || only === 'recipes') {
        await record(browser, base, pages, `/recipes-${theme}.html`, {
          seconds: RECIPE_SECONDS,
          // settle a cell into its starting state before frame 0, so the loop's first frame is its last
          preroll: names.flatMap((n, i) => (RECIPES[n].preroll ? [{ i, actions: [{ set: RECIPES[n].preroll }] }] : [])),
          frame: (t, dt) => names.map((n, i) => recipeFrame(n, i, t, dt)),
          out: join(ASSETS, `recipes${suffix}.gif`), sheet,
        });
      }
    }
    if (!only || only === 'hero') {
      // the social card is the moment it glances at its own name
      await record(browser, base, pages, '/social.html', {
        seconds: 1.4, frame: (t, dt) => [heroFrame(t, dt)], still: Math.round(1.3 * FPS),
      });
      console.log('  assets/social.png');
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
