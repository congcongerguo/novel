# -*- coding: utf-8 -*-
"""ep01 极轻底乐（非叙事环境音床）—— 纯 numpy 合成，22050Hz 单声道，长 230.5 秒。

为什么不用"生成的歌"：这个片子的调性是**安静、没有未来**。
随手贴一首 BGM 会立刻把气质做俗。所以做的是一条**几乎听不出来、但撤掉会空**的音床。

分段设计（**按镜号定位，脚本自动读取各镜实际时长累加** —— 改任何一镜的帧数都不会错位）：
  场1 晨 s01–s02         只留呼吸噪声 + 极淡低频（最疏）
  场2 街头 s03–s05        低频微微长起来
  场3 配给点 s06–s12 ★     **低频撤掉**，只留一条高音细线 + 淡噪声 → 制度的"干净、空"
  场4 废品站 s13–s20 ★★    最暖最满：低频 + 偶尔的钟音（全片的情感中心）
  场5 暮 s21             温和退一档
  场6 夜 s22–s25          最疏 → 淡出到零
  ⛔ s14「无所事事」= **硬静默**（宪法：缓冲段不给音乐），位置由镜长算出

用法：python tools/make_music.py
产物：releases/2026-09-12_ep01_成片包/04_配音与音效/_底乐/ep01_底乐.wav
"""
import subprocess
import numpy as np
import wave
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P

SR = 22050
OUT = P.EP01_MUSIC
rng = np.random.default_rng(1937)

ORDER = ["s%02d" % i for i in range(1, 26)]
ORDER.insert(ORDER.index("s23"), "s22b")   # 道具确认镜插在 s22 与 s23 之间（2026-09-12 新增）
_FF = P.FFMPEG_FULL if Path(P.FFMPEG_FULL).exists() else r""

# ── 时间轴：从实际镜长算出每镜的绝对起点 ──────────────────────────
# ⚠️ 分段点**必须**由镜长驱动，不能硬编码秒数：改任何一镜的帧数，
#    硬编码的静默窗与分段就会整体错位（s13 从 141 帧改到 124 帧时踩过）。
def _shot_seconds():
    d = {}
    for p in sorted(P.EP01_VIDEOS.glob("s*_*.mp4")):
        sid = p.stem.split("_")[0]
        try:
            r = subprocess.run([_FF, "-i", str(p)], capture_output=True, text=True)
            s = r.stderr.split("Duration:")[1].split(",")[0].strip()
            h, m, sec = s.split(":")
            d[sid] = int(h) * 3600 + int(m) * 60 + float(sec)
        except Exception:
            pass
    return d


_DUR = _shot_seconds()
_MISS = [s for s in ORDER if s not in _DUR]
if _MISS:
    print("!! 缺少这些镜的成片，时间轴可能不准:", _MISS)
OFF = {}
_acc = 0.0
for _s in ORDER:
    OFF[_s] = _acc
    _acc += _DUR.get(_s, 0.0)
DUR = _acc


def T(shot, rel=0.0):
    """镜号 + 镜内秒 → 整片绝对秒"""
    return OFF.get(shot, 0.0) + rel


N = int(DUR * SR)
t = np.arange(N) / SR


def ramp(points):
    """分段线性包络：points = [(秒, 值), ...]"""
    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)
    return np.interp(t, xs, ys)


def onepole_lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = a * acc + (1 - a) * v
        y[i] = acc
    return y


def drone(freqs, amps):
    """两个微失谐的振荡叠加 → 温暖、缓慢晃动，不会像电子音"""
    x = np.zeros(N)
    for f, a in zip(freqs, amps):
        for det in (-0.35, 0.35):          # 拍频 = 呼吸感
            x += a * np.sin(2 * np.pi * (f + det) * t)
    # 极慢的音量呼吸（0.06Hz ≈ 17 秒一轮）
    x *= (1.0 + 0.10 * np.sin(2 * np.pi * 0.06 * t + 1.2))
    return x


def layer_high():
    """高音细线：制度场景的"空"（一个干净的纯音，冷而不刺）"""
    x = 0.5 * np.sin(2 * np.pi * 440.0 * t) + 0.22 * np.sin(2 * np.pi * 1320.0 * t)
    x *= (1.0 + 0.18 * np.sin(2 * np.pi * 0.045 * t))
    return x


def layer_breath():
    """呼吸噪声：像空气，不是像风"""
    n = rng.normal(0, 1, N)
    n = onepole_lp(n, 420) - onepole_lp(n, 90)      # 带通感
    n *= (1.0 + 0.35 * np.sin(2 * np.pi * 0.033 * t + 0.4))
    return n


