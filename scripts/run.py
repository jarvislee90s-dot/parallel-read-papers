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
