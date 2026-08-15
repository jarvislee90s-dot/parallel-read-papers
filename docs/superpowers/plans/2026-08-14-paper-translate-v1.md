# PaperTranslate V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 PaperTranslate skill 的 V1：接收 MinerU API 解析或本地 MinerU 产物的论文 md，agent 逐段翻译为中文，按 `--outputs` 参数生成四态输出（纯中文 md、对开双栏对照 PDF、中文单栏还原 PDF、对照版 md），并提供 validate 三态校验。

**Architecture:** SKILL.md 方法论驱动 + scripts 机械化。脚本职责：`mineru_convert.py`（PDF→full.md）、`validate.py`（三态校验）、`copy_images.py`（图片复制）、`make_single.py`（中文单栏 PDF：pandoc→ctexart→xelatex）、`make_bilingual_md.py`（对照版 md）、`make_bilingual.py`（对开双栏 PDF：md 块切分配对→paracol→xelatex）、`run.py`（统一入口 `--outputs`）。

**Tech Stack:** Python 3.10+、pandoc、TeX Live xelatex、ctexart、paracol、requests、python-dotenv、pytest。

**前置条件：** 设计文档 `docs/superpowers/specs/2026-08-14-paper-translate-design.md` 已批准。本机已装 pandoc + TeX Live 2025 + SimSun/SimHei 字体。

**测试数据：** 父目录真实论文 `E:\LLMproject\Cordis\paper.pdf-bd13ec9e-de16-402b-b201-7b06202e44e5\full.md`（2242 行、84 公式、5 图）。测试样例 `tests/sample/`。

---

### Task 1: 仓库基础设施（LICENSE、.gitignore、README、config、requirements）

**Files:**
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `README.md`
- Create: `config/.env.example`
- Create: `requirements.txt`
- Create: `config/.env`（复制自 `.env.example`，占位空 token）
- Create: `scripts/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 创建 LICENSE（MIT）**

```text
MIT License

Copyright (c) 2026 PaperTranslate contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: 创建 .gitignore**

```gitignore
# 敏感配置（真实 token 不入库）
config/.env

# Python
__pycache__/
*.pyc
.venv/
venv/

# 输出产物
*.pdf
out/
_output/
temp/

# 测试生成物
tests/sample/out/
.pytest_cache/
```

- [ ] **Step 3: 创建 requirements.txt**

```text
requests>=2.31
python-dotenv>=1.0
pytest>=8.0
```

- [ ] **Step 4: 创建 config/.env.example**

```env
# 复制本文件为 config/.env 并填入真实 token（https://mineru.net/apiManage/token）
MINERU_API_TOKEN=
```

- [ ] **Step 5: 创建 config/.env（从 example 复制，token 留空占位）**

- [ ] **Step 6: 创建 scripts/__init__.py 与 tests/__init__.py（空文件）**

- [ ] **Step 7: 创建 README.md 骨架**

```markdown
# PaperTranslate

把英文论文 PDF 翻译为中文，并生成多形态输出（纯中文 md、对开双栏中英对照 PDF、中文单栏还原 PDF、对照版 md）。

## 依赖
- Python 3.10+（`pip install -r requirements.txt`）
- pandoc
- TeX Live（xelatex，含 ctex 宏包）
- 中文字体（Windows：SimSun/SimHei）

## 配置
复制 `config/.env.example` 为 `config/.env`，填入 `MINERU_API_TOKEN`（https://mineru.net/apiManage/token）。

## 使用（V1）
1. 解析：`python scripts/run.py --source <paper.pdf> --outputs zh_md`（或用本地 MinerU 产物目录）
2. 翻译：在 SKILL.md 流程指导下，agent 将 `full.md` 翻译为 `full_zh.md`
3. 生成：`python scripts/run.py --source <dir> --outputs bilingual_pdf,single_pdf`
```

- [ ] **Step 8: 提交**

```bash
git add LICENSE .gitignore README.md requirements.txt config/ scripts/__init__.py tests/__init__.py
git commit -m "chore: 初始化仓库基础设施（MIT、README、config、依赖）"
```

---

### Task 2: 测试样例与 pytest 基线

**Files:**
- Create: `tests/sample/sample_en.md`
- Create: `tests/sample/sample_zh.md`
- Create: `tests/sample/images/sample.jpg`（占位图片）
- Create: `pytest.ini`

- [ ] **Step 1: 创建 pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 2: 创建样例英文 md（覆盖全部块类型）**

`tests/sample/sample_en.md`：
```markdown
# Sample Paper Title

Yifan Shi<sup>1,2</sup>, Wei Zhang<sup>1</sup>

<sup>1</sup>Peking University <sup>2</sup>DeepSeek-AI

## Abstract

This is a sample paragraph with inline math $x + y = z$ and normal text.

$$
E = m c ^ { 2 } \tag{1}
$$

Another paragraph after the formula, with a list below:

- first item
- second item with math $\alpha + \beta$

![figure](images/sample.jpg)

| Column A | Column B |
|----------|----------|
| 1 | 2 |
| 3 | 4 |
```

- [ ] **Step 3: 创建样例中文 md（逐段对应翻译）**

`tests/sample/sample_zh.md`：
```markdown
# 样例论文标题

Yifan Shi<sup>1,2</sup>, Wei Zhang<sup>1</sup>

<sup>1</sup>北京大学 <sup>2</sup>DeepSeek-AI

## 摘要

这是一个样例段落，包含行内公式 $x + y = z$ 和普通文字。

$$
E = m c ^ { 2 } \tag{1}
$$

公式之后还有另一段，包含一个列表：

- 第一项
- 第二项（含公式 $\alpha + \beta$）

![figure](images/sample.jpg)

| 列A | 列B |
|-----|-----|
| 1 | 2 |
| 3 | 4 |
```

- [ ] **Step 4: 创建占位图片**

```bash
mkdir -p tests/sample/images
python -c "open('tests/sample/images/sample.jpg','wb').write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01')"
```

- [ ] **Step 5: 验证 pytest 可运行（无测试也应退出码 0）**

Run: `python -m pytest -q`
Expected: `no tests ran` 或 `0 passed`

- [ ] **Step 6: 提交**

```bash
git add pytest.ini tests/sample/
git commit -m "test: 添加测试样例与 pytest 基线"
```

---

### Task 3: validate.py — FAIL 组（公式闭合/HTML 标签/乱码/图片一致性）

**Files:**
- Create: `scripts/validate.py`
- Test: `tests/test_validate.py`

- [ ] **Step 1: 写失败测试**

`tests/test_validate.py`：
```python
from pathlib import Path
import scripts.validate as v

SAMPLE_DIR = Path(__file__).parent / "sample"

def test_display_math_closed():
    ok = "para\n$$\na + b\n$$\nend\n"
    bad = "para\n$$\na + b  # 未闭合\nend\n"
    assert v.check_display_math(ok) == []
    assert len(v.check_display_math(bad)) >= 1

def test_inline_math_closed():
    assert v.check_inline_math("text $x$ and $y$") == []
    assert len(v.check_inline_math("text $x and $y")) >= 1  # 奇数个 $
    assert v.check_inline_math("cost is \\$5 and $x$") == []  # \$ 转义不算

def test_html_tags_paired():
    assert v.check_html_tags("a<sup>1</sup>b") == []
    assert len(v.check_html_tags("a<sup>1</sup>b<sup>2</sup>c")) >= 1  # 未闭合
    assert v.check_html_tags("a<sup>1</sup>b<sup>2</sup>") == []

def test_unicode_replacement():
    assert v.check_unicode_replacement("clean text") == []
    assert len(v.check_unicode_replacement("bad \ufffd char")) >= 1

def test_extract_image_refs():
    md = "![a](images/x.jpg)\n![b](images/y.png)\n"
    assert v.extract_image_refs(md) == {"images/x.jpg", "images/y.png"}

def test_check_images_consistency():
    en = "![f](images/a.jpg)\n"
    zh = "![f](images/a.jpg)\n"
    img_dir = SAMPLE_DIR / "images"
    assert v.check_images(en, zh, img_dir) == []  # sample.jpg 存在
    # 译文缺图 → 报错
    assert len(v.check_images("![f](images/a.jpg)\n", "no image\n", img_dir)) >= 1
    # 引用不存在的图 → 报错
    assert len(v.check_images("![f](images/none.jpg)\n", "![f](images/none.jpg)\n", img_dir)) >= 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_validate.py -v`
