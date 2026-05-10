#!/usr/bin/env python
"""
align_panda.py v3 — 自动检测 panda body PNG 内白色 face 区，输出对齐准确的 faceOffset

v3 改进 vs v2：
  v2 取"白色像素"最大联通区 bbox，但 panda 头脸内黑眼睛 / 嘴巴会把白脸 split
       成多个小块，导致最大联通区只是某一小块（panda-01/02/stand 给 w=1 等 bug）
  v3 加 binary_dilation 5 px 让 panda 头内部窄间隙白色合并成一片，再找最大联通区
       → bbox 才能囊括整片 panda 头脸（含被眼睛嘴巴 split 的白色像素）

算法：
  1. 读 panda PNG → RGBA
  2. mask = "白色 + 不透明" pixel (R>200 G>200 B>200 alpha>200)
  3. 限制 y < height * 0.7 (panda 头脸都在上半)
  4. binary_dilation(5 iter) 合并被黑色 split 的小白块
  5. scipy.ndimage.label 找联通组件
  6. 取最大组件 → 在原 mask 上找该组件内所有白 pixel 的 bbox
  7. 转换到 350×350 panda body 坐标系（contain scaling + letterbox padding）
  8. 输出 faceOffset

依赖：pip install pillow numpy scipy

慎用：
  - 部分 panda 头里完全没白色 (panda-04/06/10/salute) 算法返回 None，需手算 offset
  - 部分 panda 头廓本身就是白色占满 → bbox = 头整体（width 接近 350）也合理
  - 算出的 bbox 是 face 落点的"建议值"，少数姿势仍需 visual review 微调
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
MIN_AREA_PIXELS = 500   # 联通区低于此忽略（噪点）
DILATE_ITER = 5         # 合并 panda 头内被眼睛嘴巴 split 的小白块


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
        return None, (W, H), 'no white pixels in head region'

    # v3: dilate 让 panda 头内被黑色 split 的白色合并
    dilated = ndi.binary_dilation(is_white, iterations=DILATE_ITER)
    labels, num = ndi.label(dilated)
    if num == 0:
        return None, (W, H), 'no connected components'

    # 取最大 dilated 联通区
    sizes = ndi.sum(dilated, labels, range(1, num + 1))
    biggest_label = int(np.argmax(sizes)) + 1
    if int(sizes[biggest_label - 1]) < MIN_AREA_PIXELS:
        return None, (W, H), f'biggest region too small ({int(sizes[biggest_label-1])} px)'

    # 在该 dilated 区里找 **原 mask 的** white pixel bbox
    region_mask = (labels == biggest_label) & is_white
    if not region_mask.any():
        return None, (W, H), 'region has no original white pixels'

    ys, xs = np.where(region_mask)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    return bbox, (W, H), 'ok'


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
    ap.add_argument('--dilate', type=int, default=DILATE_ITER)
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
    skipped = []
    for f in files:
        bbox, size, reason = detect_face_bbox(f)
        if bbox is None:
            skipped.append((f.stem, reason))
            print(f'  [skip] {f.name}: {reason}')
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
    print(f'\n[done] {len(results)} panda processed, {len(skipped)} skipped -> {out}')
    if skipped:
        print(f'[skipped] {[s[0] for s in skipped]} (need manual offset)')


if __name__ == '__main__':
    main()
