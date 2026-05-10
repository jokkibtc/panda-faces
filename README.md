# panda-faces — PandaHead 素材库

> 来自 [PandaHead](https://pandahead.fun) ([github.com/jokkibtc/panda](https://github.com/jokkibtc/panda)) 的人脸 + 熊猫头廓素材库，
> 贡献给中文熊猫头表情包社区使用（[xiongmaotou.work](https://xiongmaotou.work) etc.）。

## 含什么

- **65 张真人脸 PNG**（`public/assets/face-ph-001.png` ~ `face-ph-066.png`，缺 002）
  - 1024×1024，已对齐头部中心
  - 含金馆长 / 姚明 / 王尼玛系列等中文互联网经典脸 + 用户截图补充
- **46 个熊猫头廓 PNG**（`public/assets/panda-ph-001.png` ~ `panda-ph-046.png`）
  - 各种 pose：经典款 / 弯腰款 / 倒立款 / 撑伞款 / 打拳 / 拿刀 ... 完整清单见 `src/data/panda-pandahead.ts`
- **TypeScript data file**（即插即用，跟现有 panda-meme-workshop 框架兼容）
  - `src/data/face-pandahead.ts` — 65 张 face 数据，含 zh/en 标签
  - `src/data/panda-pandahead.ts` — 46 张 shell 数据，含 zh/en 标签 + `faceOffset` 已自动转到 350×350 panda body 坐标系
- **Python 自动构建工具**（`scripts/normalize_face.py`）
  - 加新 face：扔 raw PNG 到一个文件夹 → 一键 resize + center alignment + 输出 face-ph-NNN.png + TS 增量条目
  - 注：本工具是为 panda-meme-workshop 框架简化版（不需要 alpha mask 直接 `<img>` overlay）；
    PandaHead 主仓库用更复杂的 `build_assets.py` 同时生成 face/panda mask 给 canvas 三层合成。
    本 `normalize_face.py` logic 提炼自 build_assets.py，已在 3 张 sample face 上 verify
    输出 1024×1024 中心对齐 PNG。如有问题欢迎 issue。

## 集成方式（panda-meme-workshop 框架）

### 1. 复制 PNG

```bash
cp public/assets/*.png <your-repo>/public/assets/
```

### 2. 把 TS data file 拼到 materials.ts

```typescript
// src/data/materials.ts
import { PANDAHEAD_FACES } from './face-pandahead';
import { PANDAHEAD_PANDAS } from './panda-pandahead';

// 你们现有数据
export const FACES: Material[] = [ /* face-01 ~ face-15 等 */ ];
export const PANDA_HEADS: Material[] = [ /* panda-01 ~ panda-24 等 */ ];

// 合并后的完整池
export const ALL_FACES = [...FACES, ...PANDAHEAD_FACES];      // 15 + 65 = 80
export const ALL_PANDAS = [...PANDA_HEADS, ...PANDAHEAD_PANDAS]; // 24 + 46 = 70
```

### 3. LeftSidebar / 编辑器引用 ALL_*

```typescript
import { ALL_FACES, ALL_PANDAS } from '@/data/materials';
// ... 用 ALL_FACES / ALL_PANDAS 替换原来的 FACES / PANDA_HEADS
```

## 命名约定

- `face-ph-NNN` / `panda-ph-NNN` — 三位 zero-pad，`ph` = pandahead 来源标记
- 跟现有 `face-NN` / `panda-NN` 完全不冲突，未来其他来源可用 `face-XX-NNN` / `panda-XX-NNN`（XX = 来源缩写）

## 标签 / faceOffset 状态

| 资源 | 真标签数 | 备注 |
|---|---|---|
| face | 4 / 65 | 4 张有真情绪标签，61 张暂用 generic（"熊猫脸 N"），社区可补充 |
| panda body | 46 / 46 | 全有名（弯腰款 / 颠勺款 / 墨镜款 等），category 含 head/bust/action/cooking/sport/misc |
| faceOffset | 46 / 46 | 自动从 PandaHead 原 `bbox` 转到 350×350 panda body 坐标系 |

注：少数 shell（如颠勺款，face 在锅里小区域）`faceOffset` 偏小是数学正确转换。视觉效果不理想可手动微调。

## License

MIT — 详见 [LICENSE](./LICENSE)。
素材属公开熊猫头梗图衍生，按 fair-use 用于研究 / 教育 / 个人非商业用途。