Expected: FAIL（`ModuleNotFoundError: scripts.validate`）

- [ ] **Step 3: 实现 validate.py（FAIL 组）**

`scripts/validate.py`：
```python
"""PaperTranslate 三态校验。

FAIL：结构性/可计数信号，必须为 0，否则阻断交付。
WARN：可疑信号，交 agent/review 复核。
SKIP：语义层，由 agent/review 负责（不在本脚本）。
"""
import re
from pathlib import Path

IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HTML_TAG_RE = re.compile(r"<(/?)(\w+)>")
# 常见配对标签（自闭合标签如 <br> 除外）
PAIRED_TAGS = {"sup", "sub", "details", "summary", "div", "span", "b", "i", "em", "strong", "table", "tr", "td", "th"}


def check_display_math(md: str) -> list[str]:
    """$$ 块级配对：移除成对 $$...$$ 后不应残留 $。"""
    reduced = re.sub(r"\$\$.*?\$\$", "", md, flags=re.S)
    if "$" in reduced:
        pos = reduced.index("$")
        ctx = reduced[max(0, pos - 30):pos + 30].replace("\n", " ")
        return [f"存在未闭合的 $$ 公式：...{ctx}..."]
    return []


def check_inline_math(md: str) -> list[str]:
    """内联 $ 闭合：先移除 $$ 块与 \\$ 转义，剩余 $ 数应为偶数。"""
    reduced = re.sub(r"\$\$.*?\$\$", "", md, flags=re.S)
    cleaned = re.sub(r"\\\$", "", reduced)
    count = cleaned.count("$")
    if count % 2 != 0:
        return [f"内联 $ 数量为奇数 {count}（存在未闭合的内联公式）"]
    return []


def check_html_tags(md: str) -> list[str]:
    """HTML 标签配对（栈式检查）。"""
    problems = []
    stack = []  # (行号, 标签)
    for lineno, line in enumerate(md.split("\n"), 1):
        for m in HTML_TAG_RE.finditer(line):
            closing, tag = m.group(1), m.group(2)
            if tag not in PAIRED_TAGS:
                continue
            if closing:
                if not stack or stack[-1][1] != tag:
                    problems.append(f"L{lineno}: </{tag}> 无匹配开标签")
                else:
                    stack.pop()
            else:
                stack.append((lineno, tag))
    for lineno, tag in stack:
        problems.append(f"L{lineno}: <{tag}> 未闭合")
    return problems


def check_unicode_replacement(md: str) -> list[str]:
    """乱码 U+FFFD 计数（OCR 丢字符的直接证据）。"""
    count = md.count("\ufffd")
    return [f"存在 {count} 个乱码字符（U+FFFD），需按上下文修复"] if count else []


def extract_image_refs(md: str) -> set[str]:
    """提取 markdown 图片引用路径集合。"""
    return set(m.group(1) for m in IMAGE_RE.finditer(md))


def check_images(en_md: str, zh_md: str, image_dir: Path) -> list[str]:
    """图片一致性：源 md == 译文 md == 磁盘实际存在。"""
    problems = []
    en_refs = extract_image_refs(en_md)
    zh_refs = extract_image_refs(zh_md)
    if en_refs != zh_refs:
        only_en = sorted(en_refs - zh_refs)
        only_zh = sorted(zh_refs - en_refs)
        if only_en:
            problems.append(f"译文缺失图片引用：{only_en}")
        if only_zh:
            problems.append(f"译文多出图片引用：{only_zh}")
    for ref in sorted(zh_refs):
        p = Path(ref) if Path(ref).is_absolute() else image_dir / ref
        if not p.exists():
            problems.append(f"图片文件不存在：{ref}")
    return problems
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_validate.py -v`
Expected: 6 passed

- [ ] **Step 5: 提交**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: validate.py FAIL 组（公式闭合/HTML 标签/乱码/图片一致性）"
```

---

### Task 4: validate.py — WARN 组与 run_validation 入口

**Files:**
- Modify: `scripts/validate.py`
- Test: `tests/test_validate.py`

- [ ] **Step 1: 写失败测试（追加到 test_validate.py）**

```python
def test_check_term_map_warn():
    md = "这里提到可组合性（composability），后面又出现 composability。"
    term_map = {"composability": "可组合性"}
    assert v.check_term_map(md, term_map) == []
    # 英文术语出现但译文里从未出现对应中文 → WARN
    bad = "这里提到 composability 但没有中文。"
    assert len(v.check_term_map(bad, term_map)) >= 1

def test_warn_signals():
    assert v.warn_signals("normal 中文段落。") == []
    # 孤立双空格（公式外）
    assert len(v.warn_signals("a  b  丢符号嫌疑")) >= 1
    # 疑似未翻译英文长句
    assert len(v.warn_signals("This is a very long English sentence that remains untranslated here.")) >= 1

def test_run_validation_shape():
    en = open(SAMPLE_DIR / "sample_en.md", encoding="utf-8").read()
    zh = open(SAMPLE_DIR / "sample_zh.md", encoding="utf-8").read()
    result = v.run_validation(en, zh, SAMPLE_DIR / "images")
    assert set(result.keys()) == {"fail", "warn"}
    assert isinstance(result["fail"], list)
    assert isinstance(result["warn"], list)
    # 样例应全 FAIL 通过（结构一致、无乱码）
    assert result["fail"] == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_validate.py -v`
Expected: 新增 3 个 FAIL（`AttributeError: module 'scripts.validate' has no attribute 'check_term_map'`）

- [ ] **Step 3: 实现 WARN 组与入口（追加到 validate.py）**

```python
def check_term_map(zh_md: str, term_map: dict[str, str]) -> list[str]:
    """术语映射一致性（WARN）：术语表存在时，英文原词与中文译法应同时出现。"""
    warns = []
    for en, zh in term_map.items():
        if not en or not zh:
            continue
        if en in zh_md and zh not in zh_md:
            warns.append(f"术语 '{en}' 在译文中出现，但全文未见对应中文 '{zh}'，请核对译法一致性")
    return warns


def warn_signals(zh_md: str) -> list[str]:
    """可疑信号（WARN）：孤立双空格、疑似未翻译英文长句。"""
    warns = []
    for lineno, line in enumerate(zh_md.split("\n"), 1):
        if re.search(r"[A-Za-z]\s{2,}[A-Za-z]", line) and "$" not in line:
            warns.append(f"L{lineno}: 疑似孤立双空格（可能丢符号）：{line.strip()[:60]}")
        if re.search(r"[A-Za-z]{4,}( [A-Za-z]{4,}){5,}", line):
            warns.append(f"L{lineno}: 疑似未翻译的英文长句：{line.strip()[:60]}")
    return warns[:20]  # 截断避免刷屏


def run_validation(en_md: str, zh_md: str, image_dir: Path, term_map: dict[str, str] | None = None) -> dict:
    """执行完整校验，返回 {'fail': [...], 'warn': [...]}。"""
    fail: list[str] = []
    fail += check_display_math(zh_md)
    fail += check_inline_math(zh_md)
    fail += check_html_tags(zh_md)
    fail += check_unicode_replacement(zh_md)
    fail += check_images(en_md, zh_md, image_dir)
    warn: list[str] = []
    if term_map:
        warn += check_term_map(zh_md, term_map)
    warn += warn_signals(zh_md)
    return {"fail": fail, "warn": warn}


