# PaperTranslate Skill 设计文档

- 日期：2026-08-14
- 状态：待用户审阅
- 仓库：`E:\LLMproject\Cordis\PaperTranslate`

## 1. 背景与目标

用户有一篇英文 CS 论文《A Programming Paradigm for Spatiotemporal Composability》，已由 MinerU 解析为 `full.md`（2242 行、84 个 LaTeX 公式、5 图、2 HTML 表、11 代码块、124 参考文献）+ `images/` + JSON。目标是把"英文论文 → 中文翻译 → 多形态 PDF 输出"沉淀为一个**可复用、可开源的通用 skill**（PaperTranslate）。

### 已确认的核心需求

| 维度 | 决策 |
|------|------|
| 翻译引擎 | **agent 自己翻译**（无第三方 LLM API 依赖，质量最高） |
| 输入边界 | 默认 **MinerU API 解析**（key 存 skill 目录 `.env`，参考 `extract-report` 模式）+ **支持本地 MinerU 已解析产物** |
| 输出集 | 四态可选参数，任意组合（见 §6） |
| 双栏对照形态 | **对开双语对照**：两个 A4 竖版横向拼接，左英文、右中文，段落对齐，图表各归各语言 |
| 并发策略 | v2：多 agent 并行翻译 + **隔离上下文的 review agent** 全篇对齐审查 |
| skill 形态 | 通用 skill（SKILL.md + scripts + templates + 安装说明，兼容多 agent） |
| 技术底座 | Pandoc + xelatex + ctex + paracol（本机 TeX Live 2025 已装） |

## 2. 调研与建库决策（第三方方案评估结论）

逐文件通读三个候选仓库的全部 SKILL.md 与 scripts 源码后：

| 维度 | APLaS/paper-translation | LiuMengxuan04/translate-… | xinghuo7953/pdf-md-pdf-translate |
|------|------|------|------|
| 定位 | PDF→中文MD 方法论 skill | PDF→目标语言MD 编辑型 skill | PDF→MD→中文→PDF 全链路 skill |
| xelatex | ❌ | ❌ | ❌ 用 `msedge --headless=new --print-to-pdf` 浏览器打印 |
| 双栏对照 | ❌ | ❌ | ❌（单栏流式） |
| 并发 | ⚠️ 仅批量（非并发） | ❌ | ✅ `asyncio`+`Semaphore`+`to_thread` 并发翻译 |
| 公式处理 | 清洗规则（方法论层） | 重建 LaTeX + `\tag` | 最强：LaTeX 规范化 + 占位符保护 |
| LICENSE | **无** | **无** | **无** |

**决策：新建库（不 fork 提 PR）**，理由：
1. 核心差异化能力 = **xelatex 原生渲染 + 对开双栏对照**，三方零重合（100% 原创）
2. 需求横跨三库（方法论↔APLaS、编辑规范↔translate-…、全链路+并发↔pdf-md-…），无单一库覆盖过半
3. 三方均无 LICENSE，fork/再分发法律受限；新增能力是本质扩展，PR 难被接受
4. **不重复造轮子**：方法论内化三方经验、并发借鉴 asyncio 设计自行实现；真正新写仅 3 块（paracol 对开组装脚本、xelatex 模板、渲染管线）。无 LICENSE → 不拷贝代码，重写实现

## 3. 仓库结构与组件

```
PaperTranslate/
├── SKILL.md                           # skill 定义(frontmatter) + 5 阶段工作流方法论
├── README.md                          # 安装/使用/依赖说明（pandoc、xelatex、Python）
├── LICENSE                            # MIT（宽松协议，允许自由使用/修改/再分发）
├── .gitignore                         # 忽略 config/.env、输出产物、__pycache__ 等
├── config/
│   ├── .env.example                   # MINERU_API_TOKEN= 模板（真实 token 不提交）
│   └── .env                           # 真实 token（gitignore）
├── scripts/
│   ├── run.py                         # 统一入口：接收 --outputs 参数，按需编排各生成脚本
│   ├── mineru_convert.py              # MinerU API: PDF→full.md（复用 extract-report 模式）
│   ├── make_bilingual.py              # 对开双栏对照 PDF: 英/中 md 切块→配对→paracol→xelatex
│   ├── make_single.py                 # 中文单栏还原 PDF: full_zh.md→pandoc→ctexart→xelatex
│   ├── make_bilingual_md.py           # 对照版 md（左英右中，可选输出）
│   ├── validate.py                    # 三态校验（FAIL/WARN/SKIP 分层，见 §7）
│   └── copy_images.py                 # images/ 引用图片复制到输出目录
├── templates/
│   ├── bilingual.tex                  # paracol 对开双栏模板（A4 拼接、SimSun/SimHei）
│   └── single.tex                     # ctexart 单栏模板（还原 arXiv 单栏风格）
└── tests/
    └── sample/                        # 小样例 md 用于脚本冒烟测试
```

