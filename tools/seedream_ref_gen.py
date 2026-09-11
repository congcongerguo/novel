# -*- coding: utf-8 -*-
"""Seedream 5.0 Pro（火山方舟）带参考图生图 —— 角色一致性路径
用法:
  python seedream_ref_gen.py <out_png> <ref_png_1> [ref_png_2] ... --prompt "<提示词>"
说明:
  - 参考图以 base64 data URI 传入 image 字段（Pro 支持单/多图参考）
  - 提示词里用 "image 1"/"image 2" 指代参考图；支持 1000x1000 归一化坐标定位
"""
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL = "doubao-seedream-5-0-pro-260628"

env_path = Path.home() / ".workbuddy" / ".env"
api_key = None
for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("ARK_API_KEY="):
        api_key = line.split("=", 1)[1].strip()
        break
if not api_key:
    sys.exit("ERROR: 未找到 ARK_API_KEY")


def data_uri(p):
    p = Path(p)
    ext = p.suffix.lower().lstrip(".") or "png"
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "png")
    return "data:image/%s;base64,%s" % (mime, base64.b64encode(p.read_bytes()).decode())


def main():
    args = sys.argv[1:]
    if "--prompt" not in args:
        sys.exit("need --prompt")
    pi = args.index("--prompt")
    prompt = args[pi + 1]
    rest = args[:pi]
    out = rest[0]
    refs = rest[1:]

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "response_format": "url",
        "size": "2K",
        "output_format": "png",
        "watermark": False,
    }
    if refs:
        payload["image"] = [data_uri(r) for r in refs] if len(refs) > 1 else data_uri(refs[0])

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key},
        method="POST",
    )
    print("请求中 model=%s refs=%d ..." % (MODEL, len(refs)))
    t0 = datetime.now()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("HTTP %s: %s" % (e.code, e.read().decode("utf-8", errors="replace")[:1500]))
        sys.exit(1)

    print("耗时 %.1fs" % (datetime.now() - t0).total_seconds())
    data = result.get("data") or []
    if not data:
        print(json.dumps(result, ensure_ascii=False)[:1500])
        sys.exit(1)
    url = data[0].get("url")
    print("url:", url)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(out, "wb") as f:
        f.write(r.read())
    print("SAVED", out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
