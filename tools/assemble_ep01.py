# -*- coding: utf-8 -*-
"""ep01 成片装配：拼接 → 混音（V.O. 按**绝对时间**叠加）→ 放大烧字幕 → 导出。

依赖：
  · releases/2026-09-12_ep01视频/sXX_*.mp4       （H3 成片，含声景 + 中文对白）
  · releases/2026-09-12_ep01配音/_清单.json       （tools/tts_vo.py 产出，含每句入点/时长）

⚠️ 架构决定（2026-09-12 踩坑后改）：**混音在拼接之后做，按整片绝对时间定位。**
  若在单镜内混音，"amix=inputs=N:duration=first" 会以视频长度为准 → **超出镜长的旁白被截断**
  （s01 旁白 3.34s、从 3.6s 起，镜长只 5.88s → 必被切）。
  放在整片上做，旁白可以**自然跨过剪辑点**——这也是内心独白的常规处理。

三段式（每步产物都留在磁盘，便于返工）：
  ① _工作文件/_无字幕整集.mp4        concat 拼接（-c copy）
  ② _工作文件/_混音整集.mp4          V.O. 绝对时间叠加（只重编音频，视频 copy）
  ③ _成片_ep01_1080x1920_字幕.mp4    放大 + 烧硬字幕（重编码）

用法：
  python tools/assemble_ep01.py            # 全流程
  python tools/assemble_ep01.py concat     # 只做①
  python tools/assemble_ep01.py mix        # 只做②
  python tools/assemble_ep01.py burn       # 只做③
"""
import json, subprocess, sys
from pathlib import Path

FFMPEG = r"C:\Users\oo\anaconda3\envs\indextts\Library\bin\ffmpeg.exe"
# ⚠️ conda 那个 ffmpeg 是精简构建：**没有 libx264**（`-preset` 会报 Unrecognized option）。
# ComfyUI 自带的 imageio-ffmpeg 7.1 才是完整版（libx264 + libass + freetype + fontconfig）→ 优先用它。
_FF_FULL = r"D:\ai\ComfyUI-V30\python\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
if Path(_FF_FULL).exists():
    FFMPEG = _FF_FULL

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
VID = ROOT / "releases" / "2026-09-12_ep01视频"
VOICE = ROOT / "releases" / "2026-09-12_ep01配音"
WORK = VID / "_工作文件"

# 1080×1920 竖屏字幕样式（抖音安全区：底部上移 260px）
SUB_STYLE = ("FontName=Microsoft YaHei,FontSize=54,PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,"
             "Alignment=2,MarginV=260")

# V.O. 混音质感："心里的话"——压低、略闷
VO_FILTER = "volume=0.62,lowpass=f=7000"


def duration(p):
    r = subprocess.run([FFMPEG, "-i", str(p)], capture_output=True, text=True)
    try:
        s = r.stderr.split("Duration:")[1].split(",")[0].strip()
        h, m, sec = s.split(":")
        return int(h) * 3600 + int(m) * 60 + float(sec)
    except Exception:
        return 0.0


def shots():
    return sorted(p for p in VID.glob("s[0-9][0-9]_*.mp4"))


def concat():
    WORK.mkdir(parents=True, exist_ok=True)
    fs = shots()
    if not fs:
        print("  ✗ 没找到单镜文件"); return None
    lst = WORK / "concat.txt"
    lst.write_text("\n".join("file '%s'" % str(p.resolve()).replace("\\", "/") for p in fs),
                   encoding="utf-8")
    out = WORK / "_无字幕整集.mp4"
    r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        print("  ✗ concat"); print("   ", r.stderr.strip()[-400:]); return None
    print("① 拼接 %d 镜 -> %s  %.2f 秒  %.1f MB"
          % (len(fs), out.name, duration(out), out.stat().st_size / 1e6))
    return out


