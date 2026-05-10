#!/usr/bin/env python
"""
normalize_face.py — 把任意尺寸 / 比例的 face PNG 标准化到 1024×1024 中心对齐
方便加新 face 素材到 panda-meme-workshop / pandahead

用法：
    python normalize_face.py --input raw/ --output public/assets/ --start 67

会自动：
  1. 检测 face 实际像素 bounding box（去除四周透明 / 纯白边距）
  2. 等比 resize 到 fits 1024×1024（保留 face 占 80% 中心区）
  3. 居中粘贴到 1024×1024 透明 canvas
  4. 输出 face-ph-{NNN}.png（NNN 从 --start 起递增）
  5. 同时生成 face-pandahead-new.ts 增量条目（手工 merge 进 face-pandahead.ts）

依赖：pip install pillow
"""

import argparse
import json
from pathlib import Path
from PIL import Image


def find_content_bbox(img: Image.Image, alpha_threshold: int = 8, white_threshold: int = 245):
    """找 face 实际内容的 bbox（去除 alpha=0 + 纯白背景）"""
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    min_x, min_y, max_x, max_y = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < alpha_threshold:
                continue
            if r > white_threshold and g > white_threshold and b > white_threshold:
                continue
            if x < min_x: min_x = x
            if y < min_y: min_y = y
            if x > max_x: max_x = x
            if y > max_y: max_y = y
    if max_x <= min_x or max_y <= min_y:
        return (0, 0, w, h)
    return (min_x, min_y, max_x + 1, max_y + 1)


def normalize(input_path: Path, output_path: Path, target_size: int = 1024, fill_ratio: float = 0.85):
    """resize + center 一张 face PNG 到 target_size×target_size"""
    img = Image.open(input_path).convert("RGBA")
    bbox = find_content_bbox(img)
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    # 等比 resize 让 max edge 占 target * fill_ratio
    target_inner = int(target_size * fill_ratio)
    scale = min(target_inner / cw, target_inner / ch)
    new_w, new_h = int(cw * scale), int(ch * scale)
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)
    # paste 居中到 target × target 透明 canvas
    canvas = Image.new("RGBA", (target_size, target_size), (255, 255, 255, 255))
    cx = (target_size - new_w) // 2
    cy = (target_size - new_h) // 2
    canvas.paste(resized, (cx, cy), resized if resized.mode == "RGBA" else None)
    canvas.save(output_path, "PNG", optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="folder of raw face PNG")
    ap.add_argument("--output", required=True, help="folder to write normalized face-ph-NNN.png")
    ap.add_argument("--start", type=int, default=67, help="starting NNN (default 67 to continue from face-ph-066)")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--fill", type=float, default=0.85, help="content fill ratio of canvas (0.0~1.0)")
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted([p for p in in_dir.glob("*.png")] + [p for p in in_dir.glob("*.jpg")])
    if not pngs:
        print(f"no PNG/JPG in {in_dir}")
        return

    new_entries = []
    for i, src in enumerate(pngs):
        n = args.start + i
        name = f"face-ph-{n:03d}.png"
        dst = out_dir / name
        normalize(src, dst, target_size=args.size, fill_ratio=args.fill)
        print(f"  {src.name}  →  {name}")
        new_entries.append({
            "id": f"face-ph-{n:03d}",
            "src": f"/assets/{name}",
            "labelCn": f"熊猫脸 {n}",
            "labelEn": f"Panda Face {n}",
        })

    # 输出 increment TS snippet
    ts_lines = ["// Append these to face-pandahead.ts → PANDAHEAD_FACES array:"]
    for e in new_entries:
        ts_lines.append(
            f"  {{ id: '{e['id']}', src: '{e['src']}', labelCn: '{e['labelCn']}', labelEn: '{e['labelEn']}' }},"
        )
    snippet = "\n".join(ts_lines)
    snippet_path = out_dir.parent / "face-pandahead-new.ts.txt"
    snippet_path.write_text(snippet, encoding="utf-8")
    print(f"\n✓ {len(new_entries)} faces normalized")
    print(f"✓ TS snippet: {snippet_path} (手工 merge 进 src/data/face-pandahead.ts)")


if __name__ == "__main__":
    main()
