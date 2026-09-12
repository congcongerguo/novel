# -*- coding: utf-8 -*-
"""从成片里抽出音频轨，便于快速验收"语言对不对 / 有没有乱码人声"。

为什么需要：H3 的语音是随画面一起生成的，判断"中文对不对"只能靠听。
逐个点开视频太慢 —— 抽成音频后可以连着听一遍。

用法：
  python extract_audio.py                      # 抽 releases/2026-09-12_ep01_成片包/03_镜头视频/ 全部
  python extract_audio.py s01 s04 s07          # 指定镜号
  python extract_audio.py --cmp                # 同时抽「废弃v1」作对照（v1_xxx.mp3）

输出：releases/2026-09-12_ep01_成片包/03_镜头视频/_音频验收/<镜号>.mp3
      加 --cmp 时同一目录下多出 v1_<镜号>.mp3
"""
import subprocess, sys
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
VID_DIR = P.EP01_VIDEOS
V1_DIR = P.EP01_HIST_V1
OUT_DIR = P.EP01_QA_AUDIO

# ffmpeg 不在 PATH，用 indextts 环境里那个（2026-09-12 探明）
FFMPEG = Path(r"C:\Users\oo\anaconda3\envs\indextts\Library\bin\ffmpeg.exe")
if not FFMPEG.exists():
    import shutil
    found = shutil.which("ffmpeg")
    if not found:
        raise SystemExit("找不到 ffmpeg，请检查 C:/Users/oo/anaconda3/envs/indextts/Library/bin/ffmpeg.exe")
    FFMPEG = Path(found)


def extract(mp4: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    # 只保留音轨，转 mp3；-vn 丢视频，音量略微归一化便于听
    cmd = [str(FFMPEG), "-y", "-i", str(mp4), "-vn",
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
           "-ar", "44100", "-ac", "1", "-b:a", "128k", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # 退一步：不做响度归一化（有些构建缺 loudnorm）
        cmd = [str(FFMPEG), "-y", "-i", str(mp4), "-vn", "-ar", "44100", "-ac", "1",
               "-b:a", "128k", str(dst)]
        r = subprocess.run(cmd, capture_output=True, text=True)
    ok = dst.exists() and dst.stat().st_size > 2000
    print("%-34s -> %s %s" % (mp4.name, dst.name, "OK %.0f KB" % (dst.stat().st_size / 1024) if ok else "FAIL"))
    if not ok:
        print("   ", r.stderr.strip()[-300:])
    return ok


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cmp_mode = "--cmp" in sys.argv

    files = sorted(VID_DIR.glob("*.mp4"))
    if args:
        files = [f for f in files if any(f.name.startswith(a + "_") for a in args)]
    if not files:
        print("没找到视频：", VID_DIR); return

    n = 0
    for f in files:
        if extract(f, OUT_DIR / (f.stem + ".mp3")):
            n += 1

    if cmp_mode and V1_DIR.exists():
        print("\n--- 对照：废弃 v1（错误版）---")
        for f in sorted(V1_DIR.glob("*.mp4")):
            if args and not any(f.name.startswith(a + "_") for a in args):
                continue
            extract(f, OUT_DIR / ("v1_" + f.stem + ".mp3"))

    print("\n共 %d 条 -> %s" % (n, OUT_DIR))
    print("听法：先听 v2 的（正确版），再听 v1_ 开头的（错误版）——同一镜对比，语言差别一耳就出来。")


if __name__ == "__main__":
    main()
