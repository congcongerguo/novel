# -*- coding: utf-8 -*-
"""抽帧对比工具 —— 把相邻镜头（或任意镜头）的关键帧抽出来拼成一张对比图。

用途：
    · 看不清"两镜之间到底哪里不连贯"时，把它们的关键帧并排放，一眼定位
    · 与首帧源图算相关度，判断画面是否延续

用法：
    python tools/frame_compare.py s13 s14              # s13/s14 各抽 首/中/尾 三帧
    python tools/frame_compare.py s13 s14 --frames 3    # 每镜抽 3 帧（默认 3）
    python tools/frame_compare.py s13 --vs-frame A1_废品收购站场景.png   # 与某张源图比对

输出：releases/.../05_质检/对比_s13_s14.png （并打印客观指标）
"""
import subprocess, sys, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P

FFMPEG = P.FFMPEG_FULL if Path(P.FFMPEG_FULL).exists() else r"C:\Users\oo\anaconda3\envs\indextts\Library\bin\ffmpeg.exe"
TMP = P.ROOT / ".workbuddy" / "tmp" / "frame_compare"


def duration(mp4):
    r = subprocess.run([FFMPEG, "-i", str(mp4)], capture_output=True, text=True)
    try:
        s = r.stderr.split("Duration:")[1].split(",")[0].strip()
        h, m, sec = s.split(":")
        return int(h) * 3600 + int(m) * 60 + float(sec)
    except Exception:
        return 0.0


def grab(mp4, t, out):
    subprocess.run([FFMPEG, "-y", "-ss", "%.2f" % t, "-i", str(mp4),
                    "-frames:v", "1", str(out)], capture_output=True)
    return out if out.exists() else None


def gray_small(p, n=64):
    from PIL import Image
    im = Image.open(p).convert("L").resize((n, n))
    d = list(im.getdata())
    m = sum(d) / len(d)
    return d, m


def struct_corr(a, b):
    da, ma = gray_small(a); db, mb = gray_small(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(da, db))
    xa = math.sqrt(sum((x - ma) ** 2 for x in da))
    xb = math.sqrt(sum((y - mb) ** 2 for y in db))
    return num / (xa * xb) if xa and xb else 0.0


def skin_ratio(p):
    """皮肤像素占比（YCrCb 阈值）—— 粗略指示"画面里有多少人"（脸/手/脖子）"""
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        return float("nan")
    im = Image.open(p).convert("RGB")
    im.thumbnail((320, 320))
    a = np.asarray(im).astype("float32")
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cr = (r - y) * 0.713 + 128
    cb = (b - y) * 0.564 + 128
    m = (cr >= 133) & (cr <= 180) & (cb >= 77) & (cb <= 127) & (y > 60)
    return float(m.mean())


def shot_video(shot):
    for p in P.EP01_VIDEOS.glob("%s_*.mp4" % shot):
        return p
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_frames = 3
    if "--frames" in sys.argv:
        n_frames = int(sys.argv[sys.argv.index("--frames") + 1])
    vs = None
    if "--vs-frame" in sys.argv:
        vs = sys.argv[sys.argv.index("--vs-frame") + 1]

    shots = [a for a in args if len(a) == 3 and a[0] == "s" and a[1:].isdigit()]
    if not shots:
        print("用法: python frame_compare.py s13 s14 [--frames 3] [--vs-frame A1_xxx.png]"); return

    TMP.mkdir(parents=True, exist_ok=True)
    P.ensure(P.EP01_QA)

    panels, labels, rows = [], [], []
    for shot in shots:
        v = shot_video(shot)
        if not v:
            print("!! 找不到 %s 的视频" % shot); continue
        d = duration(v)
        ts = [0.05] if n_frames == 1 else [d * (i + 0.5) / n_frames for i in range(n_frames)] if n_frames == 2 \
            else [0.05, d / 2, max(0.05, d - 0.1)]
        print("── %s (%.2f 秒)" % (shot, d))
        for i, t in enumerate(ts):
            f = grab(v, t, TMP / ("%s_%02d.png" % (shot, i)))
            if not f:
                continue
            sk = skin_ratio(f)
            print("   %5.2fs  皮肤占比 %.3f" % (t, sk))
            panels.append(f); labels.append("%s @%.1fs" % (shot, t)); rows.append((shot, t, sk, f))
        print()

    # 与指定源图的相关度
    if vs:
        src = P.frame_path(vs)
        if src.exists():
            print("── 与 %s 的表面相似度（越低说明画面越不同）" % vs)
            for shot, t, sk, f in rows:
                print("   %s @%.1fs  相关 %+.3f" % (shot, t, struct_corr(src, f)))
            print()

    # 拼图
    try:
        from PIL import Image, ImageDraw
        ims = [Image.open(p).convert("RGB") for p in panels]
        W = 380
        ims = [im.resize((W, int(im.height * W / im.width))) for im in ims]
        H = max(im.height for im in ims) + 44
        cols = len(ims)
        sheet = Image.new("RGB", (W * cols, H), (24, 24, 24))
        dr = ImageDraw.Draw(sheet)
        for i, im in enumerate(ims):
            sheet.paste(im, (i * W, 40))
            dr.text((i * W + 10, 12), labels[i], fill=(255, 210, 120))
        out = P.EP01_QA / ("对比_%s.png" % "_".join(shots))
        sheet.save(out)
        print("已生成对比图:", out)
    except Exception as e:
        print("拼图失败:", e)


if __name__ == "__main__":
    main()
