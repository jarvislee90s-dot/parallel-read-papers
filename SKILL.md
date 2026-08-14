---
name: paper-translate
description: 把英文论文 PDF 翻译为中文，并按需生成四态输出（纯中文 md、对开双栏中英对照 PDF、中文单栏还原 PDF、对照版 md）。输入支持 MinerU API 解析（token 在 config/.env）或本地 MinerU 产物。触发场景：翻译这篇论文、论文翻译成中文、生成中英对照 PDF、把论文还原为 PDF 等。
---

# PaperTranslate

把英文论文（MinerU 解析的 full.md）逐段翻译为中文，并按 `--outputs` 生成四态输出。

## 前置检查

- 若 `config/.env` 无 `MINERU_API_TOKEN` 且需要 API 解析：提示用户参考 `config/.env.example` 配置（https://mineru.net/apiManage/token）。
- 若本地已有 MinerU 产物目录（含 `full.md` + `images/`）：跳过 API 解析，直接使用。

## 工作流（5 阶段）

### 1. 准备
- 用 `python -m scripts.validate <full.md> <full_zh.md> --image-dir <dir>` 建立基线（先仅对源做检查）
- 统计源 md 行数、图片引用数（`grep -c '!\[.*\](images/'`）
- **乱码修复**：源 md 含 U+FFFD 的，翻译时按上下文推断修复（公式丢失变量/箭头、正文丢失符号）
- **OCR 拼写还原**：源 md 的系统性错字（如 "efect"→"effect"、"coefect"→"coeffect"）按语义识别还原
- **公式清洗**：合并断裂 `$$`、转义内联 `$` 中裸下划线、去多余 `\begin{array}` 包装
- 构建**术语表**（见 §术语表），确保全文同词同译

### 2. 翻译（agent 自己执行，逐段）
- **逐段翻译，不概括**：每个英文段落 ↔ 一段中文；保留全部 LaTeX 公式（`$...$`/`$$...$$`）、图片引用 `![](images/…)`、代码块、`<sup>` 上标
- References 章节保留英文原文（作者/标题/期刊/会议名不翻译）
- 标题、图注、表注翻译为中文；专有名词（VSCode、Koishi、Moggi 等）保留英文
- 术语首次出现附英文，如「可逆效应（revertible effect）」
- 公式内容（符号、结构、`\tag{n}` 编号）**保持原样**

### 3. 生成输出
```bash
python -m scripts.run --source <目录或PDF> --outputs zh_md,bilingual_pdf,single_pdf,bilingual_md --out-dir out
```
- 默认输出：`zh_md + bilingual_pdf + single_pdf`（对照版 md 需显式加入 `bilingual_md`）
- 对开双栏：左英文、右中文、段落对齐、图表各归各语言；单栏：还原原论文排版

### 4. 校验
```bash
python -m scripts.validate full.md full_zh.md --image-dir <目录> [--term-file 术语表.json]
```
- **FAIL 必须为 0**：公式闭合、HTML 标签、乱码、图片一致性
- **WARN 交 agent 复核**：孤立双空格、未翻译长句、术语映射
- **SKIP（agent 兜底）**：OCR 错字语义修复、公式丢符号推断、术语选词正确性、前后逻辑、引用关系

### 5. 交付
- 复核 WARN 项、抽查 3-5 处术语一致性
- 确认四态输出齐全（按所选 outputs）
- 提交产物

## 术语表约定
翻译开始前先扫描原文构建术语表（类型论/编程语言领域示例，按论文领域自建）：

| English | 中文 |
|---------|------|
| composability | 可组合性 |
| effect | 效应 |
| coeffect | 余效应 |
| revertible | 可逆的 |
| reactive | 响应式 |
| component | 组件 |
| fiber | 纤维 |
| context | 上下文 |
| dynamic composition | 动态组合 |
| dependency | 依赖 |
| monad / comonad | 单子 / 余单子 |
| hot module replacement | 热模块替换 |
| observational equivalence | 观测等价 |
| preservation / progress / confluence | 保真 / 进展性 / 合流性 |

原则：全篇同一术语同一译法；专有名词保留英文；首次出现中英对照。

## 文件结构
```
PaperTranslate/
├── SKILL.md
├── README.md
├── config/.env.example      # MINERU_API_TOKEN（复制为 .env）
├── scripts/
│   ├── run.py               # 统一入口 --outputs
│   ├── mineru_convert.py    # MinerU API 解析
│   ├── validate.py          # 三态校验
│   ├── copy_images.py       # 图片复制
│   ├── make_single.py       # 中文单栏 PDF
│   ├── make_bilingual_md.py # 对照版 md
│   └── make_bilingual.py    # 对开双栏 PDF
├── templates/
│   ├── single.tex
│   └── bilingual.tex
└── tests/
```

## 依赖
- Python 3.10+（`pip install -r requirements.txt`）
- pandoc、TeX Live（xelatex + ctex）、中文字体