def mix(src):
    """在整片上按绝对时间叠加 V.O./画外音，并生成 SRT（音频与字幕同源，不会错位）。"""
    fs = shots()
    man = json.loads((VOICE / "_清单.json").read_text(encoding="utf-8"))
    # 镜号 -> (绝对起点, 镜长)
    off, dur_of, t = {}, {}, 0.0
    for p in fs:
        k = p.stem.split("_")[0]
        d = duration(p)
        off[k] = t
        dur_of[k] = d
        t += d

    # ⚠️ 入点收敛：旁白不能越过本镜（否则跨剪辑点，字幕会压在下一个场景上）
    #    place = min(原计划, 镜长 − 旁白时长 − 余量)，且不早于 0.3s
    for m in man:
        k = m["id"][:3]
        shot_d = dur_of.get(k, 99.0)
        place = min(float(m["at"]), max(0.3, shot_d - float(m["dur"]) - 0.2))
        m["place"] = round(max(0.3, place), 3)
        m["abs"] = round(off.get(k, 0.0) + m["place"], 3)

    man.sort(key=lambda x: x["abs"])

    if not man:
        print("  ✗ _清单.json 为空"); return None
    ins, fc, tags = [], [], []
    for i, m in enumerate(man, start=1):
        f = VOICE / m["file"]
        if not f.exists():
            print("   缺", f.name); continue
        ins.append(str(f))
        d = int(m["abs"] * 1000)
        fc.append("[%d:a]adelay=%d|%d,%s[v%d]" % (i, d, d, VO_FILTER, i))
        tags.append("[v%d]" % i)
    fc.append("[0:a]volume=1.0[h3]")
    fc.append("%s[h3]amix=inputs=%d:duration=first:dropout_transition=0:normalize=0[aout]"
              % ("".join(tags), len(tags) + 1))
    out = WORK / "_混音整集.mp4"
    cmd = [FFMPEG, "-y", "-i", str(src)] + sum([["-i", s] for s in ins], []) + \
          ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[aout]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("  ✗ mix"); print("   ", r.stderr.strip()[-600:]); return None
    print("② 混入 %d 句旁白/画外音 -> %s  %.1f MB" % (len(ins), out.name, out.stat().st_size / 1e6))
    for m in man:
        print("    %-5s %-4s 镜内 %5.2f s → 全片 %7.2f s  时长 %.2f s  字幕 %.2f–%.2f"
              % (m["id"], m["who"], m["place"], m["abs"], m["dur"],
                 m["abs"], m["abs"] + m["dur"]))
    build_srt(off, man)
    return out


# 全片字幕表——**只含 H3 生成的对白**。
# 旁白（V.O.）与画外音的字幕不写在这里，而是由 `_清单.json` 的实际放置时间生成
# （见 build_srt），保证字幕与声音**同源、绝不错位**。
# (镜号, 角色, 相对起, 相对止, 文本)  时间来自 tools/gen_ep01_h3.py 提示词里的动作时间轴
LINES = [
    ("s04", "大姐", 1.7, 3.6, "让你的模型来问。"),
    ("s05", "摊主", 0.5, 2.2, "你没登记吧。"),
    ("s05", "陆远", 2.4, 3.6, "……怎么登记？"),
    ("s05", "摊主", 3.7, 7.9, "去配给点。无证人员有救助配额。"),
    ("s05", "摊主", 8.1, 10.7, "先去领上。不然你连今天都过不去。"),
    ("s07", "系统", 0.4, 3.9, "正在核验。核验失败——您不在系统内。"),
    ("s07", "陆远", 4.2, 6.5, "我知道。所以我来登记。"),
    ("s08", "系统", 0.5, 2.0, "登记需要预约。"),
    ("s08", "陆远", 2.2, 3.2, "那我预约。"),
    ("s08", "系统", 3.4, 5.0, "预约需要身份。"),
    ("s08", "陆远", 5.2, 6.4, "那我没身份。"),
    ("s08", "系统", 6.6, 8.0, "检测到矛盾。"),
    ("s09", "系统", 0.5, 7.5, "建议方案 A：申请临时身份，审核周期四至六周。方案 B：签署样本代理协议，即时生效，效率最优。"),
    ("s09", "陆远", 7.9, 10.6, "方案 B 是什么。"),
    ("s10", "系统", 0.5, 6.1, "将您的经历授权予模型公司，作为训练样本，即时获得配额。约 17% 的无证人员选这个。"),
    ("s10", "陆远", 6.4, 8.6, "……哪部分经历。"),
    ("s11", "系统", 0.5, 1.0, "全部。"),
    ("s11", "陆远", 1.2, 3.2, "包括我记得的东西。"),
    ("s11", "系统", 3.4, 5.0, "记忆是经历的存储形式。"),
    ("s11", "陆远", 5.3, 7.6, "……你们让我把家卖了。"),
    ("s11", "系统", 7.9, 9.4, "系统不评价方案，只提供方案。"),
    ("s18", "老头", 0.6, 2.4, "你……怎么修好的。"),
    ("s18", "陆远", 2.7, 5.4, "没修好。它没坏。一个开关的事。"),
    ("s20", "老头", 0.6, 3.9, "修得好。不过这事儿，别往新城区说。"),
    ("s20", "陆远", 4.2, 5.1, "为什么。"),
    ("s20", "老头", 5.5, 10.9, "均衡局判过死的东西，你让它又喘上气了。它们不爱听这个。"),
    ("s21", "年轻人", 0.5, 1.2, "好吃吗。"),
    ("s21", "陆远", 1.5, 2.4, "能咽下去。"),
    ("s21", "年轻人", 2.7, 5.5, "一接，什么都有。何必费这个劲。"),
    ("s21", "陆远", 5.9, 8.0, "我是旧人。旧人靠吃饭活着。"),
    ("s21", "年轻人", 8.3, 12.1, "城里只有三种人吃东西。有钱人，要死的人，不在系统里的。你是哪种。"),
    ("s22", "陆远", 0.5, 1.5, "你猜。"),
]

