# ep01《醒来在 2055》· 分镜剧本 v3（按短剧剧本 v2.0 重做）

> 2026-09-11 ｜ **源：`screenplay/ep01.md` v2.0**（旧 v2 分镜按旧剧情，已不适用）
> 竖屏 9:16 · KLEIN fp8 首帧（832×1216）· H3 图生视频 · 帧数 `length = 124 + 17k`
> 视觉规格：沿 `visual-spec-lock.md`（暖调清洁配方 + 负向词 + 竖屏约束），**一处不改**

---

## ⚠️ 开工前必须先定的两件事

### ① 陆远形象模板（P0 · 影响全部已出素材）

现有生产线模板（`gen_ep01_frames_v2.py` L8）写的是：

```
a 32-year-old slightly heavyset Chinese man, ...
```

**"slightly heavyset" 与角色档案（30 岁 / 175cm / 62kg 偏瘦）冲突**——ep02–08 已产出的 111 镜全偏胖（见 memory 2026-09-10 已记录）。

**本文档采用的修正版模板**（待你确认）：

```
LY = a 30-year-old lean Chinese man, thin wiry build, short messy black hair,
     old black-frame glasses with a scratched left lens and taped temple,
     faded plaid shirt with frayed collar, dark work pants, oil-stained fingernails
```

> 改法建议：**先只改文字模板，不重做定妆**——`input/juese/luyuan/luyuan.png` 那张脸仍是一致性基准（图生图时以它为参考），文字模板只影响文生图时的体型。
> 若首帧仍偏胖 → 再用定妆图做一次图生图派生"偏瘦版基准"。

### ② 时长档次（内容量涨了，2 分钟装不下）

新剧本要装的是**完整第一天**（晨→夜）+ 手机线闭合 + 修设备 + 两种人对话。算完账：

| 版本 | 镜数 | 时长 | 取舍 |
|------|------|------|------|
| A · 压到 2 分钟 | 17 镜 | ~120s | **砍掉场 5（干粮"三种人"对话）**，配给点再压 1 镜 |
| **B · 标准版（本文档采用）** | **23 镜** | **~180s（3 分钟）** | 完整第一天，一个不砍 |

**我建议 B**——3 分钟在抖音短剧里是正常长度，而场 5 那句"城里只有三种人吃东西"是全季最锋利的台词之一，砍了可惜。**你定，砍不砍。**

---

## 一、必须先出的"锚点图"（先生成这 6 张，再出分镜首帧）

分镜首帧之间的一致性，靠这 6 张锚点撑住。**顺序不能颠倒**。

| # | 锚点 | 用途 | 提示词要点 |
|---|------|------|-----------|
| A1 | **废品收购站 · 场景锚点** ★新 | 场 4 全部 7 镜共用背景 | `a narrow alley corner piled with scrap: machine shells, sheet metal, half-dismantled fridge, stack of unknown-brand monitors, a plastic canopy overhead, vertical 9:16` |
| A2 | **那台旧设备 · 道具锚点** ★新 | 场 4/6 共 6 镜 | `a waist-high machine, rusted beyond original colour, flaking rust, a dusty control panel with a single lever, a dusty two-prong socket on its side, vertical framing` |
| A3 | **充电头 + 三孔圆口插座** ★新 | s01 钩子 / s21–22 | `extreme close-up: a 2026-era two-prong flat-pin charger held against a round three-hole wall socket, does not fit, worn bright copper prongs on a fingertip` |
| A4 | **2026 手机屏幕（2%）** ★关键 | s22 集尾 | `close-up of an old smartphone screen from 2026, an old-style interface, battery icon at 2%, warm screen glow on a man's face` |
| A5 | **旧设备的 2026 界面** ★新 | s15–16 | `a cracked screen showing a year-2026-era interface: old fonts, old icons, dim warm glow, dust on the glass` |
| A6 | **卖旧零件的摊主**（单场角色） | s05 | `a middle-aged Chinese man in an old jacket wiping a pile of screws with a rag, indifferent expression, street stall` |

> 角色一致性规则不变：含陆远的镜一律**图生图**（以 `input/juese/luyuan/luyuan.png` 为源），不重新文生图。

---

## 二、分镜表（23 镜 · 标准版 B）

