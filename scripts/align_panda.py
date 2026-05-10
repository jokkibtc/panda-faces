#!/usr/bin/env python
"""
align_panda.py v2 — 自动检测 panda body PNG 内白色 face 区，输出对齐准确的 faceOffset

v2 改进 (vs v1)：
  v1 取所有白色像素 bbox → 对已 cropped 的 panda PNG 经常 width 满宽（把 panda
       廓内整片白都算了，包括身体白色和头脸白色一起）。
  v2 用 scipy.ndimage.label 找连通组件 → 取**最大白色联通区**（panda 头脸主体）
       的 bbox。能 isolate panda 头部白脸而不被身体/手白色干扰。

算法：
  1. 读 panda PNG，转 RGBA
  2. mask = "白色 + 不透明" pixel (R>200 G>200 B>200 alpha>200)
  3. 限制 y < height * 0.7 (panda 头脸都在上半，过滤腿/手)
  4. scipy.ndimage.label 找联通组件
  5. 取最大组件 → 该 mask 的 bbox
  6. 转换到 350x350 panda body 坐标系（contain scaling + letterbox padding）
  7. 输出 faceOffset

依赖：pip install pillow numpy scipy
"""
import argparse, json
from pathlib import Path
from PIL import Image
import numpy as np
import scipy.ndimage as ndi


TARGET = 350
HEAD_TOP_RATIO = 0.7
WHITE_THRESHOLD = 200
ALPHA_THRESHOLD = 200
MIN_AREA_PIXELS = 100  # 太小的联通块过滤掉（噪点）


def detect_face_bbox(img_path: Path):
    img = Image.open(img_path).convert('RGBA')
    W, H = img.size
    arr = np.array(img)

    is_white = (
        (arr[:, :, 0] > WHITE_THRESHOLD) &
        (arr[:, :, 1] > WHITE_THRESHOLD) &
        (arr[:, :, 2] > WHITE_THRESHOLD) &
        (arr[:, :, 3] > ALPHA_THRESHOLD)
    )

    head_cutoff = int(H * HEAD_TOP_RATIO)
    is_white[head_cutoff:, :] = False

    if not is_white.any():
        return None, (W, H)

    # scipy 找联通组件
    labels, num = ndi.label(is_white)
    if num == 0:
        return None, (W, H)

    # 取最大联通组件
    sizes = ndi.sum(is_white, labels, range(1, num + 1))
    biggest_label = int(np.argmax(sizes)) + 1
    biggest_size = int(sizes[biggest_label - 1])
    if biggest_size < MIN_AREA_PIXELS:
        return None, (W, H)

    mask = labels == biggest_label
    ys, xs = np.where(mask)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    return bbox, (W, H)


def to_face_offset(bbox, img_size):
    W, H = img_size
    scale = min(TARGET / W, TARGET / H)
    pad_x = (TARGET - W * scale) / 2
    pad_y = (TARGET - H * scale) / 2
    return {
        'x': round(bbox[0] * scale + pad_x),
        'y': round(bbox[1] * scale + pad_y),
        'w': round((bbox[2] - bbox[0]) * scale),
        'h': round((bbox[3] - bbox[1]) * scale),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', default='align-suggestions.json')
    ap.add_argument('--head-cutoff', type=float, default=HEAD_TOP_RATIO)
    args = ap.parse_args()

    in_path = Path(args.input)
    if in_path.is_file():
        files = [in_path]
    else:
        files = sorted(in_path.glob('panda*.png'))

    if not files:
        print(f'[err] no panda*.png in {in_path}')
        return

    results = {}
    for f in files:
        bbox, size = detect_face_bbox(f)
        if bbox is None:
            print(f'  [skip] {f.name}: no white head region')
            continue
        offset = to_face_offset(bbox, size)
        pid = f.stem
        results[pid] = {
            'src': f'/assets/{f.name}',
            'origBbox': bbox,
            'origSize': list(size),
            'faceOffset': offset,
        }
        print(f'  [ok] {pid}: faceOffset = x={offset["x"]:3} y={offset["y"]:3} w={offset["w"]:3} h={offset["h"]:3}')

    out = Path(args.output)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\n[done] {len(results)} panda processed -> {out}')


if __name__ == '__main__':
    main()
