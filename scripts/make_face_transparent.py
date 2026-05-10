#!/usr/bin/env python
"""
make_face_transparent.py — 把 face PNG 的白色 padding alpha=0，face 内容保留

为啥需要：
  原 face PNG 是 1024x1024 中心 face + 周围白色 padding（alpha=255 不透明）。
  在 panda-meme-workshop 的 <img> overlay 渲染下，padding 白色 cover panda 黑廓 →
  视觉错位（face 矩形可见、panda 装饰被遮）。
  PandaHead 自家用 canvas 三层 mask 解决，但 panda-meme-workshop 是 <img> 堆叠。

算法（flood fill from boundary）：
  1. mask_white = pixel 是 pure white (R>250 G>250 B>250)
  2. seed = mask_white 在图像 4 边界 (top/bottom/left/right rows)
  3. flooded = binary_propagation(seed, mask=mask_white)
     → 从边界 reachable 的白色 pixel = padding (周围连通的纯白)
     → 不 reachable 的白色 pixel = face 内白色（牙齿/高光，被 face 内容包围孤立）
  4. set alpha[flooded] = 0

输出：覆盖原 PNG，face 内容不变，padding 透明。

依赖：pip install pillow numpy scipy
"""
import argparse
from pathlib import Path
from PIL import Image
import numpy as np
import scipy.ndimage as ndi


WHITE_THRESHOLD = 250  # 严格阈值，避免 face 内浅色被误抠


def make_transparent(img_path: Path, out_path: Path = None):
    out_path = out_path or img_path
    img = Image.open(img_path).convert('RGBA')
    arr = np.array(img)
    H, W = arr.shape[:2]

    # 严格白色 mask
    mask_white = (
        (arr[:, :, 0] >= WHITE_THRESHOLD) &
        (arr[:, :, 1] >= WHITE_THRESHOLD) &
        (arr[:, :, 2] >= WHITE_THRESHOLD)
    )
    if not mask_white.any():
        print(f'  [skip] {img_path.name}: no pure white pixel')
        return False, 0

    # 4 边界种子
    seed = np.zeros_like(mask_white)
    seed[0, :] = mask_white[0, :]
    seed[-1, :] = mask_white[-1, :]
    seed[:, 0] = mask_white[:, 0]
    seed[:, -1] = mask_white[:, -1]

    # flood fill — 从边界 propagate within mask_white
    flooded = ndi.binary_propagation(seed, mask=mask_white)

    if not flooded.any():
        print(f'  [skip] {img_path.name}: no boundary white connected')
        return False, 0

    # set padding alpha = 0
    arr[flooded, 3] = 0

    transparent_count = int(flooded.sum())
    Image.fromarray(arr, 'RGBA').save(out_path, 'PNG', optimize=True)
    return True, transparent_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='单 PNG 或目录（自动扫 face*.png 或 *.png）')
    ap.add_argument('--output', help='默认覆盖 input PNG。指定时 mirror 文件结构')
    ap.add_argument('--pattern', default='face-ph-*.png', help='文件名 glob (default face-ph-*.png)')
    args = ap.parse_args()

    in_path = Path(args.input)
    if in_path.is_file():
        files = [in_path]
    else:
        files = sorted(in_path.glob(args.pattern))

    if not files:
        print(f'[err] no {args.pattern} matched in {in_path}')
        return

    ok, total_transp = 0, 0
    for f in files:
        out = Path(args.output) / f.name if args.output else f
        out.parent.mkdir(parents=True, exist_ok=True)
        success, n = make_transparent(f, out)
        if success:
            print(f'  [ok] {f.name}: {n} padding pixel -> alpha 0')
            ok += 1
            total_transp += n

    print(f'\n[done] {ok}/{len(files)} transparentified, total {total_transp} pixels removed')


if __name__ == '__main__':
    main()
