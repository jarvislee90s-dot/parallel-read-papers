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
- **OCR 拼写还原**：源 md 的系统性错字按语义识别还原，**注意含大写形式**：
  `efect→effect`、`coefect→coeffect`、`Efect→Effect`、`Coefect→Coeffect`、
  `targe→target`、`effec→effect`、`difering→differing`；References 段的引用标题/URL 保留原文
- **公式清洗**：合并断裂 `$$`、转义内联 `$` 中裸下划线、去多余 `\begin{array}` 包装；
  **`$ `（`$` 后跟空格）会被 pandoc 转义为 `\$`**（导致 `\mathfrak`/`\mathrm` 进文本模式报错），
  需去掉空格；**array 声明列数不得少于单元格数**（否则 `Extra alignment tab`），
  如 `{r c l r c l}` 配 7 个单元格要补成 `{r c l r c l c}`
- 构建**术语表**（见 §术语表），确保全文同词同译

### 2. 翻译（agent 自己执行，逐段）
- **逐段翻译，不概括**：每个英文段落 ↔ 一段中文；保留全部 LaTeX 公式（`$...$`/`$$...$$`）、图片引用 `![](images/…)`、代码块、`<sup>` 上标
- References 章节保留英文原文（作者/标题/期刊/会议名不翻译）
- 标题、图注、表注翻译为中文；专有名词（VSCode、Koishi、Moggi 等）保留英文
- 术语首次出现附英文，如「可逆效应（revertible effect）」
- 公式内容（符号、结构、`\tag{n}` 编号）**保持原样**

### 3. 生成输出
```bash
python -m scripts.run --source <目录或PDF> --outputs zh_md,bilingual_pdf,single_pdf,bilingual_md --out-dir example
```
- 默认输出：`zh_md + bilingual_pdf + single_pdf`（对照版 md 需显式加入 `bilingual_md`）
- **输出命名**：英文相关输出取**英文论文标题** slug，中文相关输出取**中文标题** slug
  （均提取失败时回退输入文件名 stem），如：
  `<英文标题>_bilingual.pdf`、`<英文标题>_bilingual.md`、`<中文标题>_zh.md`、`<中文标题>_single.pdf`
- 对开双栏：**每栏自成一体**——左栏为完整英文原文（标题/作者/章节标题/正文/公式/图/表），
  右栏为完整中文译文（全部翻译）；段落首行对齐、两栏互相等待、图表各归各语言；单栏：还原原论文排版

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

## 常见坑与修复（踩坑记录）

按踩坑频率/危害排序，脚本已自动处理的部分标注「脚本自动」：

1. **paracol 同步语义（最易踩）**：`leftcolumn*`/`rightcolumn*`（星号=同步）的同步点
   设在「最深一栏底部」。**右栏必须用非同步 `rightcolumn`**——若用 `rightcolumn*`，
   中文块会被放到左栏英文块底部、整体低一行，产生「英文标题行1、中文标题行2、
   英文作者行3、中文作者行4」的中英文交错。正确结构（make_bilingual.py 已实现）：
   `\begin{leftcolumn*} 英文 \end{leftcolumn*}` + `\begin{rightcolumn} 中文 \end{rightcolumn}`。
2. **xelatex 崩溃 `map_char_to_glyph`**：正文裸 Unicode 数学符号（CJK 文本中的 `∘`/`∂`/`Γ` 等）
   触发 xelatex 内部错误 → 对开双栏改用 **lualatex**（make_bilingual.py 已用；ctex+fontspec
   中文渲染一致）。lualatex 日志为 **UTF-16 编码**，调试读日志需 `decode('utf-16-le')`。
3. **pandoc pipe table 列宽 `p{(\linewidth-N\tabcolsep)*\real{f}}`**：普通 LaTeX 不接受
   LaTeX3 的 `\real`，lualatex 报 `Missing number / Illegal unit`（两处大表曾出 ~230 错）
   → 转 `p{\dimexpr{f}\linewidth-{fN}\tabcolsep\relax}`（脚本 `_fix_table_widths` 已自动）。
4. **HTML `<table>` 被 pandoc 压成单列堆叠**：pandoc 把 HTML 表转 LaTeX 时丢列宽，
   5 列表变成竖排文本 → 需先转 pipe table（脚本 `html_table_to_pipe` 已自动；MinerU 源的
   表格常见 HTML 形式，本坑使任意论文源可直接使用，无需手工改源）。
5. **模板注释不得含占位符 `%%BODY%%`**：`template.replace("%%BODY%%", body)` 会把整段 body
   塞进注释行，导致 `\begin{document} ended by \end{leftcolumn*}`（bilingual.tex 曾踩）。
6. **PDF 文件被 Chrome/Acrobat 锁定**：lualatex 报 `I can't write on file ...pdf` →
   改用新输出名生成或让用户关闭查看器（Windows 常见，handoff 有记录）。
7. **断裂数学 `$ {`（`$` 后跟空格）**：pandoc 把 `$ ` 转义为 `\$`，`\mathfrak`/`\mathrm`
   进文本模式报 `allowed only in math mode` → 源清洗时去掉 `$` 后空格。
8. **array 列数不匹配**：声明列数 < 单元格数 → `Extra alignment tab has been changed to \cr`，
   需补齐列数声明（本论文 effect 数组曾 `{r c l r c l}` 配 7 单元格）。
9. **OCR 错字含大写**：小写替换后漏掉句首/标题的大写形式（`Efect`/`Coefect`/`Targe`），
   需大小写都处理（见 §准备·OCR 拼写还原）。
10. **作者上标 `extsuperscript` 显示成文字**：`re.sub` 替换串里 `\t` 会被解释为制表符
    吞掉反斜杠 → 替换串必须写 `r"\\textsuperscript{...}"`（双反斜杠）。

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
- pandoc、TeX Live（中文单栏用 xelatex + ctex；对开双栏用 **lualatex** + ctex + paracol，见 `make_bilingual.py` 说明）、中文字体
