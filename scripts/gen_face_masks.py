#!/usr/bin/env python
"""
gen_face_masks.py — 给每个 panda body PNG 生成对应的 face area alpha mask

为啥需要：
  panda-meme-workshop 用 `<img>` overlay 堆 face 到 panda 上，face PNG 自带的
  白色背景会 cover panda 头黑廓 / 超出 panda 白脸区。
  PandaHead 自家用 canvas 三层 mask 合成（face mask + panda white mask）解决。
  本脚本生成 face area mask，让 panda-meme-workshop 用 CSS mask-image 复刻效果。

输出：
  对每个 panda-NN.png 输出 panda-NN-facemask.png (alpha mask, size = face area bbox)
  face area = panda 内白色联通区域 bbox（dilated 5px 合并被眼睛/嘴巴 split 的小白）
  alpha = 255 在 face area 实际白色区，alpha = 0 其他

CSS 用法：
  <img src="face.png" style={{
    width: panda.faceOffset.w + 'px',
    height: panda.faceOffset.h + 'px',
    maskImage: `url(${panda.id}-facemask.png)`,
    maskSize: '100% 100%',
    WebkitMaskImage: `url(${panda.id}-facemask.png)`,
    WebkitMaskSize: '100% 100%',
  }} />

依赖：pip install pillow numpy scipy
"""
import argparse
from pathlib import Path
from PIL import Image
import numpy as np
import scipy.ndimage as ndi


HEAD_TOP_RATIO = 0.7
WHITE_THRESHOLD = 200
ALPHA_THRESHOLD = 200
MIN_AREA_PIXELS = 500
DILATE_ITER = 5


def detect_face_region_mask(img_path: Path):
    """返回 (face_area_mask_bool_array, bbox)。bbox 是 face area 的 [x1,y1,x2,y2]"""
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
        return None, None

    dilated = ndi.binary_dilation(is_white, iterations=DILATE_ITER)
    labels, num = ndi.label(dilated)
    if num == 0:
        return None, None

    sizes = ndi.sum(dilated, labels, range(1, num + 1))
    biggest_label = int(np.argmax(sizes)) + 1
    if int(sizes[biggest_label - 1]) < MIN_AREA_PIXELS:
        return None, None

    region_dilated = labels == biggest_label
    region_white = region_dilated & is_white  # 真正白色像素 (face 实际填充)
    if not region_white.any():
        return None, None

    ys, xs = np.where(region_white)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]

    # face area mask = dilated 联通区（含 panda 头内被分割的小白块的"包含"区域）
    # 这样 mask 是 panda 头内 face 整体形状（含眼睛/嘴/耳朵所在 black pixel 的位置都算 mask 内）
    return region_dilated, bbox


def make_facemask_png(img_path: Path, out_path: Path):
    """生成 face area alpha mask PNG，crop 到 face area bbox"""
    region, bbox = detect_face_region_mask(img_path)
    if region is None:
        return False, 'no face area detected'

    x1, y1, x2, y2 = bbox
    face_region = region[y1:y2, x1:x2]  # crop 到 bbox

    # 生成 alpha mask: 255 在 region True, 0 其他
    H, W = face_region.shape
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0] = 255   # white
    rgba[..., 1] = 255
    rgba[..., 2] = 255
    rgba[..., 3] = np.where(face_region, 255, 0).astype(np.uint8)

    # 软化边缘 (Gaussian blur on alpha) — 让 face 边缘平滑融入
    alpha_smooth = ndi.gaussian_filter(rgba[..., 3].astype(np.float32), sigma=1.5)
    rgba[..., 3] = np.clip(alpha_smooth, 0, 255).astype(np.uint8)

    Image.fromarray(rgba, 'RGBA').save(out_path, 'PNG', optimize=True)
    return True, f'{W}x{H}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='dir of panda*.png')
    ap.add_argument('--output', help='output dir (default same as input)')
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.output) if args.output else in_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob('panda*.png'))
    files = [f for f in files if 'facemask' not in f.name]

    if not files:
        print(f'[err] no panda*.png in {in_dir}')
        return

    ok, fail = 0, []
    for f in files:
        out = out_dir / f.name.replace('.png', '-facemask.png')
        success, info = make_facemask_png(f, out)
        if success:
            print(f'  [ok] {f.name} -> {out.name} ({info})')
            ok += 1
        else:
            print(f'  [skip] {f.name}: {info}')
            fail.append(f.stem)

    print(f'\n[done] {ok} masks generated, {len(fail)} skipped')
    if fail:
        print(f'[skipped] {fail}')


if __name__ == '__main__':
    main()
