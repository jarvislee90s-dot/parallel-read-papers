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
    """$$ 块级配对：移除成对 $$...$$ 后不应残留 $$ 分片（行内 $...$ 不算）。"""
    reduced = re.sub(r"\$\$.*?\$\$", "", md, flags=re.S)
    if "$$" in reduced:
        pos = reduced.index("$$")
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
    parser.add_argument("--image-dir", required=True, help="images 所在基础目录（md 相对引用基准）")
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
