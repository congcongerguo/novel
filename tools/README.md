# tools/ — 生产脚本（**唯一事实来源**）

> 这些脚本是《注释》影视化流水线的全部工具。**25 镜的提示词、锚点常量、轴线规则都写在里面**，
> 是核心创作资产，因此入库（`.workbuddy/scripts/` 已被清空，只留迁移说明——那里曾有两份不同步的副本，
> 旧版 `gen_ep01_h3.py` 会产出"没锁首帧"的视频，极易误用）。

## 📍 路径统一在 `paths.py`

所有脚本的产物路径都从 `paths.py` 取，**不再硬编码**：

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P
P.EP01_VIDEOS          # releases/2026-09-12_ep01_成片包/03_镜头视频
P.frame_path("A1_xxx.png")   # 首帧查找（会自动兼顾 _锚点/ 子目录）
```

**归档、迁移、开新一集 —— 只改这一个文件。**

## 🛠 脚本表

### 生图（Seedream 5.0 Pro · 云端付费）
| 脚本 | 作用 | 用法 |
|------|------|------|
| `seedream_batch.py` | **ep01 首帧批量生成**｜内含全 25 镜提示词、锚点常量（A1–A4）、场景/轴线常量（`INST_WARM`/`NIGHT_WARM`/`AXIS_WINDOW`/`DUSK`）、多图参考 `REF_NOTE` | `python seedream_batch.py s01 s13` ／ `all` |
| `seedream_ref_gen.py` | 单张参考图生图（`image` 传 base64 参考） | `python seedream_ref_gen.py out.png ref.png --prompt "…"` |
| `seedream_gen.py` | 纯文生图（最早跑通的版本，留档） | `python seedream_gen.py …` |

### 生视频（MiniMax H3 · 本地 ComfyUI）
| 脚本 | 作用 | 用法 |
|------|------|------|
| `gen_ep01_h3.py` | **ep01 视频批量生成**｜全 25 镜 H3 结构化提示词 + 帧数表（124+17k）+ `<d>[Chinese]` 对白 + 轴线常量 | `python gen_ep01_h3.py s01` ／ `all` |
| `test_h3_modes.py` | 节点/模式 A/B 测试（验证"首帧锁定 vs 参考图"） | `python test_h3_modes.py s04 i2v i2v_ref` |
| `frame_fidelity.py` | **首帧保真度自检**（抽视频第 0 帧 vs 首帧源图，逐像素 MAD + 相关度 + 平移搜索） | `python frame_fidelity.py` ／ `s01 --cmp` |

### 配音（IndexTTS2 · 本地）
| 脚本 | 作用 | 用法 |
|------|------|------|
| `make_voice_refs.py` | 从 H3 成片**剪出角色参考音色**（保证旁白与对白同一个嗓子） | `python make_voice_refs.py` |
| `tts_vo.py` | 批量合成旁白/画外音（**单进程、模型只加载一次**） | `python tts_vo.py` |
| `make_music.py` | 合成**极轻底乐**（numpy，分段设计 + s14 硬静默） | `python make_music.py` |
| `make_sfx.py` | 合成**动作音效**（机器嗡/屏亮/电流变化） | `python make_sfx.py` |

### 装配与质检
| 脚本 | 作用 | 用法 |
|------|------|------|
| `assemble_ep01.py` | **拼接 → 整片绝对时间混音 → ASS 字幕 → 放大 1080×1920 → 片头片尾黑场 → 导出** | `python assemble_ep01.py` ／ `concat` ／ `mix` ／ `burn` |
| `consistency_check.py` | 画面一致性检查（暖度/饱和/明度/尺寸 + 分组均值 + 违规清单） | `python consistency_check.py` |
| `contact_sheet.py` | 把 25 张拼成**联系表**（带镜号标签，一次验收） | `python contact_sheet.py` |
| `extract_audio.py` | 抽成片音轨为 mp3（"语言对不对"用耳朵听比逐个点视频快） | `python extract_audio.py s04 s05` |

## 🔧 运行环境

- **Pillow / numpy 在隔离 venv**：`C:\Users\oo\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
  （`consistency_check` / `contact_sheet` / `frame_fidelity` / `make_music` / `make_sfx` / `assemble_ep01` 用它跑）
- **IndexTTS2 用自己的 venv**：`C:\Users\oo\WorkBuddy\Claw\index-tts-windows\.venv\Scripts\python.exe`（`tts_vo.py` 必须用它，且**要在该目录下运行**——`indextts` 是本地包未装进 venv）
- **ffmpeg 用 ComfyUI 自带版**：`imageio_ffmpeg 7.1`（conda 那个精简构建**没有 libx264**）
- 依赖服务：ComfyUI `127.0.0.1:8188`；火山方舟云端生图（key 在 `~/.workbuddy/.env` 的 `ARK_API_KEY`）

## ⛔ 铁律（详见 `spec/visual/生成管线.md` 与 `h3提示词规范.md`）

**生图**
1. **Seedream 提示词零否定词**——"不要冷 / not too dark" 会被反向执行（连那个字都别写）
2. **锚点必须作为 `image` 参考传入**，只写文字等于没锚点
3. **同一场戏共用常量**（光色 + 轴线），各写一遍必然错乱
4. **改图前先备份**（改名 `.v2` / `.preanchor` 等）

**生视频**
5. **要锁首帧必须用 `Yuan_MiniMaxH3Video` 的「图生视频」模式**——`MiniMaxH3ReferenceToVideo` 没有首帧通道（提示词写再多也没用）
6. **对白必须 `<d>[Chinese] 台词。</d>`**（否则出英文/乱码）；无对白镜的声景里禁止出现 `voice/says/talking` 等触发词
7. **H3 必须串行跑**——并行抢 GPU，单镜从 6 分钟涨到 38 分钟
8. **每批出片必跑 `frame_fidelity.py`**——首帧没锁住是肉眼最难看出的错

**装配**
9. **`amix duration=first` 取的是输入列表第一位**——主音轨必须排第一，否则音轨被截断（**容器时长看不出**，必须量音轨）
10. **混音要在拼接之后、按整片绝对时间做**——单镜内混音会被镜长截断
