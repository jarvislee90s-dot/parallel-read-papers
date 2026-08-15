"""对开双栏对照 PDF：英/中 md 块切分配对 → paracol LaTeX → lualatex。

注：用 lualatex 而非 xelatex。xelatex 对正文混排的裸 Unicode 数学符号
（尤其 CJK 文本中的 ∘/∂/Γ 等）会触发 "bad native font flag in
map_char_to_glyph" 内部崩溃，lualatex 无此问题且对中文（ctex + fontspec）
渲染一致。
"""
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


def strip_toc_section(md_text: str) -> str:
    """剔除 Contents/目录 标题段：英文论文的 Table of Contents 目录,译文通常省略。

    若两侧都保留或都省略,双语对照的块配对才会逐块对齐。目录段 = Contents 标题
    与其后直到下一个标题之间的行(目录条目多为列表/短行)。
    """
    lines = md_text.split("\n")
    out: list[str] = []
    in_toc = False
    for line in lines:
        stripped = line.strip()
        if not in_toc and re.match(r"^#{1,6}\s+(?:contents|目录)\s*$", stripped, re.I):
            in_toc = True
            continue
        if in_toc:
            if re.match(r"^#{1,6}\s", stripped):
                in_toc = False
            else:
                continue
        out.append(line)
    return "\n".join(out)


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
        # 显示公式（可跨行，累计 $$ 计数直到闭合）
        if stripped == MATH_OPEN or stripped.startswith(MATH_OPEN):
            j = i
            buf = []
            dollars = 0
            while j < n:
                buf.append(lines[j])
                dollars += lines[j].count("$$")
                j += 1
                if dollars % 2 == 0:  # 已闭合
                    break
            blocks.append({"type": "math", "content": "\n".join(buf)})
            i = j
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
    """按序配对英文/中文块,校验数量与类型一致。

    list↔paragraph 视为同构可互配(翻译时常把列表翻成段落或反之)。
    返回 (pairs, errors)。
    """
    errors: list[str] = []
    if len(en_blocks) != len(zh_blocks):
        return None, [f"块数量不一致：英文 {len(en_blocks)} vs 中文 {len(zh_blocks)}，请检查翻译是否逐段对应"]
    pairs: list[tuple[dict, dict]] = []
    for idx, (en, zh) in enumerate(zip(en_blocks, zh_blocks)):
        if en["type"] != zh["type"] and (en["type"], zh["type"]) not in {("list", "paragraph"), ("paragraph", "list")}:
            errors.append(f"块#{idx} 类型不一致：英文={en['type']} vs 中文={zh['type']}（内容：{en['content'][:40]!r} / {zh['content'][:40]!r}）")
        pairs.append((en, zh))
    if errors:
        return None, errors
    return pairs, []


MD_TO_LATEX_CACHE: dict[str, str] = {}


def _longtable_to_tabular(latex: str) -> str:
    """把 pandoc 输出的 longtable（含 LTcaptype 包装）转为 tabular。

    longtable 只能在单栏模式使用，放入 paracol 双栏会报
    "longtable not in 1-column mode"，故表块统一转 tabular。
    """
    # 开头包装 {\def\LTcaptype{none} ... \begin{longtable}[...]
    latex = re.sub(
        r"\{\\def\\LTcaptype\{none\}.*?\\begin\{longtable\}(\[[^\]]*\])?",
        r"\\begin{tabular}", latex, flags=re.S)
    # 结尾 \end{longtable}\n}
    latex = re.sub(r"\\end\{longtable\}[ \t]*\n?\s*\}", r"\\end{tabular}", latex)
    latex = re.sub(r"\\end\{longtable\}", r"\\end{tabular}", latex)
    # 清理 longtable 专有命令
    latex = re.sub(r"\\noalign\{\}", "", latex)
    for cmd in ("endhead", "endlastfoot", "endfirsthead", "endfoot"):
        latex = re.sub(rf"\\{cmd}", "", latex)
    return latex


def _fix_table_widths(latex: str) -> str:
    """修复 pandoc pipe table 列宽：p{(\\linewidth - N\\tabcolsep) * \\real{f}}。

    pandoc 用 LaTeX3 real 算术（\\real{...}），普通 LaTeX 的 p{} 不接受
    带括号的 dim 表达式（\\dimexpr 求值会被括号破坏为 0，导致表格列重叠）。
    改为 e-TeX 的 \\dimexpr{f}\\linewidth - {f*N}\\tabcolsep\\relax。
    与 make_single 的修复保持一致。
    """
    return re.sub(
        r"p\{\(\\linewidth - (\d+)\\tabcolsep\) \* \\real\{([0-9.]+)\}\}",
        lambda m: (
            f"p{{\\dimexpr{float(m.group(2)):.4f}\\linewidth "
            f"- {float(m.group(2)) * int(m.group(1)):.4f}\\tabcolsep\\relax}}"
        ),
        latex,
    )


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
    out = result.stdout.strip()
    out = _longtable_to_tabular(out)
    out = _fix_table_widths(out)
    MD_TO_LATEX_CACHE[md_text] = out
    return MD_TO_LATEX_CACHE[md_text]


def _math_latex(content: str) -> str:
    """公式块 → equation 环境，保留 \tag 编号（有 \tag 用 equation，否则 equation*）。"""
    inner = content.replace("$$", "").strip()
    inner = inner.strip("$")
    has_tag = "\tag" in inner
    env = "equation" if has_tag else "equation*"
    return f"\\begin{{{env}}}\n{inner}\n\\end{{{env}}}"


def _image_latex(content: str, resource_dir: Path) -> str:
    """图片块 → \\includegraphics（宽度撑满栏宽）。"""
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
            # 用 * 版标题命令：中文标题本身已含编号（如「1. 引言」），避免双编号
            cmd = {1: "\\section*", 2: "\\subsection*", 3: "\\subsubsection*"}.get(level, "\\subsubsection*")
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
    en_text = strip_toc_section(en_md.read_text(encoding="utf-8"))
    zh_text = strip_toc_section(zh_md.read_text(encoding="utf-8"))
    en_blocks = split_blocks(en_text)
    zh_blocks = split_blocks(zh_text)
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
            ["lualatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={output_pdf.parent.resolve()}", str(tex_path.name)],
            cwd=tex_path.parent, capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"lualatex 编译失败：\n{result.stdout[-2500:]}")
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
    # 作者行 HTML 上标/下标转 LaTeX 命令（避免 <sup> 作为非法 LaTeX 进 \author{}）
    # 注意：re.sub 替换串中 \t 会被解释为制表符，必须用 \\ 转义保留反斜杠
    authors = re.sub(r"<sup>(.*?)</sup>", r"\\textsuperscript{\1}", authors)
    authors = re.sub(r"<sub>(.*?)</sub>", r"\\textsubscript{\1}", authors)
    return title, authors


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="生成对开双栏对照 PDF")
    parser.add_argument("en_md", help="英文 md 路径")
    parser.add_argument("zh_md", help="中文 md 路径")
    parser.add_argument("--resource-dir", required=True, help="images 所在基础目录（相对引用基准）")
    parser.add_argument("--output", required=True, help="输出 PDF 路径")
    parser.add_argument("--template-dir", default=None, help="模板目录（默认 skill 内 templates/）")
    args = parser.parse_args()
    template_dir = Path(args.template_dir) if args.template_dir else Path(__file__).resolve().parent.parent / "templates"
    render_bilingual_pdf(Path(args.en_md), Path(args.zh_md), Path(args.resource_dir), Path(args.output), template_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