def main() -> int:
    """CLI：python -m scripts.validate <en.md> <zh.md> --image-dir <dir> [--term-file <json>]"""
    import argparse
    import json
    parser = argparse.ArgumentParser(description="PaperTranslate 三态校验")
    parser.add_argument("en_md", help="英文源 md")
    parser.add_argument("zh_md", help="中文译文 md")
    parser.add_argument("--image-dir", required=True, help="images 目录")
    parser.add_argument("--term-file", default=None, help="术语表 JSON {英文: 中文}")
    args = parser.parse_args()

    en_md = Path(args.en_md).read_text(encoding="utf-8")
    zh_md = Path(args.zh_md).read_text(encoding="utf-8")
    term_map = None
    if args.term_file:
        term_map = json.loads(Path(args.term_file).read_text(encoding="utf-8"))
    result = run_validation(en_md, zh_md, Path(args.image_dir), term_map)

    print("=== FAIL（阻断项）===")
    for msg in result["fail"]:
        print("  [FAIL]", msg)
    print("=== WARN（复核项）===")
    for msg in result["warn"]:
        print("  [WARN]", msg)
    print(f"\nFAIL: {len(result['fail'])} 项, WARN: {len(result['warn'])} 项")
    return 1 if result["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_validate.py -v`
Expected: 9 passed

- [ ] **Step 5: 用样例做 CLI 冒烟**

Run: `python -m scripts.validate tests/sample/sample_en.md tests/sample/sample_zh.md --image-dir tests/sample`
Expected: 退出码 0，FAIL 0 项（图片路径 `images/sample.jpg` 相对 `--image-dir` 解析需以 `tests/sample` 为 base）

注：CLI 冒烟若 `--image-dir tests/sample` 时 `images/sample.jpg` 解析为 `tests/sample/images/sample.jpg` ✓。

- [ ] **Step 6: 提交**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: validate.py WARN 组与 run_validation/CLI 入口"
```

---

### Task 5: copy_images.py

**Files:**
- Create: `scripts/copy_images.py`
- Test: `tests/test_copy_images.py`

- [ ] **Step 1: 写失败测试**

`tests/test_copy_images.py`：
```python
from pathlib import Path
import scripts.copy_images as ci

SAMPLE = Path(__file__).parent / "sample"

def test_copy_referenced_images(tmp_path):
    en_md = SAMPLE / "sample_en.md"
    src_dir = SAMPLE  # 包含 images/sample.jpg
    out_dir = tmp_path / "out"
    copied = ci.copy_referenced_images(en_md, src_dir, out_dir)
    target = out_dir / "images" / "sample.jpg"
    assert target.exists()
    assert target in copied

def test_missing_image_reported(tmp_path):
    en_md = SAMPLE / "sample_en.md"
    src_dir = tmp_path / "empty"  # 无 images
    src_dir.mkdir()
    missing = ci.copy_referenced_images(en_md, src_dir, tmp_path / "out")
    assert "sample.jpg" in missing  # 返回缺失列表
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_copy_images.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现**

`scripts/copy_images.py`：
```python
"""复制 md 引用的图片到输出目录，返回 (已复制列表, 缺失列表)。"""
import shutil
from pathlib import Path
import re

IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def copy_referenced_images(md_file: Path, src_dir: Path, out_dir: Path) -> tuple[list[Path], list[str]]:
    """复制 md 中引用的图片（相对路径按 src_dir 解析）到 out_dir 对应相对位置。"""
    md_text = md_file.read_text(encoding="utf-8")
    refs = set(m.group(1) for m in IMAGE_RE.finditer(md_text))
    copied: list[Path] = []
    missing: list[str] = []
    for ref in sorted(refs):
        src = Path(ref) if Path(ref).is_absolute() else src_dir / ref
        dst = out_dir / ref
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst)
        else:
            missing.append(ref)
    return copied, missing


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="复制 md 引用图片")
    parser.add_argument("md", help="md 文件路径")
    parser.add_argument("--src-dir", required=True, help="图片源目录（md 相对引用基准）")
    parser.add_argument("--out-dir", required=True, help="输出目录")
    args = parser.parse_args()
    copied, missing = copy_referenced_images(Path(args.md), Path(args.src_dir), Path(args.out_dir))
    print(f"已复制 {len(copied)} 张图片")
    if missing:
        print(f"缺失 {len(missing)} 张：{missing}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_copy_images.py -v`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add scripts/copy_images.py tests/test_copy_images.py
git commit -m "feat: copy_images.py 图片复制"
```

---

### Task 6: mineru_convert.py（MinerU API 解析）

**Files:**
- Create: `scripts/mineru_convert.py`
- Test: `tests/test_mineru_convert.py`

说明：核心 API 模式参考用户现有 skill `extract-report/pdf_to_md.py`（MinerU API v4）。真实上传/轮询需网络与 token，单元测试用 `unittest.mock` 打桩。

- [ ] **Step 1: 写失败测试**

`tests/test_mineru_convert.py`：
```python
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import scripts.mineru_convert as mc

def test_upload_file_calls_batch_api(tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    with patch("scripts.mineru_convert.requests") as mock_req:
        mock_req.post.return_value.json.return_value = {
            "code": 0,
            "data": {"batch_id": "b1", "file_urls": ["https://oss/upload"]},
        }
        batch_id = mc.upload_file(pdf, "token")
        assert batch_id == "b1"
        # 断言请求带 token 与文件信息
        post_kwargs = mock_req.post.call_args
        assert post_kwargs.kwargs["headers"]["Authorization"] == "Bearer token"
        assert post_kwargs.kwargs["json"]["files"] == [{"name": "paper.pdf"}]
        # PUT 上传到 OSS
        mock_req.put.assert_called_once()
        mock_req.put.call_args.kwargs["data"] == b"%PDF-1.4 fake"

def test_get_token_reads_env(tmp_path, monkeypatch):
    # .env 位于 config/ 目录
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ".env").write_text("MINERU_API_TOKEN=abc123\n")
    monkeypatch.setattr(mc, "CONFIG_DIR", config_dir)
    assert mc.get_token() == "abc123"

def test_get_token_missing_raises(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ".env").write_text("MINERU_API_TOKEN=\n")
    monkeypatch.setattr(mc, "CONFIG_DIR", config_dir)
    try:
        mc.get_token()
        assert False, "应抛出 ValueError"
    except ValueError:
        pass

def test_poll_and_download_done(tmp_path):
    # 模拟轮询一次成功 + zip 下载 + 解压
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF")
    out_dir = tmp_path / "out"
    zip_bytes = _make_zip({"full.md": "# title\n", "images/": None})
    with patch("scripts.mineru_convert.requests") as mock_req:
        mock_req.get.side_effect = [
            MagicMock(json=lambda: {"data": {"extract_result": [
                {"state": "done", "full_zip_url": "https://zip", "err_msg": ""}]}}),
            MagicMock(content=zip_bytes),
        ]
        result = mc.download_result("https://zip", out_dir)
        assert (out_dir / "full.md").exists()

def _make_zip(files: dict) -> bytes:
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in files.items():
            if content is None:
                continue
            z.writestr(name, content)
    return buf.getvalue()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_mineru_convert.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现**

`scripts/mineru_convert.py`：
```python
"""MinerU API 解析：PDF → full.md + images/（API 模式参考 extract-report/pdf_to_md.py）。"""
import os
import re
import time
import zipfile
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# config/ 目录位于 skill 根（scripts/ 的上一级）
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

UPLOAD_API = "https://mineru.net/api/v4/file-urls/batch"
RESULT_API = "https://mineru.net/api/v4/extract-results/batch/{batch_id}"


def _load_env() -> None:
    env_file = CONFIG_DIR / ".env"
    if env_file.exists():
        if load_dotenv:
            load_dotenv(env_file)
        else:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())


def get_token() -> str:
    """从 config/.env 读取 MinerU token。"""
    _load_env()
    token = os.getenv("MINERU_API_TOKEN", "").strip()
    if not token:
        raise ValueError("未找到 MINERU_API_TOKEN，请在 config/.env 中配置（参考 config/.env.example）")
    return token


def upload_file(file_path: Path, token: str) -> str:
    """上传 PDF 到 MinerU，返回 batch_id。"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在：{file_path}")
    header = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        UPLOAD_API,
        headers=header,
        json={"files": [{"name": file_path.name}], "is_ocr": True, "enable_table": True},
        timeout=60,
    )
    resp.raise_for_status()
    info = resp.json()
    if info.get("code") != 0:
        raise ValueError(f"上传链接申请失败：{info.get('msg')}")
    upload_url = info["data"]["file_urls"][0]
    batch_id = info["data"]["batch_id"]
    with open(file_path, "rb") as f:
        resp = requests.put(upload_url, data=f.read(), timeout=300)
    resp.raise_for_status()
    return batch_id


def poll_result(batch_id: str, token: str, timeout: int = 600, interval: int = 5) -> dict:
    """轮询任务状态直到 done/failed，返回文件结果 dict。"""
    header = {"Authorization": f"Bearer {token}"}
    url = RESULT_API.format(batch_id=batch_id)
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        resp = requests.get(url, headers=header, timeout=60)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        extract = data.get("extract_result") or []
        if not extract:
            continue
        file_result = extract[0]
        state = file_result.get("state")
        if state == "done":
            return file_result
        if state == "failed":
            raise RuntimeError(f"MinerU 解析失败：{file_result.get('err_msg')}")
    raise TimeoutError(f"MinerU 任务超时（>{timeout}s）")


def download_result(zip_url: str, out_dir: Path) -> Path:
    """下载并解压 MinerU 结果到 out_dir，返回 full.md 路径。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    resp = requests.get(zip_url, timeout=300)
    resp.raise_for_status()
    zip_path = out_dir / "_result.zip"
    zip_path.write_bytes(resp.content)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(out_dir)
    zip_path.unlink()
    # 找 full.md（MinerU zip 内通常根目录或一级子目录）
    for cand in (out_dir / "full.md", *sorted(out_dir.glob("*/full.md"))):
        if cand.exists():
            return cand
    raise FileNotFoundError(f"未在 {out_dir} 中找到 full.md")


def convert_pdf(pdf_path: str | Path, out_dir: str | Path) -> Path:
    """完整转换：上传 → 轮询 → 下载解压 → 返回 full.md 路径。"""
    token = get_token()
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    batch_id = upload_file(pdf_path, token)
    file_result = poll_result(batch_id, token)
    full_md = download_result(file_result["full_zip_url"], out_dir)
    print(f"解析完成：{full_md}")
    return full_md


def find_local_full_md(source_dir: str | Path) -> Path | None:
    """在目录中查找已存在的 full.md（本地 MinerU 产物）。"""
    src = Path(source_dir)
    for cand in (src / "full.md", *sorted(src.glob("*/full.md"))):
        if cand.exists():
            return cand
    return None


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="MinerU API 解析 PDF 或查找本地 full.md")
    parser.add_argument("source", help="PDF 路径或含 full.md 的目录")
    parser.add_argument("--out-dir", default=None, help="解析结果输出目录")
    args = parser.parse_args()
    src = Path(args.source)
    if src.is_dir():
        full_md = find_local_full_md(src)
        if not full_md:
            print(f"未在 {src} 找到 full.md")
            return 1
        print(f"找到本地 full.md：{full_md}")
        return 0
    out_dir = Path(args.out_dir) if args.out_dir else src.parent
    convert_pdf(src, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_mineru_convert.py -v`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add scripts/mineru_convert.py tests/test_mineru_convert.py
git commit -m "feat: mineru_convert.py MinerU API 解析（上传/轮询/下载）"
```

---

### Task 7: templates/single.tex + make_single.py（中文单栏还原 PDF）

**Files:**
- Create: `templates/single.tex`
- Create: `scripts/make_single.py`
- Test: `tests/test_make_single.py`

- [ ] **Step 1: 写失败测试**

`tests/test_make_single.py`：
```python
import shutil
from pathlib import Path
import pytest
import scripts.make_single as ms

SAMPLE = Path(__file__).parent / "sample"

@pytest.mark.skipif(shutil.which("pandoc") is None or shutil.which("xelatex") is None,
                    reason="需要 pandoc 与 xelatex")
def test_render_single_pdf(tmp_path):
    zh_md = SAMPLE / "sample_zh.md"
    out_pdf = tmp_path / "out.pdf"
    result = ms.render_single_pdf(zh_md, SAMPLE, out_pdf, Path(__file__).parent.parent / "templates")
    assert result.exists()
    assert result.stat().st_size > 1000  # 非空 PDF

def test_tex_body_generated(tmp_path):
    """不依赖 xelatex 的纯逻辑测试：生成 .tex 内容应包含公式编号与文档类。"""
    zh_md = SAMPLE / "sample_zh.md"
    tex = ms.zh_md_to_tex(zh_md, SAMPLE)
    assert "documentclass" in tex or "ctexart" in tex
    assert "E = m c" in tex  # 公式内容保留
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_make_single.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 创建模板 single.tex**

`templates/single.tex`：
```latex
% PaperTranslate 中文单栏还原 PDF 模板（ctexart 单栏，arXiv 风格）
% 由 make_single.py 填充 %%BODY%% 与 %%TITLE%% / %%AUTHORS%%
\documentclass[11pt,a4paper]{ctexart}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{hyperref}
\hypersetup{hidelinks}
\title{%%TITLE%%}
\author{%%AUTHORS%%}
\date{}
\begin{document}
\maketitle
%%BODY%%
\end{document}
```

- [ ] **Step 4: 实现 make_single.py**

`scripts/make_single.py`：
```python
"""中文单栏还原 PDF：full_zh.md → pandoc 转 LaTeX → 套 single.tex → xelatex。"""
import re
import subprocess
import sys
from pathlib import Path


def zh_md_to_tex(zh_md: Path, resource_dir: Path) -> str:
    """用 pandoc 把中文 md 转 LaTeX body（保留公式 \\tag 编号）。"""
    cmd = [
        "pandoc", "-f", "markdown", "-t", "latex",
        "--resource-path", str(resource_dir),
        "--no-highlight",
        str(zh_md),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"pandoc 转换失败：{result.stderr}")
    return result.stdout


def extract_meta(md_text: str) -> tuple[str, str]:
    """从 md 提取标题与作者（第一个 # 标题为标题，含 sup 的段落为作者，尽力而为）。"""
    title = "Untitled"
    authors = ""
    for line in md_text.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m and title == "Untitled":
            title = m.group(1).strip()
            continue
        if line.strip() and "<sup>" in line and not line.startswith("#") and not authors:
            authors = line.strip()
    return title, authors


def render_single_pdf(zh_md: Path, resource_dir: Path, output_pdf: Path, template_dir: Path) -> Path:
    """生成中文单栏还原 PDF，返回输出路径。"""
    zh_md = Path(zh_md)
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    md_text = zh_md.read_text(encoding="utf-8")
    title, authors = extract_meta(md_text)
    body = zh_md_to_tex(zh_md, resource_dir)

    template = (Path(template_dir) / "single.tex").read_text(encoding="utf-8")
    tex = (template
           .replace("%%TITLE%%", title)
           .replace("%%AUTHORS%%", authors)
           .replace("%%BODY%%", body))

    tex_path = output_pdf.with_suffix(".tex")
    tex_path.write_text(tex, encoding="utf-8")

    # xelatex 编译（两次跑目录交叉引用）
    for _ in range(2):
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={output_pdf.parent}", str(tex_path.name)],
            cwd=tex_path.parent,
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"xelatex 编译失败：\n{result.stdout[-2000:]}")
    if not output_pdf.exists():
        raise FileNotFoundError(f"未生成 PDF：{output_pdf}")
    return output_pdf


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="生成中文单栏还原 PDF")
    parser.add_argument("zh_md", help="中文 md 路径")
    parser.add_argument("--resource-dir", required=True, help="images 目录（相对引用基准）")
    parser.add_argument("--output", required=True, help="输出 PDF 路径")
    parser.add_argument("--template-dir", default=None, help="模板目录（默认 skill 内 templates/）")
    args = parser.parse_args()
    template_dir = Path(args.template_dir) if args.template_dir else Path(__file__).resolve().parent.parent / "templates"
    render_single_pdf(Path(args.zh_md), Path(args.resource_dir), Path(args.output), template_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest tests/test_make_single.py -v`
Expected: 2 passed（test_render_single_pdf 需要 pandoc+xelatex 环境，本机已具备）

- [ ] **Step 6: 用样例做真实渲染冒烟**

Run:
```bash
cd E:\LLMproject\Cordis\PaperTranslate
python -m scripts.make_single tests/sample/sample_zh.md --resource-dir tests/sample --output tests/sample/out/sample.pdf
```
Expected: 生成 `tests/sample/out/sample.pdf`，非空

- [ ] **Step 7: 提交**

```bash
git add templates/single.tex scripts/make_single.py tests/test_make_single.py
git commit -m "feat: 中文单栏还原 PDF（pandoc→ctexart→xelatex）"
```

---

### Task 8: make_bilingual_md.py（对照版 md）

**Files:**
- Create: `scripts/make_bilingual_md.py`
- Test: `tests/test_make_bilingual_md.py`

- [ ] **Step 1: 写失败测试**

`tests/test_make_bilingual_md.py`：
```python
from pathlib import Path
import scripts.make_bilingual_md as bmd

SAMPLE = Path(__file__).parent / "sample"

def test_make_bilingual_md(tmp_path):
    en = SAMPLE / "sample_en.md"
    zh = SAMPLE / "sample_zh.md"
    out = tmp_path / "bilingual.md"
    bmd.make_bilingual_md(en, zh, out)
    text = out.read_text(encoding="utf-8")
    assert "样例论文标题" in text
    assert "Sample Paper Title" in text
    assert "|" in text  # 表格结构
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_make_bilingual_md.py -v`
Expected: FAIL

- [ ] **Step 3: 实现**

`scripts/make_bilingual_md.py`：
```python
"""生成左英右中的对照版 md（两列表格，段落对齐）。"""
import re
from pathlib import Path

BLOCK_START = re.compile(r"^(#{1,6})\s|^\$\$|^```|^!\[|<table|^\|")


def _split_paragraphs(md_text: str) -> list[str]:
    """按空行切分段落（保留标题/公式/图片/列表块作为一个整体单元）。"""
    raw_blocks = [b.strip() for b in md_text.split("\n\n") if b.strip()]
    merged: list[str] = []
    for block in raw_blocks:
        if block.startswith("$$"):
            if merged and merged[-1].startswith("$$") and not merged[-1].endswith("$$"):
                merged[-1] += "\n\n" + block
            else:
                merged.append(block)
        else:
            merged.append(block)
    return merged


def make_bilingual_md(en_md: Path, zh_md: Path, output_md: Path) -> Path:
    """生成左英右中两列对照 md。"""
    en_blocks = _split_paragraphs(en_md.read_text(encoding="utf-8"))
    zh_blocks = _split_paragraphs(zh_md.read_text(encoding="utf-8"))
    if len(en_blocks) != len(zh_blocks):
        raise ValueError(f"段落数不一致：英文 {len(en_blocks)} vs 中文 {len(zh_blocks)}")

    lines = ["<!-- 中英对照版：左英文、右中文，逐段对齐 -->", ""]
    for en, zh in zip(en_blocks, zh_blocks):
        # 标题块：直接输出（不做表格）
        if re.match(r"^#{1,6}\s", en) and re.match(r"^#{1,6}\s", zh):
            lines.append(zh)
            lines.append("")
            continue
        # 公式块：居中显示
        if en.startswith("$$") or zh.startswith("$$"):
            lines.append(en)
            lines.append("")
            lines.append(zh)
            lines.append("")
            continue
        # 其他：两列表格
        en_flat = en.replace("\n", " ").replace("|", "\\|")
        zh_flat = zh.replace("\n", " ").replace("|", "\\|")
        lines.append(f"| 英文 | 中文 |")
        lines.append(f"|------|------|")
        lines.append(f"| {en_flat} | {zh_flat} |")
        lines.append("")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")
    return output_md


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="生成对照版 md")
    parser.add_argument("en_md")
    parser.add_argument("zh_md")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    make_bilingual_md(Path(args.en_md), Path(args.zh_md), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_make_bilingual_md.py -v`
Expected: 1 passed

- [ ] **Step 5: 提交**

```bash
git add scripts/make_bilingual_md.py tests/test_make_bilingual_md.py
git commit -m "feat: make_bilingual_md.py 对照版 md"
```

---

### Task 9: make_bilingual.py 核心 — split_blocks / pair_blocks

**Files:**
- Create: `scripts/make_bilingual.py`
- Test: `tests/test_make_bilingual.py`

- [ ] **Step 1: 写失败测试（核心切分配对）**

`tests/test_make_bilingual.py`：
```python
from pathlib import Path
import scripts.make_bilingual as mb

SAMPLE = Path(__file__).parent / "sample"

def _read(name):
    return (SAMPLE / name).read_text(encoding="utf-8")

def test_split_blocks_types():
    md = _read("sample_en.md")
    blocks = mb.split_blocks(md)
    types = [b["type"] for b in blocks]
    # 应包含全部块类型
    assert "heading" in types
    assert "paragraph" in types
    assert "math" in types
    assert "image" in types
    assert "list" in types
    assert "table" in types

def test_split_math_keeps_content():
    md = "before\n$$\nE = m c ^ { 2 } \\tag{1}\n$$\nafter\n"
    blocks = mb.split_blocks(md)
    math_blocks = [b for b in blocks if b["type"] == "math"]
    assert len(math_blocks) == 1
    assert "E = m c" in math_blocks[0]["content"]

def test_pair_blocks_matching():
    en_blocks = mb.split_blocks(_read("sample_en.md"))
    zh_blocks = mb.split_blocks(_read("sample_zh.md"))
    pairs, errors = mb.pair_blocks(en_blocks, zh_blocks)
    assert errors == []
    assert len(pairs) == len(en_blocks)

def test_pair_blocks_mismatch_detected():
    en = mb.split_blocks("para one\n\n$$a+b$$\n")
    zh = mb.split_blocks("para one\n")  # 少一块
    pairs, errors = mb.pair_blocks(en, zh)
    assert pairs is None
    assert any("数量不一致" in e for e in errors)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_make_bilingual.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 split_blocks / pair_blocks**

`scripts/make_bilingual.py`（本任务实现前半部分，Task 10 追加渲染部分）：
```python
"""对开双栏对照 PDF：英/中 md 块切分配对 → paracol LaTeX → xelatex。"""
import re
import subprocess
from pathlib import Path

FENCE = re.compile(r"^```|^~~~")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
MATH_OPEN = "$$"
IMAGE = re.compile(r"^!\[[^\]]*\]\([^)]+\)")
TABLE_START = re.compile(r"^<table|^\|")
LIST_ITEM = re.compile(r"^([-*+]|\d+\.)\s")
HEADING_LEVEL = re.compile(r"^#+")


def split_blocks(md: str) -> list[dict]:
    """把 markdown 切成块序列，块为 {'type','content','level'?}。"""
    lines = md.split("\n")
    n = len(lines)
    blocks: list[dict] = []
    i = 0
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        # 代码块
        if FENCE.match(stripped):
            end = i + 1
            while end < n and not FENCE.match(lines[end].strip()):
                end += 1
            blocks.append({"type": "code", "content": "\n".join(lines[i:end + 1])})
            i = end + 1
            continue
        # 标题
        m = HEADING.match(stripped)
        if m:
            blocks.append({"type": "heading", "level": len(m.group(1)), "content": stripped})
            i += 1
            continue
        # 显示公式（可跨行）
        if stripped == MATH_OPEN or stripped.startswith(MATH_OPEN):
            j = i
            buf = [lines[j]]
            while j + 1 < n and lines[j].count("$$") % 2 == 1:
                j += 1
                buf.append(lines[j])
            blocks.append({"type": "math", "content": "\n".join(buf)})
            i = j + 1
            continue
        # 图片
        if IMAGE.match(stripped):
            blocks.append({"type": "image", "content": line})
            i += 1
            continue
        # 表格（HTML 或管道，收集连续行）
        if TABLE_START.match(stripped):
            j = i
            buf = []
            while j < n:
                s = lines[j].strip()
                if TABLE_START.match(s) or s.startswith("</table>") or (buf and not s):
                    if s:
                        buf.append(lines[j])
                    else:
                        break
                    j += 1
                else:
                    break
            blocks.append({"type": "table", "content": "\n".join(buf)})
            i = j
            continue
        # 列表（收集连续列表项及缩进行）
        if LIST_ITEM.match(stripped):
            j = i
            buf = []
            while j < n:
                s = lines[j]
                ss = s.strip()
                if not ss:
                    break
                if LIST_ITEM.match(ss) or ss.startswith(("  ", "\t")):
                    buf.append(s)
                    j += 1
                else:
                    break
            blocks.append({"type": "list", "content": "\n".join(buf)})
            i = j
            continue
        # 普通段落：收集直到空行或新块
        j = i
        buf = []
        while j < n:
            s = lines[j]
            ss = s.strip()
            if not ss:
                break
            if FENCE.match(ss) or HEADING.match(ss) or ss.startswith(MATH_OPEN) \
               or IMAGE.match(ss) or TABLE_START.match(ss) or LIST_ITEM.match(ss):
                break
            buf.append(s)
            j += 1
        blocks.append({"type": "paragraph", "content": "\n".join(buf)})
        i = j
    return blocks


def pair_blocks(en_blocks: list[dict], zh_blocks: list[dict]) -> tuple[list[tuple[dict, dict]] | None, list[str]]:
    """按序配对英文/中文块，校验数量与类型一致。返回 (pairs, errors)。"""
    errors: list[str] = []
    if len(en_blocks) != len(zh_blocks):
        return None, [f"块数量不一致：英文 {len(en_blocks)} vs 中文 {len(zh_blocks)}，请检查翻译是否逐段对应"]
    pairs: list[tuple[dict, dict]] = []
    for idx, (en, zh) in enumerate(zip(en_blocks, zh_blocks)):
        if en["type"] != zh["type"]:
            errors.append(f"块#{idx} 类型不一致：英文={en['type']} vs 中文={zh['type']}（内容：{en['content'][:40]!r} / {zh['content'][:40]!r}）")
        pairs.append((en, zh))
    if errors:
        return None, errors
    return pairs, []
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_make_bilingual.py -v`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add scripts/make_bilingual.py tests/test_make_bilingual.py
git commit -m "feat: make_bilingual.py 块切分与配对（核心）"
```

---

### Task 10: make_bilingual.py 渲染 — templates/bilingual.tex + blocks_to_paracol + xelatex

**Files:**
- Create: `templates/bilingual.tex`
- Modify: `scripts/make_bilingual.py`（追加渲染部分）
- Test: `tests/test_make_bilingual.py`（追加）

- [ ] **Step 1: 写失败测试（追加）**

```python
def test_blocks_to_paracol_has_left_right():
    en = mb.split_blocks(_read("sample_en.md"))
    zh = mb.split_blocks(_read("sample_zh.md"))
    pairs, errors = mb.pair_blocks(en, zh)
    assert errors == []
    tex = mb.blocks_to_paracol(pairs)
    assert "\\begin{leftcolumn}" in tex
    assert "\\begin{rightcolumn}" in tex
    assert "leftcolumn*" in tex  # 跨栏标题

def test_blocks_to_paracol_math_kept():
    en = mb.split_blocks("$$\nE = m c ^ { 2 } \\tag{1}\n$$\n")
    zh = mb.split_blocks("$$\nE = m c ^ { 2 } \\tag{1}\n$$\n")
    pairs, _ = mb.pair_blocks(en, zh)
    tex = mb.blocks_to_paracol(pairs)
    assert "E = m c" in tex
    assert "\\tag{1}" in tex
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_make_bilingual.py -v`
Expected: 新增 2 个 FAIL（`AttributeError: blocks_to_paracol`）

- [ ] **Step 3: 创建模板 bilingual.tex**

`templates/bilingual.tex`：
```latex
% PaperTranslate 对开双栏对照 PDF 模板
% 两个 A4 竖版横向拼接：左栏英文全文、右栏中文全文，段落对齐（paracol）
% 由 make_bilingual.py 填充 %%TITLE%%、%%AUTHORS%%、%%BODY%%
\documentclass[11pt]{ctexart}
% 页面 = 两个 A4 竖版（210mm x 2）+ 边距
\usepackage[paperwidth=420mm,paperheight=297mm,margin=16mm]{geometry}
\usepackage{paracol}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{hyperref}
\hypersetup{hidelinks}
\setlength{\columnsep}{24pt}
\pagestyle{plain}
\title{%%TITLE%%}
\author{%%AUTHORS%%}
\date{}
\begin{document}
\maketitle
\begin{paracol}{2}
%%BODY%%
\end{paracol}
\end{document}
```

- [ ] **Step 4: 实现渲染部分（追加到 make_bilingual.py）**

```python
MD_TO_LATEX_CACHE: dict[str, str] = {}


def md_to_latex(md_text: str) -> str:
    """用 pandoc 把单个 md 块转 LaTeX 片段（带缓存）。"""
    if md_text in MD_TO_LATEX_CACHE:
        return MD_TO_LATEX_CACHE[md_text]
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "latex", "--no-highlight", "-"],
        input=md_text, capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"pandoc 块转换失败：{result.stderr}")
    MD_TO_LATEX_CACHE[md_text] = result.stdout.strip()
    return MD_TO_LATEX_CACHE[md_text]


def _math_latex(content: str) -> str:
    """公式块 → equation 环境，保留 \\tag 编号（有 \\tag 用 equation，否则 equation*）。"""
    inner = content.replace("$$", "").strip()
    inner = inner.strip("$")
    has_tag = "\\tag" in inner
    env = "equation" if has_tag else "equation*"
    return f"\\begin{{{env}}}\n{inner}\n\\end{{{env}}}"


def _image_latex(content: str, resource_dir: Path) -> str:
    """图片块 → includegraphics（宽度撑满栏宽）。"""
    m = re.search(r"!\[[^\]]*\]\(([^)]+)\)", content)
    path = m.group(1) if m else "missing"
    return f"\\includegraphics[width=\\linewidth]{{{path}}}"


def blocks_to_paracol(pairs: list[tuple[dict, dict]], resource_dir: Path | None = None) -> str:
    """生成 paracol 左右栏片段。heading 用跨栏；其余块左右成对。"""
    out: list[str] = []
    for en, zh in pairs:
        t = en["type"]
        if t == "heading":
            level = en.get("level", 1)
            cmd = {1: "\\section", 2: "\\subsection", 3: "\\subsubsection"}.get(level, "\\subsubsection")
            zh_title = re.sub(r"^#{1,6}\s+", "", zh["content"])
            # 跨栏章节标题：leftcolumn* + rightcolumn*（同步对齐）
            out.append(f"\\begin{{leftcolumn*}}\n{cmd}{{{zh_title}}}\n\\end{{leftcolumn*}}\n")
        elif t == "math":
            out.append(_math_latex(en["content"]))
        elif t == "image":
            en_img = _image_latex(en["content"], resource_dir) if resource_dir else _image_latex(en["content"], Path("."))
            zh_img = _image_latex(zh["content"], resource_dir) if resource_dir else _image_latex(zh["content"], Path("."))
            # 左右栏各放图片（英文原图/中文同图），栏内流式
            out.append("\\begin{leftcolumn}\n" + en_img + "\n\\end{leftcolumn}\n"
                       "\\begin{rightcolumn}\n" + zh_img + "\n\\end{rightcolumn}\n")
        else:
            en_latex = md_to_latex(en["content"])
            zh_latex = md_to_latex(zh["content"])
            out.append("\\begin{leftcolumn}\n" + en_latex + "\n\\end{leftcolumn}\n"
                       "\\begin{rightcolumn}\n" + zh_latex + "\n\\end{rightcolumn}\n")
    return "\n".join(out)


def render_bilingual_pdf(en_md: Path, zh_md: Path, resource_dir: Path, output_pdf: Path, template_dir: Path) -> Path:
    """生成对开双栏对照 PDF，返回输出路径。"""
    en_blocks = split_blocks(en_md.read_text(encoding="utf-8"))
    zh_blocks = split_blocks(zh_md.read_text(encoding="utf-8"))
    pairs, errors = pair_blocks(en_blocks, zh_blocks)
    if pairs is None:
        raise ValueError("块配对失败：\n" + "\n".join(errors))

    body = blocks_to_paracol(pairs, resource_dir)
    md_text = en_md.read_text(encoding="utf-8")
    title, authors = _extract_meta(md_text)
    template = (Path(template_dir) / "bilingual.tex").read_text(encoding="utf-8")
    tex = (template
           .replace("%%TITLE%%", title)
           .replace("%%AUTHORS%%", authors)
           .replace("%%BODY%%", body))

    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    tex_path = output_pdf.with_suffix(".tex")
    tex_path.write_text(tex, encoding="utf-8")
    # 复制 images 到 tex 同目录（paracol 相对路径解析）
    if resource_dir and (resource_dir / "images").exists():
        import shutil
        dst_images = tex_path.parent / "images"
        shutil.copytree(resource_dir / "images", dst_images, dirs_exist_ok=True)

    for _ in range(2):
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={output_pdf.parent}", str(tex_path.name)],
            cwd=tex_path.parent, capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"xelatex 编译失败：\n{result.stdout[-2500:]}")
    if not output_pdf.exists():
        raise FileNotFoundError(f"未生成 PDF：{output_pdf}")
    return output_pdf


def _extract_meta(md_text: str) -> tuple[str, str]:
    """从英文 md 提取标题与作者（与 make_single 相似，复用逻辑）。"""
    title = "Untitled"
    authors = ""
    for line in md_text.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m and title == "Untitled":
            title = m.group(1).strip()
            continue
        if line.strip() and "<sup>" in line and not line.startswith("#") and not authors:
            authors = line.strip()
    return title, authors
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest tests/test_make_bilingual.py -v`
Expected: 6 passed

- [ ] **Step 6: 真实渲染冒烟（需 pandoc + xelatex）**

Run:
```bash
cd E:\LLMproject\Cordis\PaperTranslate
python -m scripts.make_bilingual tests/sample/sample_en.md tests/sample/sample_zh.md --resource-dir tests/sample --output tests/sample/out/bilingual.pdf
```
Expected: 生成 `tests/sample/out/bilingual.pdf`，两栏对开、段落对齐、公式渲染

- [ ] **Step 7: 提交**

```bash
git add templates/bilingual.tex scripts/make_bilingual.py tests/test_make_bilingual.py
git commit -m "feat: 对开双栏对照 PDF（paracol + xelatex）"
```

---

### Task 11: run.py 统一入口（--outputs 编排）

**Files:**
- Create: `scripts/run.py`
- Test: `tests/test_run.py`

- [ ] **Step 1: 写失败测试**

`tests/test_run.py`：
```python
from pathlib import Path
import pytest
import scripts.run as r

SAMPLE = Path(__file__).parent / "sample"
OUTPUTS_ALL = ["zh_md", "bilingual_pdf", "single_pdf", "bilingual_md"]

def test_parse_outputs():
    assert r.parse_outputs("zh_md,single_pdf") == ["zh_md", "single_pdf"]
    assert r.parse_outputs("") == ["zh_md", "bilingual_pdf", "single_pdf"]  # 默认集
    with pytest.raises(ValueError):
        r.parse_outputs("zh_md,unknown")

def test_resolve_source(tmp_path):
    # 目录模式：找到 full.md
    src = tmp_path / "src"
    src.mkdir()
    (src / "full.md").write_text("# t\n", encoding="utf-8")
    assert r.resolve_source(src) == src / "full.md"
    # 文件模式
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    assert r.resolve_source(pdf) == pdf
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_run.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 run.py**

`scripts/run.py`：
```python
"""PaperTranslate 统一入口：输入准备 + 按 --outputs 生成输出。

用法：
  python -m scripts.run --source <pdf 或含 full.md 的目录> --outputs zh_md,bilingual_pdf
  python -m scripts.run --source <dir> --outputs single_pdf --zh-md <full_zh.md>
"""
import argparse
import shutil
from pathlib import Path

from . import make_bilingual, make_bilingual_md, make_single, mineru_convert

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"
DEFAULT_OUTPUTS = ["zh_md", "bilingual_pdf", "single_pdf"]
KNOWN_OUTPUTS = {"zh_md", "bilingual_pdf", "single_pdf", "bilingual_md"}


def parse_outputs(raw: str) -> list[str]:
    """解析 --outputs；空则默认集。"""
    if not raw.strip():
        return list(DEFAULT_OUTPUTS)
    outputs = [o.strip() for o in raw.split(",") if o.strip()]
    unknown = [o for o in outputs if o not in KNOWN_OUTPUTS]
    if unknown:
        raise ValueError(f"未知输出：{unknown}，可选 {sorted(KNOWN_OUTPUTS)}")
    return outputs


def resolve_source(source: str | Path) -> Path:
    """目录 → 找 full.md；文件 → 原样返回。"""
    src = Path(source)
    if src.is_dir():
        full_md = mineru_convert.find_local_full_md(src)
        if not full_md:
            raise FileNotFoundError(f"目录 {src} 中未找到 full.md（本地 MinerU 产物）")
        return full_md
    return src


def run(source: str | Path, outputs: list[str], out_dir: Path, zh_md: Path | None) -> dict:
    """执行主流程，返回 {输出名: 路径}。"""
    src = resolve_source(source)
    src = Path(src)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    resource_dir = src.parent  # images/ 相对 full.md 目录

    # 输入准备：PDF → 调 MinerU；md 文件 → 本地产物（含翻译前的 full.md）
    if src.suffix.lower() == ".pdf":
        full_md = mineru_convert.convert_pdf(src, src.parent)
        resource_dir = full_md.parent
    else:
        full_md = src

    # 翻译产物定位
    if zh_md:
        zh_md_path = Path(zh_md)
    else:
        zh_md_path = resource_dir / "full_zh.md"
        if not zh_md_path.exists():
            raise FileNotFoundError(
                f"未找到翻译产物 {zh_md_path}。请先按 SKILL.md 流程将 {full_md.name} 翻译为 full_zh.md。"
            )

    results: dict[str, Path] = {}
    if "zh_md" in outputs:
        dst = out_dir / "full_zh.md"
        shutil.copy2(zh_md_path, dst)
        results["zh_md"] = dst
    if "bilingual_pdf" in outputs:
        pdf = out_dir / "full_bilingual.pdf"
        make_bilingual.render_bilingual_pdf(full_md, zh_md_path, resource_dir, pdf, TEMPLATES_DIR)
        results["bilingual_pdf"] = pdf
    if "single_pdf" in outputs:
        pdf = out_dir / "full_zh.pdf"
        make_single.render_single_pdf(zh_md_path, resource_dir, pdf, TEMPLATES_DIR)
        results["single_pdf"] = pdf
    if "bilingual_md" in outputs:
        md = out_dir / "full_bilingual.md"
        make_bilingual_md.make_bilingual_md(full_md, zh_md_path, md)
        results["bilingual_md"] = md
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="PaperTranslate 统一入口")
    parser.add_argument("--source", required=True, help="PDF 路径或含 full.md 的目录")
    parser.add_argument("--outputs", default="", help="逗号分隔：zh_md,bilingual_pdf,single_pdf,bilingual_md（默认前三个）")
    parser.add_argument("--out-dir", default="out", help="输出目录（默认 ./out）")
    parser.add_argument("--zh-md", default=None, help="指定翻译产物路径（默认 <源目录>/full_zh.md）")
    args = parser.parse_args()

    outputs = parse_outputs(args.outputs)
    results = run(args.source, outputs, Path(args.out_dir), args.zh_md)
    print("=== 生成完成 ===")
    for name, path in results.items():
        print(f"  [{name}] {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_run.py -v`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add scripts/run.py tests/test_run.py
git commit -m "feat: run.py 统一入口（--outputs 编排）"
```

---

### Task 12: SKILL.md 方法论

**Files:**
- Create: `SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

`SKILL.md`（frontmatter + 5 阶段方法论，翻译规则与术语表约定）：
```markdown
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
```

- [ ] **Step 2: 提交**

```bash
git add SKILL.md
git commit -m "docs: SKILL.md 方法论（5 阶段工作流、术语表、校验分层）"
```

---

### Task 13: 端到端验收（父目录真实论文）

**Files:**
- 无新文件（验证 + 修复）

- [ ] **Step 1: 用真实论文生成中文版（agent 逐段翻译全篇）**

说明：真实论文 2242 行，由执行者按 SKILL.md §翻译 逐段翻译为 `full_zh.md`（本次实现中翻译为验收步骤；可在执行时委托子代理分批完成，保留公式/图片/乱码修复/术语统一）。产物放在父目录论文目录下。

- [ ] **Step 2: 生成四态输出**

Run:
```bash
cd E:\LLMproject\Cordis\PaperTranslate
python -m scripts.run --source "E:\LLMproject\Cordis\paper.pdf-bd13ec9e-de16-402b-b201-7b06202e44e5" --outputs zh_md,bilingual_pdf,single_pdf,bilingual_md --out-dir out
```
Expected: 四态输出生成成功

- [ ] **Step 3: validate 验收**

Run:
```bash
python -m scripts.validate "E:\LLMproject\Cordis\paper.pdf-bd13ec9e-de16-402b-b201-7b06202e44e5\full.md" "E:\LLMproject\Cordis\paper.pdf-bd13ec9e-de16-402b-b201-7b06202e44e5\full_zh.md" --image-dir "E:\LLMproject\Cordis\paper.pdf-bd13ec9e-de16-402b-b201-7b06202e44e5"
```
Expected: FAIL 0 项；WARN 项人工复核

- [ ] **Step 4: 人工验收 PDF 质量**

- 对开双栏：抽查 3-5 处段落对齐、公式渲染、图表各归各语言
- 单栏：编译零错误、公式编号正确、图片显示

- [ ] **Step 5: 修复并提交最终产物清单**

若发现问题，回到对应 Task 修复脚本后：
```bash
git add -A && git commit -m "test: 真实论文端到端验收"
```

---

## Self-Review

**1. Spec coverage 检查：**
- §3 仓库结构 → Task 1-12 逐项覆盖（run.py 在 Task 11）
- §4 数据流 → Task 6（输入）、Task 12（翻译）、Task 7/8/9/10（输出）、Task 3/4（校验）
- §5.1 对开双栏（段落对齐、图表各归各语言、`\tag` 保留）→ Task 9/10
- §5.2 中文单栏 → Task 7
- §5.3 对照版 md → Task 8
- §6 四态参数化、默认集 → Task 11
- §7 validate 三态分层 → Task 3/4
- §8 错误处理 → 各脚本 raise + run.py 透传
- §9 v1 范围 → Task 1-13；v2（并发 + review agent）不在本次范围，SKILL.md §工作流已预留结构
- §10 测试策略 → Task 13 端到端 + 各脚本 TDD

**2. Placeholder scan：** 所有步骤含完整代码或明确命令；SKILL.md 为方法论文档，结构完整。无 TBD/TODO。

**3. Type consistency：**
- `split_blocks`/`pair_blocks`/`blocks_to_paracol`/`render_bilingual_pdf` 签名在 Task 9/10 一致
- `run_validation(en_md, zh_md, image_dir, term_map)` 在 Task 4 定义与使用一致
- `render_single_pdf(zh_md, resource_dir, output_pdf, template_dir)` 在 Task 7 一致
- `resolve_source`/`parse_outputs` 在 Task 11 一致

## 执行注意事项（实施时逐条遵守）

### 环境与工具
1. **中文路径**：Windows 下 pandoc/xelatex 对含中文的绝对路径/输出目录兼容性差。所有中间产物与 PDF 输出放 **ASCII 路径**（默认 `out/`）；若某步失败先怀疑路径编码，改用纯 ASCII 目录重跑。
2. **工具链**：pandoc、xelatex 必须在 PATH；TeX Live 2025 已装；中文字体 SimSun/SimHei（ctex 自动配置）。`pip install -r requirements.txt`（requests、python-dotenv、pytest）。
3. **MinerU API**：真实调用需 `config/.env` 中的真实 `MINERU_API_TOKEN`。若未配置，端到端用**本地 MinerU 产物目录**（父目录已含 `full.md` + `images/`）验收——不阻塞实现。
4. **环境依赖测试标记**：依赖 pandoc/xelatex 的集成测试用 `pytest.mark.skipif(shutil.which(...) is None)` 标记，但**本机必须真实跑通，禁止跳过**（本机工具齐全）。

### 安全与目录边界（用户全局规则，违反即失败）
5. **禁止泄露 token**：绝不打印/提交/写入 `config/.env` 内容；`.gitignore` 已忽略 `config/.env`，提交前用 `git status` 确认其未入库。
6. **禁止批量删除**：不使用 rm -rf / del /s 等；清理仅单文件且先确认。
7. **目录边界**：写入只允许在 `E:\LLMproject\Cordis\PaperTranslate\` 内。父目录论文目录（`paper.pdf-bd13ec9e-...\`）**只读**：允许新增 `full_zh.md` 一个翻译产物文件，**不得修改/删除其中任何现有内容**（full.md、images/、json 均不动）。
8. **不擅改配置**：不改 `.gitignore`、`pytest.ini`、`requirements.txt` 之外无关文件；LICENSE/MIT 固定。

### 脚本与 LaTeX 细节
9. **paracol 对开页**：页面 420×297mm 横向超宽（两 A4 竖版拼接），阅读横向滚动或双屏对开；如需标准 A4 竖版属 v2 调整，V1 不做。
10. **xelatex 编译**：每份 PDF 跑 2 遍；失败时读日志尾部 2000-2500 字符定位出错公式，先清洗公式再重编，仍失败则报告具体行号（不绕过）。
11. **split_blocks 边界**：列表/段落/表格歧义最多，务必覆盖测试：连续 `$$` 公式、嵌套缩进列表、表格后紧跟段落、标题下紧邻段落、`$$` 与同行文字。
12. **validate 边界**：SKIP 层（OCR 错字还原、公式丢符号推断、术语选词、逻辑与引用）由 agent 在执行时人工兜底，脚本不做；FAIL 项任何一条非零即判失败，**不得放行**。
13. **图片路径**：md 中图片引用为 `images/xxx.jpg` 相对路径；渲染时按资源目录解析（pandoc `--resource-path` / tex 同目录 `images/` 复制），保证 PDF 图片正常。

### 执行纪律（superpowers 流程）
14. **严格 TDD**：每任务先写失败测试→运行确认失败→最小实现→运行确认通过→提交。禁止"先实现后补测"。
15. **每任务一个 commit**：commit message 用 plan 各任务 Step 中给定的原文；Task 1 前确认 git 已初始化（master 分支）。
16. **任务依赖**：顺序执行（2→3/4→5→6→7→8→9→10→11→12，13 最后），不可跳序；任一任务失败必须修复后再继续。
17. **中途汇报**：每完成一个任务向主会话报告 `pytest` 结果与 commit 哈希；Task 13 验收按下方标准逐项给出 PASS/FAIL 与证据。

## 验收标准（严格，逐项自查）

### A. 代码与测试质量
- [ ] `python -m pytest -q` 全绿（本机真实执行，无环境缺失导致的 skip）
- [ ] 每脚本有 `argparse` 入口 + `if __name__ == "__main__"`，CLI 与 README/plan 一致
- [ ] 无硬编码绝对路径（模板目录、样例路径用相对 `Path(__file__)` 解析）
- [ ] 关键逻辑有中文注释、命名清晰、风格统一
- [ ] validate 单测覆盖全部 FAIL 信号与关键 WARN 信号（未闭合 $$、奇数内联 $、`\$` 转义豁免、标签错配、乱码、图片缺失/译文多出）

### B. 样例冒烟（tests/sample/）
- [ ] `make_single` 样例生成 PDF：文件存在、>1KB、编译零错误
- [ ] `make_bilingual` 样例生成 PDF：两栏、段落对齐、公式 `\tag{1}` 渲染
- [ ] `make_bilingual_md` 样例：含左右两列表格、中英均出现
- [ ] `validate` 样例：FAIL 0 项（结构一致、无乱码）
- [ ] `mineru_convert` mock 单测：上传 body/header、轮询 done、zip 解压全断言通过
- [ ] `run.py` 对样例 `--outputs zh_md,bilingual_pdf,single_pdf,bilingual_md` 一次生成 4 个文件

### C. 端到端验收（父目录真实论文）
- [ ] 四态输出全部生成于 `out/`
- [ ] `validate`（源 full.md vs full_zh.md，image-dir 指向论文目录）：**FAIL 0 项**；WARN 每项给出复核结论（术语映射/未翻译长句逐条判定）
- [ ] **乱码清零**：full_zh.md 无 U+FFFD（源 1140 处已按上下文修复）
- [ ] **公式编号 1:1**：抽查 ≥5 个公式，左右 `\tag{n}` 与英文原版一致、符号结构未改
- [ ] **图片一致性**：5 张引用图源==译==磁盘，PDF 内均显示
- [ ] **参考文献**：124 条 `[n]` 保留英文原文，`[n]` 编号贯穿正文一致
- [ ] **结构完整**：标题层级、代码块、HTML 表格数英中一致（对照源 84 公式/11 代码块/2 表格）

### D. PDF 渲染质量
- [ ] 对开双栏 PDF：页面尺寸 ≈420×297mm 横向对开
- [ ] 章节标题跨栏（`leftcolumn*`）生效，无左右重复
- [ ] 抽查 ≥5 处左右段落同一视觉高度对齐（跨页处同步）
- [ ] 抽查 ≥3 个公式左右渲染正确、编号对应
- [ ] 图片/图注各归各语言栏内流式，不跨栏混用
- [ ] 表格左右各自排版
- [ ] 单栏 PDF：编译零错误、公式编号正确、图片显示、中文渲染正常（SimSun）
- [ ] 两个 PDF 可打开、体积合理（非空、无 0 字节）

### E. 交付物
- [ ] README 的 CLI 示例与 `run.py --help` 一致
- [ ] SKILL.md 覆盖：输入双路径、5 阶段工作流、术语表约定、三态校验分层
- [ ] `config/.env` 未被 git 跟踪（`.gitignore` 生效），`git status` 干净
- [ ] LICENSE(MIT)、.gitignore、requirements.txt 就位
- [ ] git log 干净：13+ 个任务 commit，message 与 plan 一致
