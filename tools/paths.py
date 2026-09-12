# -*- coding: utf-8 -*-
"""全项目产物路径的唯一事实来源（Single Source of Truth）。

为什么要有这个文件：
    之前路径硬编码散在 8 个脚本里，一归档/一改目录就要逐个改，漏一个就会
    "重跑时把文件又散到旧目录去"。现在所有脚本都从这里取路径 —— 归档、
    迁移、开始新一集，只改这一个文件。

用法：
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    import paths as P
    print(P.EP01_VIDEOS)
"""
from pathlib import Path

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
RELEASES = ROOT / "releases"

# ══════════════════════ ep01 成片包（2026-09-12 归档） ══════════════════════
# 归档结构：01 成片 / 02 首帧 / 03 视频 / 04 配音 / 05 质检 / 06 中间产物 / 99 历史废弃
EP01 = RELEASES / "2026-09-12_ep01_成片包"

EP01_FINAL      = EP01 / "01_成片"                    # 最终交付 mp4
EP01_FRAMES     = EP01 / "02_分镜首帧"                 # 25 张定稿首帧
EP01_ANCHORS    = EP01 / "02_分镜首帧" / "_锚点"        # A1-A4（A1/A2/A3/A4 同时是 s13/s15/s01/s24 的首帧）
EP01_VIDEOS     = EP01 / "03_镜头视频"                 # 25 条 H3 镜头 + 整集粗剪
EP01_AUDIO      = EP01 / "04_配音与音效"
EP01_VO         = EP01_AUDIO / "旁白与画外音"           # IndexTTS 产出的 V.O./OS
EP01_REF        = EP01_AUDIO / "_参考音色"             # 从 H3 成片剪出的角色音色（供 TTS 当 prompt）
EP01_MUSIC      = EP01_AUDIO / "_底乐"                # make_music.py 产出
EP01_SFX        = EP01_AUDIO / "_音效"                # make_sfx.py 产出
EP01_QA         = EP01 / "05_质检"
EP01_QA_FRAMES  = EP01_QA / "质检帧"                   # 烧字幕后的关键帧截图
EP01_QA_AUDIO   = EP01_QA / "音轨验收"                  # 每条镜的 mp3（听语言/对白）
EP01_QA_REPORT  = EP01_QA / "_一致性报告.txt"           # consistency_check.py 产出
EP01_MID        = EP01 / "06_中间产物"                 # concat 列表 / 无字幕整集 / 混音整集 / ass / srt
EP01_HIST       = EP01 / "99_历史与废弃"               # 废版本，只为对照留档
EP01_HIST_V1    = EP01_HIST / "视频_废弃v1_无对白无轴线"
EP01_HIST_FRAME = EP01_HIST / "首帧旧版本"


# ══════════════════════ 早期批次（2026-09-09 量产） ══════════════════════
BATCH_0909 = RELEASES / "2026-09-09_量产"
BATCH_0909_FRAMES = BATCH_0909 / "02_分镜首帧"
BATCH_0909_VIDEOS = BATCH_0909 / "03_镜头视频"

# ══════════════════════ 工具链固定路径（非产物） ══════════════════════
FFMPEG_FULL = r"D:\ai\ComfyUI-V30\python\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
COMFY_HOST = "http://127.0.0.1:8188"
INDEX_TTS_DIR = Path(r"C:\Users\oo\WorkBuddy\Claw\index-tts-windows")


def ensure(*dirs):
    """按需创建目录（避免 import 时到处 mkdir）。"""
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def frame_path(name):
    """按文件名找首帧 —— 首帧分布在两处，必须都查。

    s01/s13/s15/s24 的首帧就是锚点图 A3/A1/A2/A4（归档后在 `_锚点/` 子目录），
    其余在 02_分镜首帧 根下。只查一处会漏掉那四张。
    """
    for d in (EP01_FRAMES, EP01_ANCHORS):
        p = d / name
        if p.exists():
            return p
    return EP01_FRAMES / name


if __name__ == "__main__":
    print("ROOT:", ROOT)
    for k, v in sorted(globals().items()):
        if k.startswith("EP01") or k.startswith("BATCH"):
            p = Path(v)
            n = len([x for x in p.rglob("*") if x.is_file()]) if p.is_dir() else (1 if p.exists() else 0)
            print("  %-16s %-58s %s" % (k, str(v).replace(str(ROOT), "."), "%d files" % n if p.is_dir() else ("存在" if n else "缺失")))
