# panda-faces

熊猫头表情包素材库 + canvas 渲染引擎 + Python 工具，给社区项目（[xiongmaotou.work](https://xiongmaotou.work) ）开箱即用。

## 包含什么

- **素材**：46 个 panda 黑白线稿（多种姿势）+ 65 个 face（金馆长 / 姚明 / 王尼玛 / 名场面）
- **70 个 panda 的手动校准 anchor**：每个 shell 的 face 落点位置 + 大小（肉眼校准 + 工具拖拽生成）
- **canvas 渲染引擎** `composeMeme.ts`：face + panda 双 mask 合成，自动处理 face 错位 / 比例 / 椭圆裁切 / 暗物体覆盖
- **Python 工具**：自动检测 face anchor、批量生成透明 face PNG、生成 face area mask

## 快速集成（React + TypeScript 项目）

```bash
git clone https://github.com/jokkibtc/panda-faces.git temp-faces
cp temp-faces/public/assets/*.png <your-repo>/public/assets/
cp -r temp-faces/src/data <your-repo>/src/
cp -r temp-faces/src/lib <your-repo>/src/
```

`materials.ts` 末尾合并：

```typescript
import { PANDAHEAD_FACES } from './data/face-pandahead';
import { PANDAHEAD_PANDAS } from './data/panda-pandahead';
import { PANDA_MANUAL_OVERRIDES } from './data/panda-manual-overrides';

export const ALL_FACES = [...YOUR_FACES, ...PANDAHEAD_FACES];
export const ALL_PANDAS = [...YOUR_PANDAS, ...PANDAHEAD_PANDAS];

[...YOUR_PANDAS, ...PANDAHEAD_PANDAS].forEach(p => {
  if (PANDA_MANUAL_OVERRIDES[p.id]) p.faceOffset = PANDA_MANUAL_OVERRIDES[p.id];
});
```

合成 face + panda 用 `composeMeme()`：

```typescript
import { composeMeme } from './lib/composeMeme';

const dataUrl = await composeMeme({
  pandaSrc: panda.src,
  faceSrc: face.src,
  faceOffset: panda.faceOffset,
  size: 1024,
});
// 设给 <img src={dataUrl}>
```

## 文件结构

```
public/assets/         46 panda + 65 face PNG
src/data/              panda/face metadata + 70 个手动校准 anchor
src/lib/composeMeme.ts canvas 合成引擎（纯 TypeScript，无外部依赖）
scripts/               Python 工具（重新校准 / 加新素材时用）
```

## Python 工具

只在加新素材 / 重做校准时需要，集成现成项目不用。

```bash
pip install pillow numpy scipy

# 给 panda PNG 自动检测 face anchor，输出 350-coord faceOffset
python scripts/align_panda.py --input ./public/assets

# 把 face PNG 周围白色 padding 改透明
python scripts/make_face_transparent.py --input ./public/assets

# 生成 face area mask（带 mask 合成方案用）
python scripts/gen_face_masks.py --input ./public/assets
```

欢迎 fork / PR。

## License

MIT — 素材 + 代码 + 工具均可商用 / 改 / 再分发。
