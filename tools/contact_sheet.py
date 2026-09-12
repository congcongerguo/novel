# -*- coding: utf-8 -*-
"""ep01 分镜联系表（contact sheet）—— 25 张拼一张，便于一次验收
输出: releases/2026-09-12_ep01_成片包/02_分镜首帧/_联系表_ep01_25镜.png
"""
import os
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
SRC = P.EP01_FRAMES

# 按镜号顺序排列（文件名 -> 镜号标签）
ORDER = [
    ("A3_充电头怼三孔圆口.png", "s01 插不进插座"),
    ("s02_蹲地碾铜脚.png", "s02 碾铜脚·库存勿动"),
    ("s03_被当成噪音.png", "s03 被当噪音"),
    ("s04_让你的模型来问.png", "s04 让你模型来问"),
    ("s05_你没登记吧.png", "s05 你没登记吧"),
    ("s06_配给点长队.png", "s06 配给点长队"),
    ("s07_核验失败.png", "s07 核验失败"),
    ("s08_预约死循环.png", "s08 预约死循环"),
    ("s09_方案与选择.png", "s09 方案A与B"),
    ("s10_哪部分经历.png", "s10 哪部分经历"),
    ("s11_把家卖了.png", "s11 把家卖了"),
    ("s12_街边逆光.png", "s12 街边逆光"),
    ("A1_废品收购站场景.png", "s13 废品收购站"),
    ("s14_无所事事坐着.png", "s14 无所事事"),
    ("A2_锈迹斑斑的旧设备.png", "s15 旧设备+面板"),
    ("s16_拨了一下.png", "s16 拨了一下"),
    ("s17_屏幕光映脸.png", "s17 屏幕光映脸"),
    ("s18_怎么修好的.png", "s18 老头两步外"),
    ("s19_塞干粮与硬币.png", "s19 塞干粮硬币"),
    ("s20_别往新城区说.png", "s20 别往新城区说"),
    ("s21_三种人吃东西.png", "s21 三种人"),
    ("s22_摸到兜里那个.png", "s22 摸到兜里那个"),
    ("s23_插上电源口.png", "s23 插上电源口"),
    ("A4_手机屏幕2%.png", "s24 手机2%"),
    ("s25_他抬起头.png", "s25 他抬起头"),
]

COLS = 5
TW = 300                      # 缩略图宽
GAP = 8
LABEL_H = 26
BG = (24, 22, 20)
FG = (235, 225, 210)

font = None
for fp in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
    if os.path.exists(fp):
        try:
            font = ImageFont.truetype(fp, 17); break
        except Exception:
            pass
if font is None:
    font = ImageFont.load_default()

imgs = []
for fn, label in ORDER:
    p = P.frame_path(fn)
    if not p.exists():
        print("MISSING", fn); continue
    im = Image.open(p).convert("RGB")
    h = int(im.height * TW / im.width)
    imgs.append((im.resize((TW, h), Image.LANCZOS), label))

if not imgs:
    raise SystemExit("no images")

TH = max(im.height for im, _ in imgs)
rows = (len(imgs) + COLS - 1) // COLS
W = COLS * TW + (COLS + 1) * GAP
H = rows * (TH + LABEL_H) + (rows + 1) * GAP

canvas = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(canvas)
for i, (im, label) in enumerate(imgs):
    r, c = divmod(i, COLS)
    x = GAP + c * (TW + GAP)
    y = GAP + r * (TH + LABEL_H + GAP)
    canvas.paste(im, (x, y))
    d.text((x + 2, y + TH + 3), label, fill=FG, font=font)

out = SRC / "_联系表_ep01_25镜.png"
canvas.save(out, quality=92)
print("SAVED", out, out.stat().st_size, "bytes", canvas.size, "imgs", len(imgs))