def layer_bells():
    """稀疏钟音：五声音阶（D E G A B），每音 4–6 秒衰减，随机但固定种子"""
    x = np.zeros(N)
    scale = [293.66, 329.63, 392.00, 440.00, 493.88,        # D4 E4 G4 A4 B4
             587.33, 659.25, 783.99, 880.00]                # D5 E5 G5 A5
    pos = 100.0
    while pos < DUR - 12:
        f = scale[rng.integers(0, len(scale))]
        i0 = int(pos * SR)
        seg = min(N - i0, int(7.0 * SR))
        if seg <= 0:
            break
        tt = np.arange(seg) / SR
        amp = 0.30 * (0.6 + 0.4 * rng.random())
        sig = (np.sin(2 * np.pi * f * tt) + 0.28 * np.sin(2 * np.pi * f * 2.01 * tt)
               + 0.12 * np.sin(2 * np.pi * f * 3.02 * tt))
        sig = sig * np.exp(-tt * 0.85) * np.clip(tt / 0.06, 0, 1)
        # 不在静默窗里留钟音
        x[i0:i0 + seg] += amp * sig
        pos += float(rng.uniform(13.0, 26.0))
    return x


def main():
    print("合成底乐（%.1f 秒）…" % DUR)

    # 各层独立的段落包络（**全部用镜号定位** → 镜长变化自动适配）
    # 场1 晨 s01–s02 ｜ 场2 街头 s03–s05 ｜ 场3 配给点 s06–s12 ★
    # 场4 废品站 s13–s20 ★★ ｜ 场5 暮 s21 ｜ 场6 夜 s22–s25
    g_low = ramp([(T("s01"), 0.30), (T("s02"), 0.55), (T("s05"), 0.60),
                  (T("s06"), 0.06), (T("s12", -1.0), 0.06),
                  (T("s13"), 0.85), (T("s14"), 1.00), (T("s20"), 0.95),
                  (T("s21"), 0.68), (T("s22"), 0.62), (T("s24"), 0.48),
                  (DUR - 4.5, 0.12), (DUR, 0.0)])
    g_high = ramp([(T("s01"), 0.05), (T("s05"), 0.08), (T("s06"), 0.52),
                   (T("s12", -1.0), 0.50), (T("s13"), 0.16), (T("s20"), 0.14),
                   (T("s22"), 0.10), (T("s25"), 0.06), (DUR, 0.0)])
    g_breath = ramp([(T("s01"), 0.55), (T("s05"), 0.45), (T("s06"), 0.20),
                     (T("s12", -1.0), 0.20), (T("s13"), 0.55), (T("s20"), 0.50),
                     (T("s25"), 0.42), (DUR, 0.05)])
    g_bell = ramp([(T("s12", -1.0), 0.0), (T("s13", +1.0), 0.62), (T("s20"), 0.75),
                   (T("s21"), 0.42), (T("s24"), 0.12), (DUR - 2.5, 0.0)])

    low = drone([73.42, 110.00, 146.83, 220.00], [0.50, 0.30, 0.16, 0.07])
    hi = layer_high()
    br = layer_breath()
    be = layer_bells()

    mix = g_low * low + g_high * hi + g_breath * br + g_bell * be

    # ⛔ s14「无所事事」硬静默（宪法：缓冲段不给音乐）—— 位置由镜长算出
    a0 = T("s14")
    a1 = a0 + _DUR.get("s14", 10.8)
    i0, i1 = int(a0 * SR), int(a1 * SR)
    fa = int(0.4 * SR)
    mix[i0:i1] = 0.0
    mix[max(0, i0 - fa):i0] *= np.linspace(1, 0, min(fa, i0))
    mix[i1:i1 + fa] *= np.linspace(0, 1, fa)

    # 首尾淡入淡出（黑场处无声）
    f_in, f_out = int(6.0 * SR), int(9.0 * SR)
    mix[:f_in] *= np.linspace(0, 1, f_in)
    mix[-f_out:] *= np.linspace(1, 0, f_out)

    peak = np.abs(mix).max()
    mix = mix / peak * 0.80                       # 归一化到 0.80 峰值，实际音量交给混音阶段

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "ep01_底乐.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    rms = np.sqrt((mix ** 2).mean())
    print("  -> %s  %.1f 秒  %.1f MB" % (p.name, len(mix) / SR, p.stat().st_size / 1e6))
    print("     峰值 0.800  RMS %.4f (%.1f dBFS)" % (rms, 20 * np.log10(rms)))
    print("     静默窗 %.1f–%.1f s（s14 实际位置）已硬静音" % (a0, a1))
    print("     正片总长 %.2f 秒（由 %d 条镜实测镜长累加）" % (DUR, len(_DUR)))


if __name__ == "__main__":
    main()
