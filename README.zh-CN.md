<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.gif">
  <img src="assets/hero.gif" alt="一个顶着嫩芽的珊瑚色小吉祥物在呼吸、眨眼，看向 rive-animator 字标；光标进入，它的眼睛跟随，点击后它下蹲、跳起、开心地落地，再目送光标离开" width="100%">
</picture>

上线之前就能正常工作、上线之后显得有生命的 Rive 文件。面向 AI 编程助手和开发者的代码优先工具包：九个在真实运行时中录制的示例、动作烘焙器、SVG 与 Lottie 转换器、专抓“编译通过却出错”问题的检查器，以及八个平台的可复制接入代码。

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-black)](https://code.claude.com/docs)
[![Antigravity](https://img.shields.io/badge/Antigravity-Skill-black)](https://antigravity.google)
[![Rive](https://img.shields.io/badge/Rive-Format_7.3-black)](https://rive.app)
[![Tests](https://img.shields.io/badge/tests-25_passed-black)](tests/)

[English](README.md) · [Español](README.es.md) · 中文

</div>

## 为什么

`.riv` 是编译后的程序，不是图片，出错时一声不吭。它能编译、能加载，却带着没人读取的输入、回不去的状态、一下子跳过去的姿势、在循环接缝处跳动的动画，或者用角度写的旋转（结果转了五十七圈）。又或者它能用，却毫无生气：所有部件同步运动，每个姿势都戛然而止，颜色直接切换而不是过渡，动作之间什么都不呼吸。

`rive-animator` 在你接触生产代码之前用检查器抓住大部分第一类问题，其余的靠渲染发现（回不去的状态只有点两次才看得出），并给你的 AI 助手一套解决第二类问题的方法。

## 示例

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/recipes-dark.gif">
  <img src="assets/recipes.gif" alt="八个由输入驱动的 Rive 组件：开关、带火花的点赞爱心、成功对勾、满 100 变绿的进度环、摆动的铃铛、旋转并填充的星星、均衡器和加载圈" width="100%">
</picture>

上面每一帧都是真实的 `@rive-app/canvas-advanced` 运行时，由脚本化的输入驱动；角落的标签显示应用设置的输入值。

| 示例 | 输入 | 演示内容 |
|---|---|---|
| [活力吉祥物](examples/living-mascot/build.py) | `lookX` 数值，`poke` 触发器 | 四层同时运行：呼吸、眨眼、视线混合、带挤压拉伸与跟随动作的跳跃 |
| [开关](examples/toggle-switch/scene.rml) | `tap` 触发器，点击监听 | 姿势状态间 240 ms 混合；圆钮随行程拉伸 |
| [点赞按钮](examples/like-heart/scene.rml) | `liked` 布尔 | 一条 `flow` 完成预备、弹出与回落；种子化火花；更快的退出 |
| [成功对勾](examples/success-check/scene.rml) | `fire` 触发器 | 从 0.92 缩放带透明度进入，对勾描绘出现；再次触发回到静止 |
| [进度环](examples/progress-ring/scene.rml) | `progress` 数值，0–100 | 数值驱动混合状态；完成是独立的一层 |
| [标签栏铃铛](examples/tab-bar-item/scene.rml) | `active` 布尔，`tap` 触发器 | 绕铰链摆动，铃舌稍晚一拍跟随 |
| [评分星星](examples/rating-star/scene.rml) | `rating` 数值 | 从描边到填充，72° 旋转永不回退，尖端迸出火花 |
| [音频均衡器](examples/audio-equalizer/scene.rml) | `isPlaying` 布尔 | 五根柱子各自叠加种子化的波形，永不同步 |
| [加载圈](examples/spinner-loader/scene.rml) | 无 | 裁切追逐动画，三个周期闭合循环 |

## 让它活起来

动作方法来自 [rossark-motion-skill](https://github.com/rossark0/rossark-motion-skill)，翻译为 RML 后写在 [references/living-motion.md](references/living-motion.md)：不瞬移、在两条强曲线上使用小幅度、部件绕真实支点旋转、用延迟而不是弹簧实现跟随、种子化的变化、一个主要动作加上永不停止的待机循环。

Rive 对每段关键帧单独缓动，所以一串姿势会在每个关键帧处停住。`scripts/motion_keys.py` 解决了这个问题：`flow` 经过每个姿势而不停顿、不过冲，并写成精确的 `cubicValue` Hermite 段（与渲染器对比误差在四分之一像素内）；`bake` 把呼吸、摆动和跟随动作变成可无缝循环的关键帧。

```bash
python3 scripts/motion_keys.py flow 0:1 9:0.86 15:1.1 44:0.8 52:1.04 76:1   # 下蹲、拉伸、挤压、回落
python3 scripts/motion_keys.py track 0:1 7:0.1 9:0.1 20:1:out               # 一次眨眼：7 / 2 / 11 帧
python3 scripts/motion_keys.py wave --base 1 --amp 0.016 --period 120 --length 240
```

## 可以这样问你的助手

| 你说 | 会发生什么 |
|---|---|
| *“用 Rive 做一个会呼吸、会眨眼、点击会跳的吉祥物”* | 从 `living-mascot` 开始，所有数值放在 tokens 里，完成前先看联系表 |
| *“这个开关在状态之间直接跳”* | 检查 `RML012`，为姿势过渡加上混合，让颜色过渡 |
| *“把这个 SVG 标志转成可交互的 Rive 画板”* | 运行 `svg2rml.py`，添加状态机，用 Rive CLI 验证 |
| *“我的 Rive 动画能显示但不响应点击”* | 运行 `rive_lint.py`，找出缺失的监听器或无效输入，打印准确的接入代码 |
| *“给我 mascot.riv 的 Flutter 接入代码”* | `rive_lint.py mascot.riv -f flutter` |

## 工具链

Python 3.8+，仅用标准库。

| 脚本 | 作用 |
|---|---|
| `scripts/motion_keys.py` | 把 `track`、`flow`、`wave` 通道烘焙成 RML 关键帧 |
| `scripts/rml_lint.py` | 预检：角度、颜色关键帧、无效输入、跳到姿势、循环接缝 |
| `scripts/rive_lint.py` | 读取 `.riv`：画板、状态机、输入、监听器、缺陷，以及 8 个平台的接入代码 |
| `scripts/svg2rml.py` / `lottie2rml.py` | SVG 或 Lottie 转 RML，使用分离式三次贝塞尔顶点 |
| `scripts/make-gifs.mjs` | 在真实运行时中以 50 fps 录制 README 图片，无缝循环，浅色与深色 |

接入：React（`@rive-app/react-canvas`）、Vue 3、Svelte、原生 Web Canvas、Flutter、SwiftUI、Android Kotlin、React Native。详见 [references/universal-framework-wiring.md](references/universal-framework-wiring.md)。

## 缺陷清单

| 代码 | 发现 | 修复 |
|---|---|---|
| `RML011` | 声明了却没有任何条件、监听器或混合读取的输入 | 接上它，或删除 |
| `RML012` | 过渡到单帧姿势却没有混合：会直接跳 | `duration="160"`–`"300"` 加三次插值器 |
| `RML013` | `loop` 的最后一个关键帧不等于第一个：接缝处会跳 | 闭合循环，或使用 `pingPong` |
| `RML004` | 旋转用了角度 | 用弧度：一整圈是 `6.2831853` |
| `RML007` / `RML008` | 没有颜料的填充；颜色属性上用了 double 关键帧 | 添加 `<SolidColor>`；使用 `KeyFrameColor` |
| `RV001`–`RV012` | 二进制缺陷：文件截断、无画板、0×0、无层、输入名重复或带空格 | 见 [references/defect-ledger.md](references/defect-ledger.md) |

## 安装

```bash
claude plugin add obeskay/rive-animator-skill                                            # Claude Code
git clone https://github.com/obeskay/rive-animator-skill.git ~/.gemini/config/skills/rive-animator   # Antigravity
```

参与开发：

```bash
git clone https://github.com/obeskay/rive-animator-skill.git && cd rive-animator-skill
npm install && npm test
npm run build:examples && npm run gifs   # 需要 Rive CLI、ffmpeg 和 Chrome
```

## 许可证

MIT © [ov (obeskay)](https://github.com/obeskay)。动作方法致谢 [rossark0/rossark-motion-skill](https://github.com/rossark0/rossark-motion-skill)（MIT）。
