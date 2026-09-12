# -*- coding: utf-8 -*-
"""ep01 成片装配（v2）：拼接 → 混音（旁白/画外音 + 底乐 + 动作音效）→ ASS 字幕 → 片头片尾黑场 → 导出。

依赖：
  · releases/2026-09-12_ep01_成片包/03_镜头视频/sXX_*.mp4          H3 成片（声景 + 中文对白）
  · releases/2026-09-12_ep01_成片包/04_配音与音效/_清单.json          tools/tts_vo.py 产出（旁白/画外音）
  · releases/2026-09-12_ep01_成片包/04_配音与音效/_底乐/ep01_底乐.wav  tools/make_music.py 产出
  · releases/2026-09-12_ep01_成片包/04_配音与音效/_音效/*.wav          tools/make_sfx.py 产出

⚠️ 三条关键工程决定（都踩过坑）：
 ① **混音必须在拼接之后、按整片绝对时间做**——单镜内混音会被 `amix duration=first` 按镜长截断
 ② **字幕用 ASS 不用 SRT**——需要"角色配色 + 关键词高亮"，SRT 做不到逐字样式
 ③ **片头片尾黑场用 tpad 加在字幕之后**——字幕已烘进帧里，加黑场不会打乱时间轴；
    音频用 `adelay + apad` 对齐（否则音画不同步）

用法：
  python tools/assemble_ep01.py            # 全流程
  python tools/assemble_ep01.py concat | mix | burn
"""
import json, subprocess, sys
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P

FFMPEG = r"C:\Users\oo\anaconda3\envs\indextts\Library\bin\ffmpeg.exe"
# ⚠️ conda 那个 ffmpeg 是精简构建：**没有 libx264**（`-preset` 报 Unrecognized option）。
# ComfyUI 自带的 imageio-ffmpeg 7.1 才是完整版（libx264 + libass + freetype + fontconfig）→ 优先用它。
_FF_FULL = r"D:\ai\ComfyUI-V30\python\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
if Path(_FF_FULL).exists():
    FFMPEG = _FF_FULL

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
VID = P.EP01_VIDEOS
VOICE = P.EP01_AUDIO
WORK = P.EP01_MID
MUSIC = P.EP01_MUSIC / "ep01_底乐.wav"
SFX_DIR = P.EP01_SFX

# ── 混音音量（相对值）──
MUSIC_VOL = 0.30        # 底乐：0.16 时独奏只有 −33.5 dBFS（手机喇叭基本听不见）→ 抬到约 −29 dBFS
                        #        仍比台词低约 12 dB，属"极轻"，但能感觉到。要更明显/更轻改这一个数即可
VO_VOL = 0.62           # 旁白：压低、略闷（"心里的话"）
SFX_VOL = 0.50          # 动作音效

# ── 片头/片尾黑场（秒）──
HEAD_BLACK = 0.5
TAIL_BLACK = 2.0

# ── ASS 字幕样式（颜色是 &HAABBGGRR，注意是 BGR 不是 RGB）──
ASS_STYLES = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: 对白,Microsoft YaHei,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0.5,0,1,3,1,2,70,70,260,134
Style: 系统,Microsoft YaHei,54,&H00E8E6C8,&H00E8E6C8,&H00000000,&H80000000,0,0,0,0,100,100,0.5,0,1,3,1,2,70,70,260,134
Style: 旁白,Microsoft YaHei,52,&H00C0E0F0,&H00C0E0F0,&H00000000,&H80000000,0,0,0,0,100,100,0.5,0,1,3,1,2,70,70,260,134

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# 关键词高亮的暖琥珀色（BGR of #FFC860）+ 加粗
HL_ON = r"{\b1\c&H0060C8FF&}"
HL_OFF = r"{\r}"          # \r = 回到该角色样式（对白=白 / 系统=淡青 / 旁白=淡暖）
                          # ⚠️ 不要写 `{\b0\c}`——`\c` 不带值是非法写法


def duration(p):
    r = subprocess.run([FFMPEG, "-i", str(p)], capture_output=True, text=True)
    try:
        s = r.stderr.split("Duration:")[1].split(",")[0].strip()
        h, m, sec = s.split(":")
        return int(h) * 3600 + int(m) * 60 + float(sec)
    except Exception:
        return 0.0


def audio_duration(p):
    """只量音轨长度。
    ⚠️ 必须有这个：容器时长由视频流决定，**音轨被截断时容器时长完全看不出来**
    （曾因此把 231 秒音轨截成 5.7 秒却没发现）。"""
    import json as _json
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(p), "-map", "0:a",
                        "-f", "null", "-"], capture_output=True, text=True)
    # 从 "time=00:03:50.49" 取最后一条
    t = None
    for line in r.stderr.splitlines():
        if "time=" in line:
            for part in line.split():
                if part.startswith("time="):
                    t = part[5:]
    if not t or t.startswith("-"):
        return 0.0
    h, m, sec = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(sec)


