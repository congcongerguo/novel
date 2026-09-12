# -*- coding: utf-8 -*-
"""H3 节点模式对比测试：找出"能锁住首帧"的接法。

背景（2026-09-12）：
  我原先用的 `MiniMaxH3ReferenceToVideo`（= 参考图生视频模式）**没有 first_frame 输入**，
  参考图只作身份/风格参考，因此视频画面与首帧脱钩（问题①）。经像素比对确认：
  新 ep01（corr 0.13）与旧 ep02（corr 0.09）都是同一现象，即"从来没锁住过"。

  `Yuan_MiniMaxH3Video` 是包装节点，mode 可选：
    · 图生视频        → first_frame / last_frame 作为**几何锚点**
    · 参考图生视频    → <Picture i> 参考

本脚本对同一镜跑三种配置，输出可比对的成片 + 指标：
  i2v        ：图生视频模式，只给 first_frame（最纯粹的首帧锁定）
  i2v_ref    ：图生视频模式，同时给 first_frame + ref_image_2/3（定妆卡/全身正面），看参考图是否被接受
  ref        ：参考图生视频模式（当前做法，作对照）

用法：
  python test_h3_modes.py s04             # 默认测 s04（有对白，可验证中文语音）
  python test_h3_modes.py s01 i2v ref     # 指定镜号与配置
输出：releases/2026-09-12_ep01_成片包/99_历史与废弃/H3模式测试/<镜号>_<配置>.mp4
"""
import json, sys, time
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HOST = "http://127.0.0.1:8188"
S = requests.Session()
S.mount("http://", HTTPAdapter(max_retries=Retry(
    total=6, backoff_factor=1.5, status_forcelist=[500, 502, 503, 504],
    allowed_methods=frozenset(["GET", "POST"])), pool_connections=4, pool_maxsize=4))

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
FRAME_DIR = P.EP01_FRAMES
OUT_DIR = P.EP01_HIST / "H3模式测试"
CARD = ROOT / "input" / "juese" / "luyuan" / "luyuan.png"
FRONT = ROOT / "input" / "juese" / "luyuan" / "三视图" / "front.png"

sys.path.insert(0, str(ROOT / "tools"))
from gen_ep01_h3 import SHOTS, FRAME_FILE, h3_prompt, upload   # 复用已写好的提示词

# 图生视频模式用的提示词：去掉 <Picture i> 引用（该模式没有参考图通道），保留动作/声景/对白
def i2v_prompt(shot):
    s = SHOTS[shot]
    head = ("The target video is a photorealistic documentary-style vertical 9:16 shot with "
            "handheld micro-shake, shallow depth of field and floating dust in the light; "
            + s["camera"] + ".")
    body = ("[Shot 1] The shot begins exactly on the provided first frame and develops forward "
            "from it: the opening frame is held exactly, then the action develops. "
            + " ".join(s["beats"]) + " " + s["close"])
    return "\n".join([
        "summary:",
        "A single continuous shot continuing directly from the provided first frame.",
        "",
        "detailed_description:",
        head,
        body,
        "",
        "overall_soundscape: " + s["sound_text"],
        "",
        "non_diegetic_music: N/A",
    ])


def build(mode, prompt, first, seed, prefix, frames, with_refs):
    wf = {
        "119": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax\\minimax_h3_video_vae_fp16.safetensors"}},
        "120": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax\\minimax_h3_audio_vae_fp32.safetensors"}},
        "128": {"class_type": "CLIPLoader", "inputs": {"clip_name": "minimax\\qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "151": {"class_type": "DiffusionModelLoaderKJ", "inputs": {"model_name": "minimax\\minimax_h3_ref2va_pruned_int8_convrot.safetensors", "weight_dtype": "default", "compute_dtype": "default", "patch_cublaslinear": False, "sage_attention": "auto", "enable_fp16_accumulation": True}},
        "137": {"class_type": "LoadImage", "inputs": {"image": first}},
        "136": {"class_type": "Yuan_MiniMaxH3Video",
                "inputs": {"mode": mode, "clip": ["128", 0], "vae": ["119", 0], "audio_vae": ["120", 0],
                           "prompt": prompt, "width": 480, "height": 832, "length": frames,
                           "ref_image_size": "匹配",
                           "first_frame": ["137", 0]}},
        "126": {"class_type": "BasicGuider", "inputs": {"model": ["151", 0], "conditioning": ["136", 0]}},
        "124": {"class_type": "BasicScheduler", "inputs": {"model": ["151", 0], "scheduler": "simple", "steps": 25, "denoise": 1.0}},
        "123": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "129": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "125": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["129", 0], "guider": ["126", 0], "sampler": ["123", 0], "sigmas": ["124", 0], "latent_image": ["136", 1]}},
        "154": {"class_type": "VAEDecode", "inputs": {"samples": ["125", 0], "vae": ["119", 0]}},
        "121": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["125", 0], "vae": ["120", 0]}},
        "130": {"class_type": "CreateVideo", "inputs": {"images": ["154", 0], "fps": 24.0, "audio": ["121", 0], "bit_depth": 8}},
        "92": {"class_type": "SaveVideo", "inputs": {"video": ["130", 0], "filename_prefix": prefix, "format": "auto", "codec": "auto"}},
    }
    if with_refs:
        wf["139"] = {"class_type": "LoadImage", "inputs": {"image": "h3_ly_card.png"}}
        wf["145"] = {"class_type": "LoadImage", "inputs": {"image": "h3_ly_front.png"}}
        wf["136"]["inputs"]["ref_image_2"] = ["139", 0]
        wf["136"]["inputs"]["ref_image_3"] = ["145", 0]
    return wf


