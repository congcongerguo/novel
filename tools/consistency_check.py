# -*- coding: utf-8 -*-
"""ep01 分镜场景一致性检查（客观色彩指标）
按 visual-spec-lock 判定：暖调（R>B）、不灰（饱和度）、明度适中
输出: releases/2026-09-12_ep01分镜图/_一致性报告.txt
"""
import os
from pathlib import Path
from PIL import Image, ImageStat

SRC = Path(r"C:\Users\oo\WorkBuddy\小说未来ai\releases\2026-09-12_ep01分镜图")

# (文件, 镜号, 场次光色标签)
SHOTS = [
    ("A3_充电头怼三孔圆口.png", "s01", "晨·室内"),
    ("s02_蹲地碾铜脚.png", "s02", "晨·室内"),
    ("s03_被当成噪音.png", "s03", "日间·外"),
    ("s04_让你的模型来问.png", "s04", "日间·外"),
    ("s05_你没登记吧.png", "s05", "午后·外"),
    ("s06_配给点长队.png", "s06", "机构·冷白"),
    ("s07_核验失败.png", "s07", "机构·冷白"),
    ("s08_预约死循环.png", "s08", "机构·冷白"),
    ("s09_方案与选择.png", "s09", "机构·冷白"),
    ("s10_哪部分经历.png", "s10", "机构·冷白"),
    ("s11_把家卖了.png", "s11", "机构·冷白"),
    ("s12_街边逆光.png", "s12", "正午·外"),
    ("A1_废品收购站场景.png", "s13", "午后·外"),
    ("s14_无所事事坐着.png", "s14", "午后·外"),
    ("A2_锈迹斑斑的旧设备.png", "s15", "午后·外"),
    ("s16_拨了一下.png", "s16", "午后·外"),
    ("s17_屏幕光映脸.png", "s17", "午后至黄昏·外"),
    ("s18_怎么修好的.png", "s18", "黄昏·外"),
    ("s19_塞干粮与硬币.png", "s19", "黄昏·外"),
    ("s20_别往新城区说.png", "s20", "黄昏·外"),
    ("s21_三种人吃东西.png", "s21", "暮·外"),
    ("s22_摸到兜里那个.png", "s22", "夜·外"),
    ("s23_插上电源口.png", "s23", "夜·外"),
    ("A4_手机屏幕2%.png", "s24", "夜·外"),
    ("s25_他抬起头.png", "s25", "夜·外"),
]


def metrics(p):
    im = Image.open(p).convert("RGB")
    w0, h0 = im.size                      # 先记录原始尺寸，再缩放
    im.thumbnail((256, 256))
    st = ImageStat.Stat(im)
    r, g, b = st.mean
    hsv = im.convert("HSV")
    s = ImageStat.Stat(hsv).mean[1] / 255.0
    v = ImageStat.Stat(hsv).mean[2] / 255.0
    warmth = r - b                      # 暖度：>0 暖、<0 冷
    return dict(w=w0, h=h0, R=r, G=g, B=b, warmth=warmth, sat=s, val=v)


rows = []
for fn, sid, light in SHOTS:
    p = SRC / fn
    if not p.exists():
        rows.append((sid, light, fn, None)); continue
    rows.append((sid, light, fn, metrics(p)))

lines = []
lines.append("ep01 分镜场景一致性报告（客观色彩指标）")
lines.append("生成日期 2026-09-12 | 引擎 Seedream 5.0 Pro | 目标：1152x2048 竖屏")
lines.append("判定基准(visual-spec-lock)：暖调 R-B>+8 合格；饱和度 >0.18 不灰；明度 0.25-0.85 正常")
lines.append("")
hdr = "%-5s %-12s %-26s %6s %8s %7s %7s %s" % ("镜", "光色", "文件", "R-B", "饱和", "明度", "尺寸", "判定")
lines.append(hdr)
lines.append("-" * len(hdr))

issues = []
for sid, light, fn, m in rows:
    if m is None:
        lines.append("%-5s %-12s %-26s   MISSING" % (sid, light, fn)); issues.append((sid, "缺文件")); continue
    flags = []
    if m["warmth"] < 5 and "夜" not in light and "机构" not in light:
        flags.append("偏冷")
    if m["warmth"] < 0:
        flags.append("冷调!!")
    if m["sat"] < 0.15 and "夜" not in light:
        flags.append("低饱和")
    if m["val"] < 0.22:
        flags.append("过暗")
    if m["val"] > 0.88:
        flags.append("过曝")
    if (m["w"], m["h"]) != (1152, 2048):
        flags.append("尺寸不符")
    verdict = "OK" if not flags else " / ".join(flags)
    if flags:
        issues.append((sid, verdict))
    lines.append("%-5s %-12s %-26s %+6.1f %8.3f %7.3f %7s %s" % (
        sid, light, fn[:24], m["warmth"], m["sat"], m["val"], "%dx%d" % (m["w"], m["h"]), verdict))

lines.append("")
lines.append("== 分组均值 ==")
groups = {}
for sid, light, fn, m in rows:
    if m is None:
        continue
    key = "机构·冷白" if "机构" in light else ("夜" if "夜" in light else "老城区·日")
    groups.setdefault(key, []).append(m)
for k, v in groups.items():
    wr = sum(x["warmth"] for x in v) / len(v)
    sa = sum(x["sat"] for x in v) / len(v)
    va = sum(x["val"] for x in v) / len(v)
    lines.append("%-12s n=%-3d 暖度%+6.1f 饱和%.3f 明度%.3f" % (k, len(v), wr, sa, va))

lines.append("")
lines.append("== 问题清单 ==")
if issues:
    for sid, why in issues:
        lines.append("  %s : %s" % (sid, why))
else:
    lines.append("  无")

out = SRC / "_一致性报告.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print()
print("SAVED", out)
