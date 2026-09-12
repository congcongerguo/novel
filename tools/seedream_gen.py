# -*- coding: utf-8 -*-
"""调用火山方舟 Seedream 生图 API"""
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL = "doubao-seedream-5-0-pro-260628"

# 从 ~/.workbuddy/.env 读取 key
env_path = Path.home() / ".workbuddy" / ".env"
api_key = None
for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("ARK_API_KEY="):
        api_key = line.split("=", 1)[1].strip()
        break
if not api_key:
    sys.exit("ERROR: 未找到 ARK_API_KEY")

prompt = sys.argv[1] if len(sys.argv) > 1 else (
    "星际穿越，黑洞，黑洞里冲出一辆快支离破碎的复古列车，抢视觉冲击力，电影大片，"
    "末日既视感，动感，对比色，oc渲染，光线追踪，动态模糊，景深，超现实主义，深蓝，"
    "画面通过细腻的丰富的色彩层次塑造主体与场景，质感真实，暗黑风背景的光影效果营造出氛围，"
    "整体兼具艺术幻想感，夸张的广角透视效果，耀光，反射，极致的光影，强引力，吞噬"
)
size = sys.argv[2] if len(sys.argv) > 2 else "2K"

payload = {
    "model": MODEL,
    "prompt": prompt,
    "response_format": "url",
    "size": size,
    "stream": False,
    "watermark": True,
}
req = urllib.request.Request(
    API_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    },
    method="POST",
)

print(f"请求中: model={MODEL}, size={size} ...")
t0 = datetime.now()
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")
    sys.exit(1)

elapsed = (datetime.now() - t0).total_seconds()
print(f"耗时 {elapsed:.1f}s")
print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])

out_dir = Path(r"C:\Users\oo\WorkBuddy\小说未来ai\releases\seedream\2026-09-11")
out_dir.mkdir(parents=True, exist_ok=True)

for i, item in enumerate(result.get("data", [])):
    url = item.get("url")
    if not url:
        continue
    ext = ".jpg"
    out_file = out_dir / f"seedream_{datetime.now().strftime('%H%M%S')}_{i}{ext}"
    urllib.request.urlretrieve(url, out_file)
    size_kb = out_file.stat().st_size / 1024
    print(f"已下载: {out_file} ({size_kb:.0f} KB)")
    # 记录 revision id 等元信息
    for k in ("size", "usage"):
        if k in item:
            print(f"  {k}: {item[k]}")