def shots():
    return sorted(p for p in VID.glob("s[0-9][0-9]_*.mp4"))


def timeline():
    """镜号 -> (绝对起点, 镜长)"""
    off, dur_of, t = {}, {}, 0.0
    for p in shots():
        k = p.stem.split("_")[0]
        d = duration(p)
        off[k] = t; dur_of[k] = d; t += d
    return off, dur_of


# ─────────────── ① 拼接 ───────────────
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


# ─────────────── ② 混音（旁白 + 画外音 + 底乐 + 音效）───────────────
def mix(src):
    off, dur_of = timeline()
    man = json.loads((P.EP01_VO / "_清单.json").read_text(encoding="utf-8"))
    # 入点收敛：旁白不能越过本镜（否则字幕压在下一个场景上）
    for m in man:
        k = m["id"][:3]
        sd = dur_of.get(k, 99.0)
        m["place"] = round(max(0.3, min(float(m["at"]), max(0.3, sd - float(m["dur"]) - 0.2))), 3)
        m["abs"] = round(off.get(k, 0.0) + m["place"], 3)
    man.sort(key=lambda x: x["abs"])

    # 动作音效的绝对入点（取自 gen_ep01_h3.py 里写死的动作时间轴）
    sfx = []
    for name, shot, rel, vol in [
        ("sfx_machine_机器嗡.wav", "s16", 3.01, 0.55),   # 继电器/嗡起（s16 机器在 3.2s 应答）
        ("sfx_screen_屏亮.wav",    "s24", 0.23, 0.40),   # 集尾手机屏
        ("sfx_current_电流变化.wav", "s25", 2.28, 0.45),  # 那一下（不是放电）
    ]:
        f = SFX_DIR / name
        if f.exists():
            sfx.append(dict(file=str(f), abs=round(off.get(shot, 0.0) + rel, 3), vol=vol))

    ins, fc, tags = [str(src)], [], []
    n = 0
    # ⚠️⚠️ 关键：amix 的 `duration=first` 取的是**输入列表里的第一个**。
    # 所以必须让 [h3]（整集原声，最长）排在**第一位**——否则会被第一个旁白片段的
    # 长度截断（曾因此把 231 秒的音轨截成 5.7 秒，且容器时长看不出来！）
    # 各输入统一转 44100 立体声，避免采样率/声道不一致导致的隐性转换问题。
    FMT = "aformat=sample_rates=44100:channel_layouts=stereo"
    fc.append("[0:a]%s,volume=1.0[h3]" % FMT)
    tags.append("[h3]")
    for m in man:
        f = P.EP01_VO / m["file"]
        if not f.exists():
            print("   缺旁白", f.name); continue
        n += 1; ins.append(str(f))
        d = int(m["abs"] * 1000)
        fc.append("[%d:a]%s,adelay=%d:all=1,volume=%.2f,lowpass=f=7000[vo%d]"
                  % (n, FMT, d, VO_VOL, n))
        tags.append("[vo%d]" % n)
    for i, s in enumerate(sfx, start=1):
        n += 1; ins.append(s["file"])
        d = int(s["abs"] * 1000)
        fc.append("[%d:a]%s,adelay=%d:all=1,volume=%.2f[sf%d]"
                  % (n, FMT, d, s["vol"], i))
        tags.append("[sf%d]" % i)
    if MUSIC.exists():
        n += 1; ins.append(str(MUSIC))
        fc.append("[%d:a]%s,volume=%.2f[mus]" % (n, FMT, MUSIC_VOL))
        tags.append("[mus]")
    fc.append("%samix=inputs=%d:duration=first:dropout_transition=0:normalize=0[aout]"
              % ("".join(tags), len(tags)))

    out = WORK / "_混音整集.mp4"
    cmd = [FFMPEG, "-y", "-i", str(src)] + sum([["-i", s] for s in ins[1:]], []) + \
          ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[aout]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("  ✗ mix"); print("   ", r.stderr.strip()[-700:]); return None

    # ⚠️ 自检：音轨长度必须与视频相当，否则说明 amix 又被截断了
    vd, ad = duration(out), audio_duration(out)
    if ad < vd - 1.0:
        print("  ✗✗ 自检失败：混音后音轨只有 %.2f 秒，视频 %.2f 秒 —— 音轨被截断！" % (ad, vd))
        print("     检查 amix 输入顺序：duration=first 要求 [h3] 必须排在第一位")
        return None
    print("② 混音 -> %s  视频 %.2f 秒 / 音轨 %.2f 秒  %.1f MB"
          % (out.name, vd, ad, out.stat().st_size / 1e6))
    print("   旁白/画外音 %d 句：" % len(man))
    for m in man:
        print("     %-5s %-4s 镜内 %5.2f → 全片 %7.2f  时长 %.2f"
              % (m["id"], m["who"], m["place"], m["abs"], m["dur"]))
    print("   动作音效 %d 个：" % len(sfx))
    for s in sfx:
        print("     %-24s 全片 %7.2f" % (Path(s["file"]).name, s["abs"]))
    print("   底乐：%s（volume %.2f）" % ("已混入" if MUSIC.exists() else "缺文件", MUSIC_VOL))
    build_ass(off, man)
    return out


