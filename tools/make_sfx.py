# -*- coding: utf-8 -*-
"""ep01 三个关键动作音效 —— 纯 numpy 合成（无外部依赖）。

为什么自己合成：片子是"安静、没有未来"的调性，随手贴素材库音效会立刻不搭。
这三个音都短、可精确控制，合成比找素材更准。

产物：releases/2026-09-12_ep01_成片包/04_配音与音效/_音效/*.wav   （22050Hz 单声道，与 H3 音轨同规格）

三个音：
  sfx_machine   旧机器开机"嗡"——s16（继电器咔哒 + 低频嗡 + 拍频晃动 + 尾音）
  sfx_screen    手机屏亮的一点微光声——s24
  sfx_current   电流变化的一下（不是放电）——s25

用法：python tools/make_sfx.py
"""
import numpy as np
import wave
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P

SR = 22050
OUT = P.EP01_SFX
rng = np.random.default_rng(20260912)


def t(n):
    return np.arange(int(n * SR)) / SR


def save(x, name):
    x = np.clip(x, -1.0, 1.0)
    x = (x * 32767).astype("<i2")
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(x.tobytes())
    print("  %-22s %.2f 秒  %.0f KB  峰值 %.3f"
          % (name, len(x) / SR, p.stat().st_size / 1024, np.abs(x / 32767).max()))


def onepole_lp(x, cutoff):
    """一阶低通（用于噪声整形）"""
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = a * acc + (1 - a) * v
        y[i] = acc
    return y


def fade(x, a=0.005, b=None):
    n = len(x)
    na = max(1, int(a * SR)); nb = max(1, int((b if b is not None else a) * SR))
    x = x.copy()
    x[:na] *= np.linspace(0, 1, na)
    x[-nb:] *= np.linspace(1, 0, nb)
    return x


def sfx_machine():
    """旧机器开机：咔哒 → 低频嗡起 → 拍频缓慢晃动 → 稳住"""
    n = 3.0
    tt = t(n)
    # ① 继电器咔哒：短促噪声 + 高频衰减
    click = rng.normal(0, 1, len(tt)) * np.exp(-tt * 260)
    click = click - onepole_lp(click, 900)          # 去低频，只剩"咔"
    # ② 低频嗡：58 / 60.5Hz 拍频（这就是"嗡"不安的那点晃动）
    def env(attack, hold):
        e = np.clip(tt / attack, 0, 1)
        e *= np.clip((n - tt) / hold, 0, 1)
        return e
    hum = (0.55 * np.sin(2 * np.pi * 58.0 * tt)
           + 0.45 * np.sin(2 * np.pi * 60.5 * tt)
           + 0.22 * np.sin(2 * np.pi * 116.0 * tt)
           + 0.10 * np.sin(2 * np.pi * 174.0 * tt))
    hum *= np.clip(tt / 0.40, 0, 1) * np.clip((n - tt) / 0.8, 0, 1)
    hum *= (1.0 + 0.06 * np.sin(2 * np.pi * 0.7 * tt))     # 极慢的呼吸
    # ③ 底噪：机械的低频沙沙
    hiss = onepole_lp(rng.normal(0, 1, len(tt)), 260) * 0.10
    hiss *= np.clip(tt / 0.5, 0, 1) * np.clip((n - tt) / 1.0, 0, 1)
    x = 0.42 * click + 0.50 * hum + hiss
    save(fade(x, 0.004, 0.35), "sfx_machine_机器嗡.wav")


def sfx_screen():
    """屏幕亮起：一点微光声（很短、很软，不抢戏）"""
    n = 0.9
    tt = t(n)
    a = np.sin(2 * np.pi * 1320 * tt) * np.exp(-tt * 7.5) * 0.5
    b = np.sin(2 * np.pi * 2640 * tt) * np.exp(-tt * 16) * 0.18
    tick = (rng.normal(0, 1, len(tt)) * np.exp(-tt * 500))
    tick = tick - onepole_lp(tick, 2500)
    x = a + b + 0.16 * tick
    save(fade(x, 0.002, 0.18), "sfx_screen_屏亮.wav")


def sfx_current():
    """电流变了那一下——不是放电：一个上行的极短滑音 + 轻颤 + 尾韵"""
    n = 1.5
    tt = t(n)
    f = 380 + 620 * np.clip(tt / 0.28, 0, 1)      # 380→1000Hz 滑音
    ph = 2 * np.pi * np.cumsum(f) / SR
    shimmer = np.sin(ph) * np.exp(-tt * 3.4) * 0.42
    shimmer *= (1 + 0.25 * np.sin(2 * np.pi * 27 * tt))   # 轻颤
    tail = np.sin(2 * np.pi * 500 * tt) * np.exp(-tt * 2.0) * 0.16
    tick = (rng.normal(0, 1, len(tt)) * np.exp(-tt * 420))
    tick = tick - onepole_lp(tick, 3000)
    x = shimmer + tail + 0.13 * tick
    save(fade(x, 0.002, 0.30), "sfx_current_电流变化.wav")


if __name__ == "__main__":
    print("合成动作音效 ->", OUT)
    sfx_machine(); sfx_screen(); sfx_current()
