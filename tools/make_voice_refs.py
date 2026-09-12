# -*- coding: utf-8 -*-
"""从 H3 成片里剪出角色声音，拼成 IndexTTS 的参考音频（reference prompt）。

为什么这么做（方案 B 的关键）：
  方案 B = 对白用 H3 生成的音 + V.O. 用 IndexTTS 配。
  若 V.O. 另找音色，观众会听出"旁白一个人、说话另一个人"。
  **所以 V.O. 的参考音频应当从 H3 已生成的陆远台词里取** —— 同一个嗓子。

时间点来自 tools/gen_ep01_h3.py 提示词里写死的动作时间轴（不是猜的）。

输出：releases/2026-09-12_ep01配音/_参考音色/
  ref_陆远.wav   （H3 里陆远几句独白拼成，约 7 秒）
  ref_老头.wav   （H3 里老头两句拼成，约 5 秒）
  ref_年轻人.wav （备用）
"""
import subprocess
from pathlib import Path

FFMPEG = r"C:\Users\oo\anaconda3\envs\indextts\Library\bin\ffmpeg.exe"
ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
VID = ROOT / "releases" / "2026-09-12_ep01视频"
OUT = ROOT / "releases" / "2026-09-12_ep01配音" / "_参考音色"
TMP = OUT / "_tmp"

# 角色 → [(镜号, 起, 止, 说明)]  时间轴源自 H3 提示词 beats
CUTS = {
    "陆远": [
        ("s18_怎么修好的", 2.6, 5.4, "没修好。它没坏。一个开关的事。"),
        ("s21_三种人", 5.8, 8.0, "我是旧人。旧人靠吃饭活着。"),
        ("s11_把家卖了", 1.2, 3.2, "包括我记得的东西。"),
    ],
    "老头": [
        ("s18_怎么修好的", 0.5, 2.4, "你……怎么修好的。"),
        ("s20_别往新城区说", 0.5, 4.0, "修得好。不过这事儿，别往新城区说。"),
    ],
    "年轻人": [
        ("s21_三种人", 2.6, 5.6, "一接，什么都有。何必费这个劲。"),
        ("s21_三种人", 8.2, 12.2, "城里只有三种人吃东西。……你是哪种。"),
    ],
}


def cut(mp4: Path, t0: float, t1: float, dst: Path):
    cmd = [FFMPEG, "-y", "-i", str(mp4),
           "-af", "atrim=start=%.2f:end=%.2f,asetpts=PTS-STARTPTS,"
                  "highpass=f=80,lowpass=f=8000,volume=1.4" % (t0, t1),
           "-ar", "24000", "-ac", "1", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = dst.exists() and dst.stat().st_size > 2000
    print("    %-22s %5.1f-%5.1f s  %s" % (mp4.name, t0, t1, "OK" if ok else "FAIL"))
    if not ok:
        print("      ", r.stderr.strip()[-250:])
    return ok


def concat(parts, dst: Path):
    lst = TMP / (dst.stem + "_list.txt")
    lst.write_text("\n".join("file '%s'" % str(p.resolve()).replace("\\", "/") for p in parts),
                   encoding="utf-8")
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
           "-ar", "24000", "-ac", "1", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return dst.exists() and dst.stat().st_size > 4000


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for who, items in CUTS.items():
        print("== %s ==" % who)
        parts = []
        for shot, t0, t1, note in items:
            src = VID / (shot + ".mp4")
            if not src.exists():
                print("    缺片:", src.name); continue
            seg = TMP / ("%s_%s_%s.wav" % (who, shot.split("_")[0], t0))
            if cut(src, t0, t1, seg):
                parts.append(seg)
        if not parts:
            print("    无可用片段"); continue
        dst = OUT / ("ref_%s.wav" % who)
        if concat(parts, dst):
            import struct
            data = dst.read_bytes()
            i = data.find(b'data')
            dur = struct.unpack('<I', data[i + 4:i + 8])[0] / 24000 if i > 0 else 0
            print("    -> %s  %.1f 秒  %.0f KB" % (dst.name, dur, dst.stat().st_size / 1024))
        else:
            print("    拼接失败")
    print("\n输出目录:", OUT)
    print("用途：tts.py --ref <ref_陆远.wav> --text \"旁白文本\" --out x.wav")


if __name__ == "__main__":
    main()