| 镜号 | 场 | 内容 | 时长 | 帧数 | 台词 | 首帧 |
|------|-----|------|------|------|------|------|
| s01 | 1-晨·废弃屋 | 钩子·充电头怼三孔圆口，怼不进 | 5.9s | 141 | — | **重出**（A3） |
| s02 | 1-晨 | 蹲地碾铜脚·环境建立（纸箱板床/塑料布窗/手写"库存，勿动"） | 7.3s | 175 | V.O.① | 重出 |
| s03 | 2-街头 | 行人两侧绕过·被当噪音 | 7.3s | 175 | — | 重出 |
| s04 | 2-街头 | 大姐"让你的模型来问"·盯着眼镜走开 | 8.7s | 209 | 2 句 | 重出 |
| s05 | 2-街头 | 卖旧零件摊主"你没登记吧？去配给点" | 10.8s | 260 | 3 句 | **新**（A6） |
| s06 | 3-配给点 | 长队·前排腕上一闪闸机放行·他看自己的手腕 | 7.3s | 175 | — | 重出（竖屏） |
| s07 | 3-配给点 | 核验失败 | 8.7s | 209 | 2 句 | 重出 |
| s08 | 3-配给点 | 登记／预约死循环 | 10.8s | 260 | 4 句 | 重出 |
| s09 | 3-配给点 | 方案 A 与 B | 10.8s | 260 | 3 句 | 重出 |
| s10 | 3-配给点 | "哪部分经历"→"全部" | 8.7s | 209 | 2 句 | **新** |
| s11 | 3-配给点 | "记忆是经历的存储形式"＋"你们让我把家卖了"＋"系统不评价方案" | 13.0s | 311 | 4 句 | **新** |
| s12 | 3-配给点 | 街边·逆光·攥着充电头 | 7.3s | 175 | V.O.② | 重出 |
| s13 | 4-废品站 | 巷子口·废品堆成小山（空间建立） | 5.9s | 141 | — | **新**（A1） |
| **s14** | 4-废品站 | **无所事事缓冲段：坐下来·太阳漏在鞋上·蹭鞋·苍蝇** ★ | 10.8s | 260 | — | **新**（A1） |
| s15 | 4-废品站 | 手闲拨锈·拨开锈皮·露出面板与拨杆 | 8.7s | 209 | — | **新**（A2） |
| s16 | 4-废品站 | 拨了一下·"嗡"—设备开机·2026 界面 | 8.0s | 192 | — | **新**（A2） |
| s17 | 4-废品站 | 屏幕光映脸·V.O."跟我一样，没人要了" | 8.7s | 209 | V.O.③ | **新** |
| s18 | 4-废品站 | 老头两步外"你……怎么修好的"／"一个开关的事" | 12.3s | 294 | 3 句 | **新** |
| s19 | 4-废品站 | "怎么知道拨这儿"／"先拨拨看"＋塞干粮硬币 | 12.3s | 294 | 4 句 | **新** |
| s20 | 4-废品站 | "别往新城区说"／"它们不爱听这个" | 12.3s | 294 | 3 句 | 新 |
| s21 | 5-暮·巷口 | 干粮·"旧人靠吃饭活着"／"三种人"／"你猜" | 12.3s | 294 | 4 句 | **新** |
| s22 | 6-夜·废品站 | 走两步·摸到兜里的充电头·走回来蹲下 | 8.7s | 209 | V.O.④ | **新**（A2） |
| s23 | 6-夜 | 电源口特写·两脚扁插·插上 | 8.7s | 209 | V.O.⑤ | **新**（A2/A3） |
| s24 | 6-夜 | **手机亮起 2%** ★集尾 | 8.0s | 192 | — | **新**（A4） |
| s25 | 6-夜 | 设备屏幕又亮一下·电流变了·他抬头 | 7.3s | 175 | V.O.⑥ | **新**（A5） |

**合计 25 镜 · 约 197 秒。** 若取版本 A（2 分钟）：砍 s21，并把 s08/s09 合成一镜、s18/s19 合成一镜 → 17 镜 ~120s。

> 注：这里 25 镜比前面估的 23 多了 2 镜（s20 单独立起来 + s24/s25 拆开），因为**集尾那两镜必须分开**——"手机亮"和"设备又亮一下"是两个独立信息点，合在一起观众会漏掉钩子。

---

## 三、台词分配（关键镜 · 按秒）

**s05 · 你没登记吧（10.8s）**
- 0.3–2.5s 快切两下（第一个摊主摆手 / 第二个连头都没抬）
- 3.0–6.0s 摊主：`你没登记吧。`
- 6.2–7.6s 陆远：`……怎么登记？`
- 7.8–10.8s 摊主：`去配给点。无证人员有救助配额。先去领上，不然你连今天都过不去。`

**s10 · 哪部分经历（8.7s）**
- 0.5–2.0s 陆远：`……哪部分经历。`
- 2.2–3.6s 合成音：`全部。`
- 3.8–5.4s 陆远：`包括我记得的东西。`
- 5.6–8.7s 合成音：`记忆是经历的存储形式。`（沉默 2s）

