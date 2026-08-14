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
