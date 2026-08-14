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
    count = md.count("�")
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
