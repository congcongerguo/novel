# -*- coding: utf-8 -*-
"""ep01 旁白（V.O.）+ 画外音 批量合成 —— 用 IndexTTS2，模型只加载一次。

方案 B 的分工：
  · 对白 → 由 MiniMax H3 生成（已在成片音轨里，不动）
  · V.O.（6 句旁白）与 s19 两句画外音 → 本脚本用 IndexTTS2 合成

音色来源：`tools/make_voice_refs.py` 从 H3 成片里剪出的角色真实声音，
**所以旁白与对白是同一个嗓子**，不会"旁白一个人、说话另一个人"。

⚠️ 用 IndexTTS 自己的 venv 跑（不是宿主 python）：
  C:\\Users\\oo\\WorkBuddy\\Claw\\index-tts-windows\\.venv\\Scripts\\python.exe tools\\tts_vo.py

输出：releases/2026-09-12_ep01_成片包/04_配音与音效/<镜号>_<角色>_<用途>.wav（24kHz 单声道）
另出 `_清单.json` 记录每句的时长与计划入点，供混音脚本读取。
"""
import json, sys, time, os
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P

# IndexTTS 是"本地包"（没装进 venv），必须把自己目录加进 sys.path，
# 且模型内部用相对路径（./checkpoints/hf_cache），所以 cwd 也要切过去。
ITT = r"C:\Users\oo\WorkBuddy\Claw\index-tts-windows"
sys.path.insert(0, ITT)
os.chdir(ITT)

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
MODEL_DIR = r"C:\Users\oo\WorkBuddy\Claw\index-tts-windows\checkpoints"
CFG = r"C:\Users\oo\WorkBuddy\Claw\index-tts-windows\checkpoints\config.yaml"
REF_DIR = P.EP01_REF
OUT_DIR = P.EP01_VO            # 旁白/画外音 wav（与 assemble_ep01.py 读取位置一致）

# 台词：id / 角色 / 用途 / 文本（TTS 用，数字写中文）/ 计划入点（秒，相对该镜）
# 文本与入点依据 spec/visual/ep01-配音剪辑台本.md + tools/gen_ep01_h3.py 的动作时间轴
LINES = [
    # ── V.O. 6 句（旁白，不进 H3）──
    dict(id="s01", who="陆远", kind="VO", shot="s01_插不进插座", at=3.6,
         text="我到二零五五年的第一个晚上，试了七面墙。",
         sub="我到 2055 年的第一个晚上，试了七面墙。"),
    dict(id="s02", who="陆远", kind="VO", shot="s02_碾铜脚", at=4.8,
         text="手写的字。这个时代没人写了。",
         sub="手写的字。这个时代没人写了。"),
    dict(id="s03", who="陆远", kind="VO", shot="s03_被当成噪音", at=2.8,
         text="我得先弄明白一件事：我在这儿，算什么东西。",
         sub="我得先弄明白一件事：我在这儿，算什么东西。"),
    dict(id="s17", who="陆远", kind="VO", shot="s17_屏幕光映脸", at=4.0,
         text="二零二六年的。……跟我一样，没人要了。",
         sub="2026 年的。……跟我一样，没人要了。"),
    dict(id="s23", who="陆远", kind="VO", shot="s23_插上电源", at=5.6,
         text="跟我手里这个，一样。",
         sub="跟我手里这个，一样。"),
    dict(id="s25", who="陆远", kind="VO", shot="s25_他抬起头", at=3.0,
         text="……不是放电。",
         sub="……不是放电。"),
    # ── s19 两句画外音（该镜在 H3 里是 No dialogue，手部特写，画外处理）──
    dict(id="s19a", who="老头", kind="OS", shot="s19_塞干粮硬币", at=1.4,
         text="修好的，能换钱。规矩。",
         sub="修好的，能换钱。规矩。"),
    dict(id="s19b", who="陆远", kind="OS", shot="s19_塞干粮硬币", at=4.8,
         text="……谢谢。",
         sub="……谢谢。"),
]


def main():
    print("[*] 加载 IndexTTS2 …", flush=True)
    t0 = time.time()
    from indextts.infer_v2 import IndexTTS2
    tts = IndexTTS2(model_dir=MODEL_DIR, cfg_path=CFG)
    print("[*] 模型就绪 %.0f 秒" % (time.time() - t0), flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for L in LINES:
        ref = REF_DIR / ("ref_%s.wav" % L["who"])
        if not ref.exists():
            print("[跳过] 缺参考音色 %s" % ref.name); continue
        out = OUT_DIR / ("%s_%s_%s.wav" % (L["id"], L["who"], L["kind"]))
        t = time.time()
        try:
            tts.infer(spk_audio_prompt=str(ref), text=L["text"], output_path=str(out))
        except Exception as e:
            print("[失败] %s: %s" % (L["id"], e)); continue
        # 读 wav 时长
        import wave
        try:
            with wave.open(str(out), "rb") as w:
                dur = w.getnframes() / float(w.getframerate())
        except Exception:
            dur = -1
        print("[OK] %-5s %-4s %-3s %.2f 秒  合成 %.0f 秒  入点 %.1f  → %s"
              % (L["id"], L["who"], L["kind"], dur, time.time() - t, L["at"], out.name), flush=True)
        m = dict(L); m["file"] = out.name; m["dur"] = round(dur, 3)
        manifest.append(m)

    (OUT_DIR / "_清单.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n完成 %d / %d 句 → %s" % (len(manifest), len(LINES), OUT_DIR))
    print("清单：_清单.json")


if __name__ == "__main__":
    main()