**s11 · 把家卖了（13.0s）**
- 0.5–3.5s 陆远（低声）：`……你们让我把家卖了。`
- 3.7–6.3s 合成音：`系统不评价方案，只提供方案。`
- 6.3–13.0s 身后人流涌上，把他挤出窗口（无台词，纯画面）

**s14 · 无所事事（10.8s · 无台词）** ★本集最重要的一镜
- 0–4s 他坐下来，没干什么，就是坐着
- 4–7s 太阳从塑料棚破洞漏下来，落在鞋上；他把鞋在地上蹭了蹭
- 7–10.8s 一只苍蝇在转；他坐了很久
- **音效**：远处市声、风、塑料布响——**不要音乐**

**s21 · 三种人（12.3s）**
- 0.5–2.2s 年轻人：`好吃吗。`
- 2.4–4.0s 陆远：`能咽下去。`
- 4.2–7.0s 年轻人：`那你还吃。一接，什么都有。何必费这个劲。`
- 7.2–9.0s 陆远：`我是旧人。旧人靠吃饭活着。`
- 9.2–12.3s 年轻人：`城里只有三种人吃东西。有钱人，要死的人，和不在系统里的人。你是哪种。`
- （"你猜"留给下一镜的尾巴或直接删——**建议删**，用陆远嚼干粮的沉默收尾更狠）

**s24–s25 · 集尾（15.3s）**
- s24：手机亮起，右上角 **2%**。他盯着看，不动。（无台词）
- s25：设备屏幕又亮一下，很轻的一声。他抬头。
- V.O.⑥（极低）：`……不是放电。` → 黑场。

---

## 四、首帧提示词（KLEIN · 直接可喂）

**基底（每镜必带，与 `visual-spec-lock.md` §4 完全一致）**

```
WARM = photorealistic, 35mm full-frame cinematic still, warm tungsten key light,
       amber highlights, clean warm shadows, natural skin with warm undertone,
       sharp focus, crisp detail, high clarity, clean image,
       shallow depth of field, 180-degree shutter, vertical 9:16 composition
LY   = a 30-year-old lean Chinese man, thin wiry build, short messy black hair,
       old black-frame glasses with a scratched left lens and taped temple,
       faded plaid shirt with frayed collar, dark work pants, oil-stained fingernails
NEG  = （沿用 visual-spec-lock §4.3 全文，含竖屏负向词 letterbox / black bars /
        widescreen crop / horizontal panorama）
```

**逐镜提示词（新增/改动镜）**

| 镜 | 提示词 |
|----|--------|
| s01 | `extreme close-up of a hand holding a 2026-era two-prong flat-pin charger against a round three-hole wall socket, the plug does not fit, worn bright copper prongs under a fingertip, faint dawn light through plastic sheeting, {WARM}` |
| s02 | `medium shot of {LY} crouching under a socket in a bare room, cardboard sheets for a bed, plastic sheeting over the window, a handwritten note on the cardboard reading stock do not move, {WARM}` |
| s05 | `medium two-shot on a street stall: {LY} standing with a black phone in hand, before him a middle-aged man in an old jacket wiping a pile of screws with a rag, indifferent, warm afternoon sunlight, hard key from side, {WARM}` |
| s13 | `a narrow alley corner piled with scrap forming a small hill: machine shells, sheet metal, a half-dismantled fridge, a stack of unknown-brand monitors, a torn plastic canopy overhead, vertical framing, warm afternoon sunlight, dust in light beam, {WARM}` |
| s14 | `wide-medium shot: {LY} sitting on the ground beside a hill of scrap, doing nothing, a shaft of sunlight through a hole in the plastic canopy falling on his shoes, one fly in the air, vertical framing, warm afternoon light, {WARM}` |
| s15 | `close-up of a hand brushing flaking rust off a waist-high machine, revealing a dusty control panel with a single lever, warm side light, shallow depth of field, {WARM}` |
| s16 | `medium shot: {LY} crouching as a rusted machine's screen flickers on, an old year-2026-style interface glowing, his face lit from below by the screen, vertical framing, {WARM}` |
| s17 | `close-up of {LY} facing the camera, screen glow on his glasses, his expression blank and still, dust in the air, vertical framing, {WARM}` |
| s18 | `medium two-shot at golden hour beside a hill of scrap: {LY} crouching by the machine, a thin elderly man in a worn jacket standing two steps away, neither moving, backlit, warm haze, vertical framing, {WARM}` |
| s19 | `extreme close-up: a weathered elderly hand pressing a small bundle of dry rations and two worn coins into a younger man's open palm, golden hour warm light, shallow depth of field, {WARM}` |
| s22 | `medium shot at night in a scrapyard alley: {LY} stops mid-step, hand in pocket touching something, warm sodium street lamp rim light on his face, vertical framing, {WARM}` |
| s23 | `extreme close-up: a dusty two-prong socket on the side of a rusted machine, a 2026-era charger being pushed in, loose, wiggling, warm dim light, shallow depth of field, {WARM}` |
| s24 | `close-up of an old smartphone screen lighting up in the dark: an old-style interface from 2026, battery icon showing 2%, the glow on a man's face and glasses, vertical framing, {WARM}` |
| s25 | `medium shot: a rusted machine's screen flickers once more in the dark alley, a man lifting his head toward it, sodium lamp rim light, vertical framing, {WARM}` |