**组件职责分离原则**：agent 承担智能工作（翻译、乱码语义推断修复、术语决策、审查），脚本承担机械化工作（API 转换、块切分配对、LaTeX 组装、编译、验证）。任何一步可被 agent 手动调用/复核。

## 4. 工作流（数据流）

```
[PDF 或已有 full.md]
   ↓ ① 输入：mineru_convert.py（MinerU API，.env 读 token）或直接采用本地 MinerU 产物
[full.md + images/]
   ↓ ② 准备：公式清洗、乱码推断修复、术语表建立、块切分（agent 完成）
[full_zh.md]（翻译，v1 顺序 / v2 多 agent 并行）
   ↓ ③ review agent 全篇对齐审查（v2；v1 由主 agent 自审）
   ↓ ④ 按 --outputs 参数并行生成选定的输出物：
[对开双栏对照 PDF]  ← make_bilingual.py → bilingual.tex → xelatex
[中文单栏还原 PDF]  ← make_single.py → single.tex → xelatex
[对照版 md（可选）] ← make_bilingual_md.py
   ↓ ⑤ validate.py 三态校验（FAIL 阻断 / WARN 交 agent）
```

## 5. 输出物生成细节

### 5.1 对开双栏对照 PDF（技术核心，make_bilingual.py）

形态：**两个独立 A4 竖版横向拼接**——左半张英文完整论文、右半张中文完整论文，并排如"同时打开两个 PDF 对比"。图表**不混用**：英文图注/表格留在左栏，中文图注/表格在右栏，各自翻译。

1. **块切分**：英文/中文 md 各自切成块序列（标题/段落/公式块/列表/图片/表格/代码）
2. **配对**：英文块[i] ↔ 中文块[i]，数量校验（逐段翻译保证一致，不一致报偏差位置人工修正）
3. **生成 paracol LaTeX**：
   - 超宽横向页面（≈两个 A4 竖版拼接），`\documentclass[11pt]{ctexart}` + `paracol/graphicx/amsmath/booktabs/hyperref`
   - paracol 两栏各占一个 A4 竖版宽度
   - 论文标题、章节标题用**跨栏** `leftcolumn*`（横跨两 A4）
   - 每对内容 `\begin{leftcolumn}`（英文）+ `\begin{rightcolumn}`（中文），paracol 保证同高度对齐、跨页自动同步
   - **公式**：左右各自保留 `\tag{n}` 编号（1:1 对应原版）
   - **图片**：栏内流式放置（不用跨栏浮动体），左栏英文图注、右栏中文图注，各归各语言
   - **表格**：左右各自排版翻译
   - 中文字体：SimSun/SimHei（xelatex + ctex 自动配置）
4. **xelatex 编译 2-3 遍**

### 5.2 中文单栏还原 PDF（make_single.py）

- `full_zh.md` → pandoc 转 LaTeX → 套 `single.tex`（ctexart 单栏模板，**保留 `\tag` 公式编号**，还原原论文单栏 arXiv 风格）→ xelatex
- 图片路径经 pandoc `--resource-path` 指向 images/ 目录

### 5.3 对照版 md（可选，make_bilingual_md.py）

- 输出左英右中的对照版（两列 Markdown 表格，段落对齐）——供无需 PDF 时的轻量阅读/二次编辑

## 6. 输出参数化（四态可选参数）

四个输出物是**可选参数，可任意组合**，一次可只生成其中任意一个或多个：

| 输出 | 参数标识 |
|------|---------|
| 纯中文 md | `zh_md` |
| 对开双栏对照 PDF | `bilingual_pdf` |
| 中文单栏还原 PDF | `single_pdf` |
| 对照版 md | `bilingual_md` |

