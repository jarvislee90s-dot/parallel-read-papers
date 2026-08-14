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
        # 标题块：中英合并输出（不做表格）
        if re.match(r"^#{1,6}\s", en) and re.match(r"^#{1,6}\s", zh):
            level = re.match(r"^#{1,6}", zh).group(0)
            en_title = re.sub(r"^#{1,6}\s+", "", en).strip()
            zh_title = re.sub(r"^#{1,6}\s+", "", zh).strip()
            lines.append(f"{level} {zh_title}（{en_title}）")
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