def run(shot, cfg):
    if cfg == "i2v":
        mode, prompt, with_refs = "图生视频", i2v_prompt(shot), False
    elif cfg == "i2v_ref":
        mode, prompt, with_refs = "图生视频", i2v_prompt(shot), True
    else:
        mode, prompt, with_refs = "参考图生视频", h3_prompt(shot), True

    s = SHOTS[shot]
    out = OUT_DIR / ("%s_%s.mp4" % (shot, cfg))
    if out.exists() and out.stat().st_size > 50_000:
        print("[%s/%s] 已存在跳过" % (shot, cfg)); return
    first = upload(P.frame_path(FRAME_FILE[shot]), "h3t_%s_first.png" % shot)
    wf = build(mode, prompt, first, 2026091290 + int(shot[1:]), "h3test/%s_%s" % (shot, cfg), s["frames"], with_refs)

    t0 = time.time()
    r = S.post(HOST + "/prompt", json={"prompt": wf}, timeout=(10, 120))
    if r.status_code != 200:
        print("[%s/%s] 提交失败 %s %s" % (shot, cfg, r.status_code, r.text[:400])); return
    pid = r.json()["prompt_id"]
    print("[%s/%s] mode=%s refs=%s pid=%s" % (shot, cfg, mode, with_refs, pid), flush=True)

    while True:
        time.sleep(15)
        try:
            h = S.get(HOST + "/history/" + pid, timeout=20).json()
        except Exception:
            continue
        if pid not in h:
            continue
        st = h[pid].get("status", {}).get("status_str")
        if st == "error":
            for m in h[pid]["status"].get("messages", []):
                if m[0] == "execution_error":
                    print("   执行错误 node=%s: %s" % (m[1].get("node_type"), str(m[1].get("exception_message"))[:400]))
            return
        for node, v in h[pid].get("outputs", {}).items():
            for key in ("videos", "gifs", "images"):
                for it in v.get(key, []) or []:
                    fn = it.get("filename")
                    if not fn:
                        continue
                    url = "%s/view?filename=%s&subfolder=%s&type=output" % (
                        HOST, requests.utils.quote(fn), requests.utils.quote(it.get("subfolder", "")))
                    OUT_DIR.mkdir(parents=True, exist_ok=True)
                    for k in range(4):
                        try:
                            with S.get(url, timeout=(10, 900), stream=True) as rr:
                                rr.raise_for_status()
                                with open(out, "wb") as f:
                                    for ch in rr.iter_content(1 << 20):
                                        f.write(ch)
                            print("[%s/%s] OK %.0fs -> %s (%.1f MB)" % (shot, cfg, time.time() - t0, out.name, out.stat().st_size / 1e6), flush=True)
                            break
                        except Exception as e:
                            print("   下载重试 %d: %s" % (k + 1, e)); time.sleep(10)
        return


if __name__ == "__main__":
    args = sys.argv[1:] or ["s04"]
    shot = args[0]
    cfgs = args[1:] or ["i2v", "i2v_ref", "ref"]
    upload(CARD, "h3_ly_card.png"); upload(FRONT, "h3_ly_front.png")
    print("角色参考已上传")
    for c in cfgs:
        try:
            run(shot, c)
        except Exception as e:
            print("[%s/%s] 异常 %s: %s" % (shot, c, type(e).__name__, e))
    print("done ->", OUT_DIR)
