import fs from 'node:fs'

const OUT = process.argv[2] || 'assets/build'

const V = {
  en: {
    tag: 'Interactive vector runtimes that actually react before they ship',
    foot: 'code-first state machines · zero-dependency svg converter · universal runtime wiring',
  },
  es: {
    tag: 'Runtimes vectoriales interactivos que sí reaccionan antes de desplegar',
    foot: 'máquinas de estado code-first · conversor svg sin dependencias · wiring universal',
  },
  zh: {
    tag: '真正具备交互响应能力的代码优先 Rive 矢量运行时引擎',
    foot: '代码优先状态机 · 零依赖 SVG 转换器 · 8大平台运行时代码直出',
  },
}

const page = (lang, w, h) => {
  const v = V[lang]
  const big = lang === 'zh' ? 88 : 96
  const cjk = lang === 'zh'
  return `<!doctype html><meta charset="utf-8"><style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:${w}px;height:${h}px;overflow:hidden}
  body{background:#08080a url("../artwork.jpg") center right/cover no-repeat;
       font-family:${cjk ? '"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC",' : ''}-apple-system,"Helvetica Neue",Arial,sans-serif;
       color:#f4f2ee;display:flex;align-items:center;position:relative}
  /* Scrim: subtle gradient so text is always ultra legible */
  body::before{content:"";position:absolute;inset:0;z-index:1;
    background:linear-gradient(90deg,#08080a 0%,rgba(8,8,10,.95) 42%,rgba(8,8,10,.72) 65%,rgba(8,8,10,.25) 85%,rgba(8,8,10,.35) 100%)}
  body::after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;z-index:3;background:rgba(255,255,255,.08)}
  .wrap{position:relative;z-index:2;padding:0 ${Math.round(w * 0.066)}px;width:100%}
  h1{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:${big}px;font-weight:700;
     letter-spacing:-.045em;line-height:.95;display:flex;align-items:flex-end;gap:${Math.round(big * 0.1)}px}
  .dot{width:${Math.round(big * 0.18)}px;height:${Math.round(big * 0.18)}px;background:#00d2ff;
       box-shadow:0 0 24px #00d2ff, 0 0 48px rgba(139,92,246,0.5);
       border-radius:4px;
       margin-bottom:${Math.round(big * 0.045)}px}
  .tag{margin-top:${Math.round(h * 0.055)}px;font-size:${cjk ? 25 : 26}px;font-weight:400;color:#c2bcb4;letter-spacing:${cjk ? '.005em' : '-.011em'};max-width:760px}
  .foot{margin-top:${Math.round(h * 0.075)}px;font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:14px;
        color:#00d2ff;opacity:0.85;letter-spacing:.04em}
</style>
<div class="wrap">
  <h1><span>rive-animator</span><span class="dot"></span></h1>
  <div class="tag">${v.tag}</div>
  <div class="foot">${v.foot}</div>
</div>`
}

fs.mkdirSync(OUT, { recursive: true })
for (const lang of ['en', 'es', 'zh']) {
  fs.writeFileSync(`${OUT}/banner-${lang}.html`, page(lang, 1200, 400))
}
fs.writeFileSync(`${OUT}/social.html`, page('en', 1280, 640))
console.log('banner html generated in ' + OUT)
