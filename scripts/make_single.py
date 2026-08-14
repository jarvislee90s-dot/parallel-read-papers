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
    # 作者行 HTML 上标/下标转 LaTeX 命令（避免 <sup> 作为非法 LaTeX 进 \author{}）
    authors = re.sub(r"<sup>(.*?)</sup>", r"\\textsuperscript{\1}", authors)
    authors = re.sub(r"<sub>(.*?)</sub>", r"\\textsubscript{\1}", authors)
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
    # 复制 images 到 tex 同目录（xelatex 相对路径解析）
    if resource_dir and (resource_dir / "images").exists():
        import shutil
        dst_images = tex_path.parent / "images"
        shutil.copytree(resource_dir / "images", dst_images, dirs_exist_ok=True)

    # xelatex 编译（两次跑目录交叉引用；output-directory 用绝对路径避免相对路径叠加）
    for _ in range(2):
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={output_pdf.parent.resolve()}", str(tex_path.name)],
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