# 旁白/画外音的字幕文本（音频 id → 显示文本）
# 注意：TTS 输入用中文数字（"二零五五"）以防 Windows 下规范化失效读错，
#       字幕显示用阿拉伯数字（"2055"）。
VO_SUB = {
    "s01": "我到 2055 年的第一个晚上，试了七面墙。",
    "s02": "手写的字。这个时代没人写了。",
    "s03": "我得先弄明白一件事：我在这儿，算什么东西。",
    "s17": "2026 年的。……跟我一样，没人要了。",
    "s23": "跟我手里这个，一样。",
    "s25": "……不是放电。",
    "s19a": "修好的，能换钱。规矩。",
    "s19b": "……谢谢。",
}


def _ts(t):
    ms = int(round((t - int(t)) * 1000)); sec = int(t)
    if ms == 1000:
        ms = 0; sec += 1
    h, rem = divmod(sec, 3600); m, s = divmod(rem, 60)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def build_srt(off, man=None):
    """对白用固定表；旁白/画外音用**实际放置时间**（与音频同源，不与声音错位）。"""
    entries = []
    n_dlg = 0
    for shot, who, a, b, txt in LINES:
        if shot in off:
            entries.append((off[shot] + a, off[shot] + b, txt))
            n_dlg += 1
    n_vo = 0
    for m in (man or []):
        txt = VO_SUB.get(m["id"])
        if txt:
            entries.append((m["abs"], m["abs"] + m["dur"], txt))
            n_vo += 1
    entries.sort()
    srt = WORK / "ep01.srt"
    with open(srt, "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(entries, 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, _ts(a), _ts(b), txt))
    print("   字幕 %d 条（对白 %d + 旁白/画外 %d）-> %s" % (len(entries), n_dlg, n_vo, srt.name))
    return srt


def burn(src):
    srt = WORK / "ep01.srt"
    if not srt.exists():
        # 需要镜长才能定位；先由 concat 阶段生成
        fs = shots(); off, t = {}, 0.0
        for p in fs:
            off[p.stem.split("_")[0]] = t; t += duration(p)
        build_srt(off)
    out = VID / "_成片_ep01_1080x1920_字幕.mp4"
    # ⚠️ Windows 盘符 ':' 在 ffmpeg 滤镜里要转义，易踩坑 →
    # 规避：cwd 切到字幕目录，滤镜里只写文件名（无盘符、无冒号）
    fc = ("[0:v]scale=1080:1920:flags=lanczos,setsar=1,"
          "subtitles=%s:force_style='%s'[v]" % (srt.name, SUB_STYLE))
    cmd = [FFMPEG, "-y", "-i", str(src), "-filter_complex", fc,
           "-map", "[v]", "-map", "0:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    print("③ 放大 1080×1920 + 烧字幕…（最慢的一步）")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(WORK))
    if r.returncode != 0:
        print("  ✗ burn"); print("   ", r.stderr.strip()[-600:]); return
    print("③ 成片 -> %s  %.1f MB  %.2f 秒"
          % (out.name, out.stat().st_size / 1e6, duration(out)))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    WORK.mkdir(parents=True, exist_ok=True)
    if step == "concat":
        concat()
    elif step == "mix":
        m = WORK / "_无字幕整集.mp4"
        mix(m if m.exists() else concat())
    elif step == "burn":
        m = WORK / "_混音整集.mp4"
        burn(m if m.exists() else WORK / "_无字幕整集.mp4")
    else:
        s = concat()
        if s:
            mx = mix(s)
            if mx:
                burn(mx)