统一入口 `run.py` 接收 `--outputs zh_md,bilingual_pdf,single_pdf` 组合。**默认输出集 = `zh_md + bilingual_pdf + single_pdf`**（对照版 md 默认不输出，需显式加入 `bilingual_md`）。脚本层面各输出生成独立、互不依赖，便于任意组合。

## 7. validate.py 三态校验（分层设计）

**脚本只能穷尽结构性/可计数的信号；语义层由 agent/review 兜底。**

```
[FAIL] 必须为 0，否则阻断交付：
  ├── $$ 块级配对（逐块解析，非仅偶数）
  ├── 内联 $ 闭合（排除 \$ 转义）
  ├── <sup>/</sup> 等 HTML 标签配对
  ├── \uFFFD 乱码计数 == 0
  └── 图片引用：源 md == 译文 md == 磁盘实际存在

[WARN] 脚本只标记"可疑信号"，交 agent/review 复核：
  ├── 孤立双空格/断裂的公式片段
  ├── 术语表映射不一致（术语表存在时）
  ├── 未翻译英文占比过高
  └── 超短公式/疑似丢内容行

[SKIP] 脚本不触碰，SKILL.md 明确由 agent/review 负责：
  ├── OCR 拼写错误语义修复（efect→effect 等）
  ├── 公式丢符号的语义推断（$X→Y$ 补箭头）
  └── 术语选词正确性、前后逻辑、引用关系
```

**定位**：机械层守门员。PASS 只代表结构完整，不代表翻译语义正确；SKILL.md 验证阶段明确"脚本报告 + agent 语义审查"双层门禁。

## 8. 错误处理

| 故障 | 应对 |
|------|------|
| MinerU API 失败 | 重试 + 超时 + 明确报错（复用 extract-report 模式） |
| xelatex 编译失败 | 解析错误日志 → 定位公式 → 清洗重编 → 仍失败则报告具体行 |
| 块配对数量不一致 | 报告首个偏差位置，人工修正 |
| 图片缺失 | validate FAIL 阻断，列出缺失文件 |
| 乱码未清零 | validate FAIL 阻断 |

## 9. 版本范围

### v1（本次实现）
1. 输入：MinerU API（`.env`）+ 本地 MinerU 产物，双路径
2. 翻译：**单篇顺序**，agent 逐段翻译（公式/图片/表格/引用保留，乱码推断修复，术语表统一）
3. 输出：四态可选参数任意组合，默认全出
4. 对开双栏对照 PDF、中文单栏还原 PDF、对照版 md
5. `validate.py` 三态校验
6. 端到端测试：父目录真实论文

### v2（后续迭代）
1. **多 agent 并行翻译**：按章节切块 → 预建**共享术语表** → 多个翻译 subagent 并行各翻一块（公式/图片引用跨块由 SKILL.md 规则约束）→ 合并
2. **隔离上下文的 review agent**：
   - **独立 subagent**，只读完整译文 + 源文，不继承任何翻译 agent 的上下文（避免"作者偏见"）
   - 职责四查：**① 名词翻译一致性**（跨块同词同译）② **前后逻辑**（证明步骤、章节衔接）③ **引用关系**（`[N]` 编号与参考文献对应）④ **结构完整性**（标题层级、公式/图片/表格无缺漏）
   - 产出：**结构化问题清单 + 修订稿**（主 agent 裁决后应用）
3. 编排机制：SKILL.md 方法论 + 执行时主 agent 用 TaskCreate/subagent 编排（保持方案 A 的通用性）

**v1 先不并发的理由**：并发翻译的前提是 PDF 生成线先跑通（块切分/配对稳定、xelatex 模板正确）；v1 顺序翻译的 full_zh.md 可作为 v2 的对照基准（术语表、格式规范、审查清单从 v1 沉淀）。

## 10. 测试策略

- **端到端**：用父目录真实论文（2242 行、84 公式、5 图）作为验收数据
- **冒烟**：`tests/sample/` 小样例 md 跑通 4 个脚本
- **验证标准**：对开双栏 PDF 段落对齐、公式渲染正确、图表各归各语言；单栏 PDF 编译零错误；validate 全 FAIL 项清零

## 11. 待决项

- LICENSE 采用 MIT（待用户最终确认）
- v1 验收后即进入 v2 迭代（并发 + review agent）
