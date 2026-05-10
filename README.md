# panda-faces — PandaHead 素材库 + 工具集

> 来自 [PandaHead](https://pandahead.fun) ([github.com/jokkibtc/panda](https://github.com/jokkibtc/panda)) 的人脸 + 熊猫头廓素材库 + Python 工具，
> 贡献给中文熊猫头表情包社区使用（[xiongmaotou.work](https://xiongmaotou.work) etc.）。

## 快速集成（panda-meme-workshop / 类似框架）

```bash
git clone https://github.com/jokkibtc/panda-faces.git temp-faces
cp temp-faces/public/assets/*.png <your-repo>/public/assets/
cp temp-faces/src/data/*.ts <your-repo>/src/data/
```

然后在你 `materials.ts` 末尾追加：

```typescript
import { PANDAHEAD_FACES } from './face-pandahead';
import { PANDAHEAD_PANDAS } from './panda-pandahead';
import { PANDA_ALIGN_OVERRIDES } from './panda-align-overrides';

// 合并完整池
export const ALL_FACES = [...FACES, ...PANDAHEAD_FACES];        // 67 + 65 = 132
export const ALL_PANDAS = [...PANDA_HEADS, ...PANDAHEAD_PANDAS]; // 24 + 46 = 70

// 应用 align_panda.py v3 自动算的 faceOffset overrides — fix 24 panda 部分姿势对齐不准
PANDA_HEADS.forEach(p => {
  if (PANDA_ALIGN_OVERRIDES[p.id]) p.faceOffset = PANDA_ALIGN_OVERRIDES[p.id];
});
```

下游 LeftSidebar / 编辑器引用 `ALL_PANDAS` / `ALL_FACES` 即可。

## 完整内容清单

### 素材 PNG（111 张总）

- **65 张真人脸**（`public/assets/face-ph-001.png` ~ `face-ph-066.png`，缺 002）
  - 1024×1024，已对齐头部中心（normalize_face.py 处理）
  - 含金馆长 / 姚明 / 王尼玛系列等中文互联网经典脸 + 用户截图补充
  - 命名 `face-ph-NNN`（`ph` = pandahead 来源），跟现有 `face-NN` 不冲突

- **46 个熊猫头廓 panda body**（`public/assets/panda-ph-001.png` ~ `panda-ph-046.png`）
  - 各种 pose：经典款 / 弯腰款 / 倒立款 / 撑伞款 / 打拳 / 拿刀 / 颠勺 / 墨镜 / OK 手势 ...
  - 完整清单 + label 见 `src/data/panda-pandahead.ts`
  - 每张自带 `faceOffset { x, y, w, h }`，自动从 PandaHead 原 bbox 转到 350×350 panda body 坐标系

### TypeScript data file（即插即用）

- `src/data/face-pandahead.ts` — 65 张 face 数据，`Material[]` 类型，含 zh/en label + tags + faceOffset
- `src/data/panda-pandahead.ts` — 46 张 shell 数据，同上 + 精准 faceOffset
- `src/data/panda-align-overrides.ts` — **47 个**已存在 panda 的 faceOffset 修正建议（auto-gen by align_panda.py v3）

### Python 工具 ×2（`scripts/`）

#### 1. `normalize_face.py` — 标准化 face PNG

把任意尺寸 / 比例的原 face PNG 处理成跟现有 65 张一致的 1024×1024 中心对齐格式。

```bash
pip install pillow
python scripts/normalize_face.py --input raw-faces/ --output public/assets/ --start 67
# raw-faces/ 里扔几张新截的脸 → 输出 face-ph-067.png 起递增 + face-pandahead-new.ts.txt
```

**Logic**：
1. 读 PNG 转 RGBA
2. 检测内容 bbox（去掉四周透明 / 纯白边距）
3. 等比 resize 让 max edge 占 canvas 85%
4. 居中粘贴到 1024×1024 透明 canvas
5. 输出 + 同时生成 TS 增量条目 snippet

**注意**：是 panda-meme-workshop 框架简化版（不需要 alpha mask 直接 `<img>` overlay）。
PandaHead 主仓库用更复杂的 `build_assets.py` 同时生成 face mask + pmask 给 canvas 三层合成。
本 `normalize_face.py` logic 提炼自 build_assets.py，已在 sample face 上 verify 输出 1024×1024 中心对齐 PNG。

#### 2. `align_panda.py` v3 — 自动检测 panda 准确 faceOffset

**解决问题**：panda-meme-workshop 现有 24 panda 用 5-6 个 preset offset 复用，部分姿势（panda-08 疑问 / panda-12 站立2 / panda-stand 等）face 落点偏离 panda 头脸 → 视觉错位。

```bash
pip install pillow numpy scipy
python scripts/align_panda.py --input <your-repo>/public/assets/ --output align-suggestions.json
# 跑完看 align-suggestions.json，review 后决定是否 apply
```

**v3 算法**（vs v1/v2）：
- v1：取所有"白色 + 不透明"像素 bbox → panda 没空白时 width 经常满宽（不准）
- v2：scipy.ndimage.label 找最大白色联通区 → panda 头内白脸被眼睛/嘴巴 split 时 bbox 只是某小块（panda-01/02/stand 给 w=1 的 bug）
- **v3：v2 + binary_dilation 5px 合并被 split 的小白块** → bbox 才能囊括整片 panda 头脸

**慎用 caveats**：
- 本 repo 已附 `panda-align-overrides.ts`，含 47 个 panda 的 v3 跑出的建议。**直接 import 用即可，不需要自己跑算法**
- 算出的 bbox 是"建议值"，少数姿势可能仍需 visual review 微调（如颠勺款 face 区在锅里就一小块、敬礼款 face 偏下方）
- panda-04 / panda-06 / panda-10 / panda-salute 等 panda 头里完全没"白色像素"的，算法返回 None → 保留原 manual offset
- **不要无脑覆盖现有 faceOffset 对所有 panda**，建议 import `PANDA_ALIGN_OVERRIDES` 选择性应用

## 配套 PR

Quick Mode（简易生图）+ Collection（草图管理批量打包）板块的代码贡献：

→ **[panda-meme-workshop fork PR #1](https://github.com/jokkibtc/panda-meme-workshop/pull/1)**

含 5 个 commit：
1. `feat: QuickMode (简易生图模式)` — 独立 page，trait selector 流程
2. `feat: 集成 PandaHead 46 shell + 65 face + align_panda.py 工具`
3. `feat: 加 Collection (草图管理) 板块 - 按 LittleRed 提的需求`
4. `feat: 完整移植 PandaHead 三大功能 — align fix + QuickMode v2 + Collection v2`

QuickMode v2 含 face rotation（拖 + 滚轮）+ flip + reset + 文字语言切换 + 收藏改名。
Collection v2 含批量选 + ZIP 打包 + filter (全部/最近)。

## 命名约定

- `face-ph-NNN` / `panda-ph-NNN` — 三位 zero-pad，`ph` = pandahead 来源标记
- 跟现有 `face-NN` / `panda-NN` 完全不冲突，未来其他来源可用 `face-XX-NNN` / `panda-XX-NNN`（XX = 来源缩写）

## 标签 / faceOffset 状态

| 资源 | 真标签数 | 说明 |
|---|---|---|
| face | 4 / 65 | 4 张有真情绪标签（愤怒/微笑/哭脸/严肃），61 张暂用 generic（"熊猫脸 N"），社区可补充 |
| panda body | 46 / 46 | 全有名（弯腰款 / 颠勺款 / 墨镜款 等），category 含 head/bust/action/cooking/sport/misc |
| faceOffset (PandaHead) | 46 / 46 | 自动从 PandaHead 原 `bbox` 转到 350×350 panda body 坐标系 |
| faceOffset overrides (panda-meme-workshop) | 47 / 47 | align_panda.py v3 算出的 fix 数据 |

## 升级指南

每次 panda-faces 更新（加 face / 算 align），下游：

```bash
cd <your-repo>
rm public/assets/face-ph-*.png public/assets/panda-ph-*.png
rm src/data/face-pandahead.ts src/data/panda-pandahead.ts src/data/panda-align-overrides.ts
git clone https://github.com/jokkibtc/panda-faces.git /tmp/panda-faces
cp /tmp/panda-faces/public/assets/*.png public/assets/
cp /tmp/panda-faces/src/data/*.ts src/data/
```

或者把本 repo 加成 git submodule：

```bash
git submodule add https://github.com/jokkibtc/panda-faces.git vendor/panda-faces
# 然后在 build 时 sync 资源
```

## License

MIT — 详见 [LICENSE](./LICENSE)。
素材属公开熊猫头梗图衍生，按 fair-use 用于研究 / 教育 / 个人非商业用途。