> 其余镜（s03/s04/s06/s07/s08/s09/s12/s20/s21）画面结构沿用旧分镜 v2 的构图，**只把 `LY` 段落换成偏瘦版、并把竖屏约束确认到位**即可。

---

## 五、生产顺序（照这个走，别跳）

```
① 定形象模板（偏瘦版）      ← 待你确认
② 出 6 张锚点图（A1–A6）    ← 废品站 / 旧设备 / 充电头 / 手机2% / 2026界面 / 摊主
③ 出 25 张首帧（含陆远的走图生图）
④ 逐镜 H3 图生视频（帧数见分镜表）
⑤ 配音：V.O.6 句 + 全部对白 + 系统女声（合成）
⑥ 剪辑：竖屏 9:16 · 字幕 · 音效（s14 不要音乐）· 集尾黑场
```

**AI 视频的现实约束（已按此设计分镜）**：
- **口型别硬做**——所有对白镜都用"画外／不抬头／背身／反应镜"处理（s05 摊主低头擦螺丝、s07–s11 系统女声是画外、s18–s20 老头可侧背）
- **静默镜是本集的宝**（s14 无所事事）——AI 视频最擅长的就是"有微动的静止"，一只苍蝇、一道光斑、蹭一下鞋就够撑 10 秒
- **每个镜头 ≤ 13s**（含台词者），超出即拆

---

## 六、出图进度（Seedream 5.0 Pro · 全部走付费线）

> **2026-09-11 作者定：弃用本地 KLEIN（质量不达标），ep01 起全部走 Seedream 付费生图。**
> 脚本：`.workbuddy/scripts/seedream_batch.py`（`python seedream_batch.py s01 s13 …` ／ `all`）
> 输出：`releases/2026-09-12_ep01分镜图/` ｜ 尺寸锁定 **1152×2048（9:16）** ｜ 实测 **38–76 秒/张**

### ✅ 已出（6 张 · 锚点齐 + 2 个关键镜）

| 文件 | 对应镜 | 说明 |
|------|--------|------|
| `A3_充电头怼三孔圆口.png` | **s01** | 全集第一帧钩子；同时是 A3 锚点 |
| `A1_废品收购站场景.png` | **s13** | A1 场景锚点（场 4 全部镜共用此背景） |
| `A2_锈迹斑斑的旧设备.png` | **s15** | A2 道具锚点（含侧面两脚扁插电源口） |
| `A4_手机屏幕2%.png` | **s24** | A4 集尾回报（2% 电量）· 带陆远定妆参考 |
| `s17_屏幕光映脸.png` | s17 | 正脸镜 · 带定妆参考 |
| `s14_无所事事坐着.png` | **s14** | 全集最重要一镜（缓冲段）· 带定妆参考 |

### ⏳ 待出（19 镜）

s02 s03 s04 s05 s06 s07 s08 s09 s10 s11 s12 s16 s18 s19 s20 s21 s22 s23 s25

### 生成口径（出后续镜时照此）

1. **带角色正脸／多角色同框** → 传 `image` 参考图（`input/juese/<角色拼音>/<角色>.png`），提示词开头拼 `LY_REF` 段
2. **空镜／道具／场景** → 纯文生图
3. 参考图路径：陆远 `luyuan` / 赵满秋 `zhaomanqiu` / 老魏 `laowei` / 沈恪 `shenge` / 李叔 `lishu`
4. **无定妆的新角色**（卖旧零件的摊主、带营养泵的年轻人）→ 先出**一张**，定稿后**当该角色的基准图**，后续镜一律以它为 `image` 参考（防脸漂移）
5. 风格基底一律拼 `W`（暖调清洁配方，中英混写，含 `not desaturated, not gray, not cold`）
