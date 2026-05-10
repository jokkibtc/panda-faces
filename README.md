# PandaHead → MemeForge：65 张真人脸素材贡献

来自 [PandaHead](https://pandahead.fun)（[github.com/jokkibtc/panda](https://github.com/jokkibtc/panda)）的人脸素材库 + 简易构建工具贡献给 [panda-meme-workshop](https://github.com/nixijue-arch/panda-meme-workshop)。

## 含什么

- **65 张 1024×1024 真人脸 PNG**：手截的中文互联网熊猫头经典脸（金馆长 / 姚明 / 王尼玛系列）+ 自己截的几十张表情各异的脸，全部已对齐头部中心
- **TS data 文件**：可直接 import 到现有 `materials.ts`
- **可选 Python 构建工具**：自动 resize + center alignment（加新脸时自动处理，不用手抠）

## 文件清单

```
public/assets/face-ph-001.png  ~ face-ph-066.png   # 65 张（缺 002，原项目 face-2 漏号，保持一致）
src/data/face-pandahead.ts                          # TS 数据
scripts/normalize_face.py                           # 自动处理新 face 的 Python 工具
README.md                                           # 本文件
```

## 集成方式（≤ 3 步）

### 1. 复制 PNG

```
cp public/assets/face-ph-*.png <your-repo>/public/assets/
```

### 2. 加 import 到 materials.ts

```diff
  // src/data/materials.ts
  export const FACES: FaceItem[] = [
    // ... 你们现有 15 张 face-01 ~ face-15 ...
  ];
+
+ // 追加 PandaHead 贡献的 65 张
+ import { PANDAHEAD_FACES } from './face-pandahead';
+ export const ALL_FACES = [...FACES, ...PANDAHEAD_FACES];
```

或更简（如果允许直接覆盖 FACES）：

```typescript
import { PANDAHEAD_FACES } from './face-pandahead';
export const FACES: FaceItem[] = [...EXISTING_FACES, ...PANDAHEAD_FACES];
```

### 3. （可选）用 Python 工具加新脸

```bash
# 把任意尺寸 face PNG 扔到 raw/，跑这个，输出标准化的 face-ph-XXX.png
pip install pillow
python scripts/normalize_face.py --input raw/ --output public/assets/ --start 67
```

## 命名约定

`face-ph-NNN.png`（pandahead 来源 + 3 位 zero-pad）— 避免跟现有 `face-NN` 冲突，未来其他 contributor 加新源也可用 `face-XX-NNN` 模式（XX = 来源缩写）。

## 标签状态

| 数量 | 标签 |
|---|---|
| 4 张 | 真标签（愤怒 / 微笑 / 哭脸 / 严肃） |
| 61 张 | Generic（"熊猫脸 N" / "Panda Face N"）— 谁有空可以重命名做更细的情绪分类 |

## License

素材属公开熊猫头梗图衍生，按 fair-use 用于研究 / 教育 / 个人非商业用途（详见 PandaHead repo `LICENSE`）。

PR 代码部分 MIT。
