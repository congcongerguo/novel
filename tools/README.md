# tools/ — 生产脚本（入库版）

> 这些脚本原本放在 `.workbuddy/scripts/`（被 .gitignore 忽略），2026-09-12 复制入库——
> **因为 25 镜的提示词全写在里面，是核心创作资产，不能只留在本地。**

| 脚本 | 作用 | 用法 |
|------|------|------|
| `seedream_batch.py` | **ep01 首帧批量生成**（Seedream 5.0 Pro）｜内含全 25 镜提示词、锚点常量（A1–A4）、场景/轴线常量（`INST_WARM` / `NIGHT_WARM` / `AXIS_WINDOW` / `DUSK`）、多图参考的 `REF_NOTE` | `python seedream_batch.py s01 s13` ／ `all`（已存在自动跳过） |
| `gen_ep01_h3.py` | **ep01 视频批量生成**（MiniMax H3 图生视频，带音频）｜内含全 25 镜 H3 结构化提示词、帧数表（124+17k）、参考图上传 | `python gen_ep01_h3.py s01` ／ `all` |
| `seedream_ref_gen.py` | 单张参考图生图（Seedream，`image` 参考） | `python seedream_ref_gen.py out.png ref.png --prompt "…"` |
| `consistency_check.py` | **成片一致性检查**（暖度/饱和度/明度/尺寸 + 分组均值 + 违规清单） | `python consistency_check.py`（路径写在文件里） |
| `contact_sheet.py` | 把一组图拼成**联系表**（带镜号标签，便于一次验收） | `python contact_sheet.py` |

## 运行环境

- **Pillow 装在隔离 venv**：`C:\Users\oo\.workbuddy\binaries\python\envs\default\Scripts\python.exe`（`consistency_check.py` / `contact_sheet.py` 用它跑）
- 纯 HTTP 调用的脚本（`seedream_batch.py` / `gen_ep01_h3.py` / `seedream_ref_gen.py`）用任意 python 3 即可
- 依赖服务：ComfyUI `127.0.0.1:8188`（视频）；云端火山方舟（生图，key 在 `~/.workbuddy/.env` 的 `ARK_API_KEY`）

## 铁律（都在 `spec/visual/生成管线.md`，这里只列最要命的）

1. **Seedream 提示词零否定词**——"不要冷 / not too dark" 会被反向执行
2. **锚点必须作为 `image` 参考传入**，只写文字等于没锚点
3. **同一场戏共用常量**（光色 + 轴线），各写一遍必然错乱
4. **改图前先备份**（改名 `.v2` / `.preanchor` 等）