# ─────────────── ASS 字幕 ───────────────
# 对白字幕：(镜号, 角色风格, 相对起, 相对止, 文本, 关键词)
#  角色风格 → ASS 样式名：对白 / 系统 / 旁白
LINES = [
    ("s04", "对白", 1.7, 3.6, "让你的模型来问。", ["模型"]),
    ("s05", "对白", 0.5, 2.2, "你没登记吧。", ["登记"]),
    ("s05", "对白", 2.4, 3.6, "……怎么登记？", []),
    ("s05", "对白", 3.7, 7.9, "去配给点。无证人员有救助配额。", ["无证人员", "救助配额"]),
    ("s05", "对白", 8.1, 10.7, "先去领上。不然你连今天都过不去。", []),
    ("s07", "系统", 0.4, 3.9, "正在核验。核验失败——您不在系统内。", ["不在系统内"]),
    ("s07", "对白", 4.2, 6.5, "我知道。所以我来登记。", []),
    ("s08", "系统", 0.5, 2.0, "登记需要预约。", []),
    ("s08", "对白", 2.2, 3.2, "那我预约。", []),
    ("s08", "系统", 3.4, 5.0, "预约需要身份。", []),
    ("s08", "对白", 5.2, 6.4, "那我没身份。", []),
    ("s08", "系统", 6.6, 8.0, "检测到矛盾。", ["矛盾"]),
    ("s09", "系统", 0.5, 7.5, "建议方案 A：申请临时身份，审核周期四至六周。方案 B：签署样本代理协议，即时生效，效率最优。", ["方案 B", "效率最优"]),
    ("s09", "对白", 7.9, 10.6, "方案 B 是什么。", ["方案 B"]),
    ("s10", "系统", 0.5, 6.1, "将您的经历授权予模型公司，作为训练样本，即时获得配额。约 17% 的无证人员选这个。", ["经历", "训练样本"]),
    ("s10", "对白", 6.4, 8.6, "……哪部分经历。", []),
    ("s11", "系统", 0.5, 1.0, "全部。", []),
    ("s11", "对白", 1.2, 3.2, "包括我记得的东西。", []),
    ("s11", "系统", 3.4, 5.0, "记忆是经历的存储形式。", ["存储形式"]),
    ("s11", "对白", 5.3, 7.6, "……你们让我把家卖了。", ["把家卖了"]),
    ("s11", "系统", 7.9, 9.4, "系统不评价方案，只提供方案。", []),
    ("s18", "对白", 0.6, 2.4, "你……怎么修好的。", []),
    ("s18", "对白", 2.7, 5.4, "没修好。它没坏。一个开关的事。", ["没坏", "一个开关"]),
    ("s20", "对白", 0.6, 3.9, "修得好。不过这事儿，别往新城区说。", ["别往新城区说"]),
    ("s20", "对白", 4.2, 5.1, "为什么。", []),
    ("s20", "对白", 5.5, 10.9, "均衡局判过死的东西，你让它又喘上气了。它们不爱听这个。", ["均衡局", "判过死"]),
    ("s21", "对白", 0.5, 1.2, "好吃吗。", []),
    ("s21", "对白", 1.5, 2.4, "能咽下去。", []),
    ("s21", "对白", 2.7, 5.5, "一接，什么都有。何必费这个劲。", []),
    ("s21", "对白", 5.9, 8.0, "我是旧人。旧人靠吃饭活着。", ["旧人", "吃饭"]),
    ("s21", "对白", 8.3, 12.1, "城里只有三种人吃东西。有钱人，要死的人，不在系统里的。你是哪种。", ["三种人", "不在系统里"]),
    ("s22", "对白", 0.5, 1.5, "你猜。", []),
]

