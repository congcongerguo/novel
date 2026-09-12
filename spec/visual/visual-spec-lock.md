# 视觉捕获规格锁 🔒 v1.0

> 建立日期：2026-09-08 ｜ 用户拍板：**按画面版原案 · 纪实暖调**
> 性质：全片统一视觉技术基线，**独立于语言风格锁**，一经锁定不得中途更改。
> 生效范围：全季 12 集所有分镜首帧、视频生成、角色派生图。
> 关联文档：`character-baseline.md`（角色一致性）｜ 各集 `epXX-director-cut.md`（画面版）
> 解锁条件：仅用户明确要求更换调性时方可修订，修订后所有已出画面版自动标记【待复核】。

---

## 一、核心结论（先看这条）

**本片是暖调，不是冷调。**

此前 ep01 十个镜头按"电影感冷调"生成，成品被判"灰不溜秋 / 完全没法用"。根因不是模型，是**规格锁被绕过**——画面版文档写的是暖调，执行提示词写的是冷调。本次锁定后，任何集、任何镜头的提示词都必须落在下面的暖调区间内。

**一句话判据**：画面里如果大面积出现"灰、蓝灰、青灰、低饱和水泥色"，即为违规，需重生成。

---

## 二、制作基线（写进每一集画面版头部）

| 项 | 锁定值 |
|----|--------|
| 视觉总纲 | 老城区烟火气 · 纪实暖调 · 旧物质感 · 制度场景冷视（仅局部） |
| 模拟摄影机体系 | 35mm 全画幅电影机（不写具体品牌，转译为下列可执行参数） |
| 镜头组与等效焦段 | 28mm 空间建立 / 35–50mm 常规对白 / 85mm 特写 · 微距用于手部与零件 |
| 画幅 / 帧率 / 快门 | 16:9（竖屏切片另出 9:16 二次构图）/ 24fps / 180°（1/48s）轻运动模糊 |
| 景深策略 | 浅景深 T2.0–T2.8，特写更浅；全景/空间建立用中景深保留环境信息 |
| 胶片 / 色彩模拟 | 轻胶片颗粒；暖棕基调（低饱和但**不灰**）；暗部暖褐不死黑；机油冷色仅作点缀 |
| 光色、颗粒、锐度、黑位 | 自然光优先（日间硬、黄昏软）；夜景用钨丝/白炽/路灯暖光源；锐度中等；黑位不压死，保留暗部暖色 |
| 运镜基线 | 手持微晃为主（生活流）；制度场景（配给点/均衡局/系统界面）固定机位冷视 |
| 运镜禁忌 | 无大航拍、无平滑长镜、无广角畸变滥用、无手持过度抖动 |
| 视觉规格偏离 | 仅梦境/回忆/监控/手机屏/主观视角可偏离，须写明偏离原因、影响范围、回归基线位置 |

## 三、语言风格锁 🔒

**白描 + 冷幽默**：短句、动作与物象优先、少形容词、不拟人、不炫术语、不煽情、不做主题句。
与视觉锁并行执行——画面不炫技，台词不点题。

---

## 四、AI 生成转译层（喂给模型用的，最关键的一节）

设备名和摄影术语不能单独当提示词，必须转译为可执行影像参数。以下为**所有分镜提示词的固定基底**。

### 4.1 正向基底（每镜必带）

```
photorealistic, 35mm full-frame cinematic still, warm tungsten key light,
amber highlights, clean warm shadows, natural skin with warm undertone,
sharp focus, crisp detail, high clarity, clean image,
shallow depth of field, 180-degree shutter
```

> **v1.1 修订（2026-09-08）**：首版基底含 `soft film grain` / `lifted blacks` / `muted earth-tone palette` / `medium sharpness`，实测导致画面"脏"（颗粒重、暗部浑、发闷）。已全部移除，改为清洁锐利配方。

### 4.1.1 步数建议（实测结论，勿凭直觉调）

KLEIN 9B 是蒸馏模型，4–8 步即可收敛，**但步数与"干净"无关**：

| 组合 | 平坦区噪声 | 暗部噪点 | 锐度 |
|------|-----------|---------|------|
| 12 步 + 脏配方 | 2.211 | 2.886 | 853 |
| 24 步 + 脏配方 | 2.329 | **3.422** | 924 |
| 24 步 + 清洁配方 | **1.373** | **2.511** | **940** |

**加步数会让脏配方更脏**（模型把 `film grain` 执行得更彻底）。因此：**只许在清洁配方下加步数，推荐 24 步。** 画面发脏时先查提示词，不要盲目加步数。

### 4.2 分场景光色微调

| 场景类型 | 追加词 |
|---------|--------|
| 日间外景（老城街/旧货巷） | `warm afternoon sunlight, hard key from side, dust in light beam` |
| 黄昏外景 | `golden hour backlight, long shadow, warm haze` |
| 铺内日间 | `single tungsten bulb overhead, warm pool of light on counter, darker warm corners` |
| 铺内夜景 | `warm incandescent practical lamp, cozy warm glow, deep warm shadows` |
| 巷口夜景 | `sodium street lamp warm orange, warm rim light on face` |
| 制度场景（配给点/均衡局/系统屏） | `neutral gray institutional interior, cool fluorescent fill, but keep skin warm, avoid full desaturation` |

> 制度场景允许偏冷，但**必须保留肤色暖意**，不得整幅降饱和变灰。

### 4.3 负向词（每镜必带）

```
desaturated, gray tone, grey tone, washed out, flat gray, muddy,
cold blue grading, teal shadows, cyan cast, cold cinematic tone,
oversaturated teal-orange, HDR, oversharpened, plastic skin,
anime, illustration, 3d render, cartoon, painting,
crushed blacks, dead black shadows,
logos, watermark, text artifacts, extra fingers, deformed hands,
blurry, low quality,
grainy, heavy film grain, noisy, noise, speckle, speckled,
blotchy, splotchy, dirty, grimy, smudged, haze, fog,
soft focus, out of focus, low detail, compression artifacts
```

> 最后一行为 v1.1 新增的"脏度"负向词，与 §4.1 清洁配方配套使用。

### 4.4 与角色基准的叠加顺序

1. 角色基准（`character-baseline.md`）：`photorealistic, cinematic lighting, realistic textures, natural skin, high detail`
2. + 本文件 4.1 暖调基底
3. + 4.2 场景光色
4. + 本镜具体内容（人物动作、道具、构图）
5. − 4.3 负向词

**顺序不可颠倒**，且第 1、2、3 层为固定模板，不得为了"好看"临时替换成冷调描述。

---

## 五、执行检查（每集出图前自查）

- [ ] 提示词里是否同时含 4.1 暖调基底与 4.3 负向词？
- [ ] 是否存在 `cold / blue / desaturated / muted gray / cinematic cool` 类词汇？（有则删）
- [ ] 制度场景是否保留肤色暖意？
- [ ] 夜景是否用了暖光源（钨丝/白炽/钠灯）而非"冷月光/冷蓝夜"？
- [ ] 出图后：画面是否读得出"暖"？若偏灰，回 4.2 加场景光源词，不靠后期拉色。

---

## 六、变更记录

- 2026-09-08 v1.0 建立。用户拍板采用画面版原案「纪实暖调」，废止此前 ep01 量产时实际执行的"电影感冷调"路线。
