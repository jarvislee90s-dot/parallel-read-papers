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