# 旁白/画外音：音频 id → (显示文本, 关键词, 样式)
VO_SUB = {
    "s01":  ("我到 2055 年的第一个晚上，试了七面墙。", ["2055", "七面墙"], "旁白"),
    "s02":  ("手写的字。这个时代没人写了。", ["手写的字"], "旁白"),
    "s03":  ("我得先弄明白一件事：我在这儿，算什么东西。", ["算什么东西"], "旁白"),
    "s17":  ("2026 年的。……跟我一样，没人要了。", ["2026", "没人要了"], "旁白"),
    "s23":  ("跟我手里这个，一样。", [], "旁白"),
    "s25":  ("……不是放电。", ["不是放电"], "旁白"),
    "s19a": ("修好的，能换钱。规矩。", ["规矩"], "对白"),
    "s19b": ("……谢谢。", [], "对白"),
}


def _ass_ts(sec):
    cs = int(round(sec * 100)); h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000); s, c = divmod(rem, 100)
    return "%d:%02d:%02d.%02d" % (h, m, s, c)


def wrap_text(s, maxlen=15):
    """手动折行：超过 maxlen 就在最近的标点处断，最多两行"""
    if len(s) <= maxlen:
        return s
    best = -1
    for i, ch in enumerate(s):
        if ch in "。，、？！：—…" and 4 <= i <= maxlen:
            best = i
    if best == -1:
        best = min(maxlen, len(s) - 1)
    return s[:best + 1] + r"\N" + s[best + 1:]


def hl(s, kws):
    """关键词高亮；先长后短，避免短词吃掉长词"""
    for k in sorted(kws, key=len, reverse=True):
        if k in s:
            s = s.replace(k, HL_ON + k + HL_OFF, 1)
    return s


def build_ass(off, man=None):
    rows = []
    for shot, style, a, b, txt, kws in LINES:
        if shot in off:
            rows.append((off[shot] + a, off[shot] + b, style, hl(wrap_text(txt), kws)))
    for m in (man or []):
        v = VO_SUB.get(m["id"])
        if v:
            txt, kws, style = v
            rows.append((m["abs"], m["abs"] + m["dur"], style, hl(wrap_text(txt), kws)))
    rows.sort()
    ass = WORK / "ep01.ass"
    with open(ass, "w", encoding="utf-8") as f:
        f.write(ASS_STYLES)
        for a, b, style, txt in rows:
            f.write("Dialogue: 0,%s,%s,%s,,0,0,0,,%s\n" % (_ass_ts(a), _ass_ts(b), style, txt))
    n_hl = sum(1 for r in rows if HL_ON in r[3])
    print("   字幕 %d 条（含关键词高亮 %d 条）-> %s" % (len(rows), n_hl, ass.name))
    return ass


# ─────────────── ③ 放大 + 烧字幕 + 片头片尾黑场 ───────────────
def burn(src):
    ass = WORK / "ep01.ass"
    if not ass.exists():
        off, _ = timeline(); build_ass(off)
    total = duration(src) + HEAD_BLACK + TAIL_BLACK
    out = P.EP01_FINAL / "_成片_ep01_1080x1920_字幕.mp4"
    # 顺序很重要：先烧字幕（时间轴=原始），再用 tpad 加黑场（字幕已烘进帧，不会错位）
    fc = ("[0:v]scale=1080:1920:flags=lanczos,setsar=1,"
          "subtitles=%s,"
          "tpad=start_duration=%.2f:start_mode=add:stop_duration=%.2f:stop_mode=add:color=black[v];"
          "[0:a]adelay=%d:all=1,apad=pad_dur=%.2f[a]"
          % (ass.name, HEAD_BLACK, TAIL_BLACK, int(HEAD_BLACK * 1000), TAIL_BLACK))
    cmd = [FFMPEG, "-y", "-i", str(src), "-filter_complex", fc,
           "-map", "[v]", "-map", "[a]", "-t", "%.3f" % total,
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    print("③ 放大 1080×1920 + 烧 ASS 字幕 + 片头 %.1fs/片尾 %.1fs 黑场…" % (HEAD_BLACK, TAIL_BLACK))
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(WORK))
    if r.returncode != 0:
        print("  ✗ burn"); print("   ", r.stderr.strip()[-700:]); return
    vd, ad = duration(out), audio_duration(out)
    tag = "" if ad >= vd - 1.0 else "   ✗✗ 音轨不足！"
    print("③ 成片 -> %s  %.1f MB  视频 %.2f 秒 / 音轨 %.2f 秒%s"
          % (out.name, out.stat().st_size / 1e6, vd, ad, tag))


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
