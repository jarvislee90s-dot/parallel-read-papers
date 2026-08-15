"""生成左英右中的对照版 md（两列表格，段落对齐）。"""
import re
from pathlib import Path

from .make_bilingual import html_table_to_pipe, strip_toc_section

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
    en_text = strip_toc_section(en_md.read_text(encoding="utf-8"))
    zh_text = strip_toc_section(zh_md.read_text(encoding="utf-8"))
    en_blocks = _split_paragraphs(en_text)
    zh_blocks = _split_paragraphs(zh_text)
    if len(en_blocks) != len(zh_blocks):
        raise ValueError(f"段落数不一致：英文 {len(en_blocks)} vs 中文 {len(zh_blocks)}")

    lines = ["<!-- 中英对照版：左英文、右中文，逐段对齐 -->", ""]
    for en, zh in zip(en_blocks, zh_blocks):
        # 标题块：中英合并输出（不做表格）
        if re.match(r"^#{1,6}\s", en) and re.match(r"^#{1,6}\s", zh):
            level = re.match(r"^#{1,6}", zh).group(0)
            en_title = re.sub(r"^#{1,6}\s+", "", en).strip()
            zh_title = re.sub(r"^#{1,6}\s+", "", zh).strip()
            # 若中文标题已含英文（如「摘要（Abstract）」「时空可组合性（Spatiotemporal
            # Composability）的编程范式」），则不再重复拼英文，避免重复。判断分两层：
            # ① 英文标题（去编号）规范化后整串已在中文标题中（如「Effects」∈「效应（Effects）」）；
            # ② 中文标题内嵌的英文核心词已在英文标题中（如 zh「…（Spatiotemporal
            #    Composability）…」的英文核心词 ⊆ en「A Programming Paradigm for …」）。
            en_title_stripped = re.sub(r"^\d+(\.\d+)*\.?\s*", "", en_title).strip()
            # 归一化后比较：忽略大小写/空白，且把源文的 OCR 拼写 efect 视同 effect，
            # 否则「效应（Effects）（2.1. Efects）」会因拼写差异重复拼英文
            def norm_heading(s: str) -> str:
                return re.sub(r"\s+", "", s).lower().replace("efect", "effect")
            zh_latin = re.sub(r"[^\x20-\x7e]", "", zh_title)
            zh_latin_norm = norm_heading(zh_latin)
            if en_title_stripped and (
                norm_heading(en_title_stripped) in norm_heading(zh_title)
                or (zh_latin_norm and zh_latin_norm in norm_heading(en_title_stripped))
            ):
                merged_title = zh_title
            else:
                merged_title = f"{zh_title}（{en_title}）"
            lines.append(f"{level} {merged_title}")
            lines.append("")
            continue
        # 公式块：居中显示
        if en.startswith("$$") or zh.startswith("$$"):
            lines.append(en)
            lines.append("")
            lines.append(zh)
            lines.append("")
            continue
        # 表格块：源 pipe table（| 开头）或 HTML <table> 原样输出为独立表格，
        # 英文表 + 中文表（markdown 无法嵌套表格做左右对照，故上下排列；
        # HTML 表先转 pipe table，避免被拍平）
        if en.lstrip().startswith("|") or zh.lstrip().startswith("|") \
                or en.lstrip().lower().startswith("<table") or zh.lstrip().lower().startswith("<table"):
            def _norm_table(blk: str) -> str:
                if re.search(r"<table", blk, re.I):
                    return re.sub(
                        r"<table>.*?</table>",
                        lambda m: html_table_to_pipe(m.group(0)),
                        blk,
                        flags=re.S | re.I,
                    )
                return blk
            lines.append("**英文表**")
            lines.append("")
            lines.append(_norm_table(en))
            lines.append("")
            lines.append("**中文表**")
            lines.append("")
            lines.append(_norm_table(zh))
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
