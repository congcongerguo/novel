# -*- coding: utf-8 -*-
"""首帧保真度检查：抽出视频的第 0 帧，与生成它的首帧原图比对。

为什么需要：H3 是"参考生视频"，prompt 里写不写 `<Picture 1>` 锚定，
肉眼很难判断"到底有没有用上首帧"。这个脚本给出可量化的答案。

指标：
  MAD      平均绝对差（0-255，越小越像）—— < 12 视为"确实从该帧起步"
  直方图相关  整体色调/明暗分布相关度（1.0 = 完全一致）—— > 0.90 视为同色调
  结构相似度  灰度降采样后的皮尔逊相关（-1..1）—— > 0.60 视为构图同源

用法：
  python frame_fidelity.py                 # 检查 releases/2026-09-12_ep01_成片包/03_镜头视频/ 全部
  python frame_fidelity.py s01 s04 s07
  python frame_fidelity.py --cmp           # 同时比对「废弃v1」错误版
"""
import sys, subprocess, math
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P
from PIL import Image, ImageStat

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
VID_DIR = P.EP01_VIDEOS
V1_DIR = P.EP01_HIST_V1
FRAME_DIR = P.EP01_FRAMES
TMP = ROOT / ".workbuddy" / "tmp" / "frame_chk"

FFMPEG = Path(r"C:\Users\oo\anaconda3\envs\indextts\Library\bin\ffmpeg.exe")

# 与 tools/gen_ep01_h3.py 的 FRAME_FILE 保持一致
FRAME_FILE = {
    "s01": "A3_充电头怼三孔圆口.png", "s02": "s02_蹲地碾铜脚.png",
    "s03": "s03_被当成噪音.png", "s04": "s04_让你的模型来问.png",
    "s05": "s05_你没登记吧.png", "s06": "s06_配给点长队.png",
    "s07": "s07_核验失败.png", "s08": "s08_预约死循环.png",
    "s09": "s09_方案与选择.png", "s10": "s10_哪部分经历.png",
    "s11": "s11_把家卖了.png", "s12": "s12_街边逆光.png",
    "s13": "A1_废品收购站场景.png", "s14": "s14_无所事事坐着.png",
    "s15": "A2_锈迹斑斑的旧设备.png", "s16": "s16_拨了一下.png",
    "s17": "s17_屏幕光映脸.png", "s18": "s18_怎么修好的.png",
    "s19": "s19_塞干粮与硬币.png", "s20": "s20_别往新城区说.png",
    "s21": "s21_三种人吃东西.png", "s22": "s22_摸到兜里那个.png",
    "s22b": "s22b_充电头在手心.png",
    "s23": "s23_插上电源口.png", "s24": "A4_手机屏幕2%.png",
    "s25": "s25_他抬起头.png",
}


def first_frame(mp4: Path, tag: str):
    TMP.mkdir(parents=True, exist_ok=True)
    dst = TMP / ("%s_%s_f0.png" % (tag, mp4.stem))
    cmd = [str(FFMPEG), "-y", "-i", str(mp4), "-vf", "select=eq(n\\,0)",
           "-frames:v", "1", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return dst if dst.exists() else None


def metrics(a: Path, b: Path):
    """逐像素比对（不是比平均色）。
    返回 (逐像素MAD, 灰度相关, 平移修正后的最大灰度相关, 最优偏移)"""
    ia = Image.open(a).convert("RGB")
    ib = Image.open(b).convert("RGB")
    ib2 = ib.resize(ia.size, Image.LANCZOS)

    # ① 逐像素平均绝对差
    diff = Image.new("L", ia.size)
    import PIL.ImageChops as C
    d = C.difference(ia, ib2).convert("L")
    mad = sum(d.getdata()) / (ia.size[0] * ia.size[1])

    # ② 灰度相关（原尺寸）
    A = ia.convert("L").resize((96, 96), Image.LANCZOS)
    B = ib2.convert("L").resize((96, 96), Image.LANCZOS)
    pa = list(A.getdata()); pb = list(B.getdata())
    n = len(pa)
    ma = sum(pa) / n; mb = sum(pb) / n
    num = sum((pa[i] - ma) * (pb[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in pa))
    db = math.sqrt(sum((x - mb) ** 2 for x in pb))
    corr = num / (da * db) if da and db else 0.0

    # ③ 平移搜索：H3 可能把参考图裁切/位移，偏移后相关才公平
    best, best_off = corr, (0, 0)
    W = 96
    for dy in (-6, -4, -2, 0, 2, 4, 6):
        for dx in (-6, -4, -2, 0, 2, 4, 6):
            if dx == 0 and dy == 0:
                continue
            # B 平移 (dx,dy) 后与 A 比（只比重叠区）
            xs = range(max(0, dx), min(W, W + dx))
            ys = range(max(0, dy), min(W, W + dy))
            va = []; vb = []
            for y in ys:
                for x in xs:
                    va.append(pa[y * W + x])
                    vb.append(pb[(y - dy) * W + (x - dx)])
            m = len(va)
            if m < W * W * 0.6:
                continue
            mva = sum(va) / m; mvb = sum(vb) / m
            nu = sum((va[i] - mva) * (vb[i] - mvb) for i in range(m))
            d1 = math.sqrt(sum((x - mva) ** 2 for x in va))
            d2 = math.sqrt(sum((x - mvb) ** 2 for x in vb))
            c = nu / (d1 * d2) if d1 and d2 else 0.0
            if c > best:
                best, best_off = c, (dx, dy)

    return mad, corr, best, best_off


def check(mp4: Path, tag=""):
    shot = mp4.stem.split("_")[0]
    src = P.frame_path(FRAME_FILE.get(shot, ""))
    if not src.exists():
        print("%-24s 找不到对应首帧，跳过" % mp4.name); return
    f0 = first_frame(mp4, tag or "v2")
    if not f0:
        print("%-24s 抽帧失败（缺 ffmpeg？）" % mp4.name); return
    mad, corr, best, off = metrics(src, f0)
    # 逐像素 MAD：<14 很像、<25 有偏移/重裁、>=25 基本无关
    if best > 0.75 and mad < 22:
        verdict = "✅ 同源"
    elif best > 0.55:
        verdict = "⚠️ 偏移/重裁"
    else:
        verdict = "❌ 脱钩"
    print("%-26s 逐像素MAD %5.1f | 灰度相关 %+.3f | 平移后最佳 %+.3f @%s   %s"
          % (mp4.name, mad, corr, best, str(off), verdict))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not FFMPEG.exists():
        raise SystemExit("找不到 ffmpeg：%s" % FFMPEG)

    files = sorted(VID_DIR.glob("*.mp4"))
    if args:
        files = [f for f in files if any(f.name.startswith(a + "_") for a in args)]
    if not files:
        print("没找到视频：", VID_DIR); return

    print("═══ v2.0（官方语法版）═══")
    for f in files:
        check(f)

    if "--cmp" in sys.argv and V1_DIR.exists():
        print("\n═══ v1（错误版 · 对照）═══")
        for f in sorted(V1_DIR.glob("*.mp4")):
            if args and not any(f.name.startswith(a + "_") for a in args):
                continue
            check(f, tag="v1")

    print("\n判读：MAD 越小 / 结构相似越高 = 视频确实从该首帧起步。")
    print("      v1 大量“❌ 脱钩”就印证了“视频和首图没关系”。")


if __name__ == "__main__":
    main()
