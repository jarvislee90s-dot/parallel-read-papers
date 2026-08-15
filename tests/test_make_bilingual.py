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

def test_strip_toc_section():
    md = """# Title

## Abstract
abstract text

## Contents
1. Introduction ...... 1
2. Preliminaries ...... 5

## 1. Introduction
body here
"""
    out = mb.strip_toc_section(md)
    assert "## Contents" not in out
    assert "Introduction ...... 1" not in out
    assert "## Abstract" in out
    assert "## 1. Introduction" in out


def test_strip_toc_section_zh_toc():
    md = "# 标题\n\n## 目录\n1. 引言 ...... 1\n\n## 1. 引言（Introduction）\n正文\n"
    out = mb.strip_toc_section(md)
    assert "## 目录" not in out
    assert "引言 ...... 1" not in out
    assert "## 1. 引言（Introduction）" in out


def test_pair_blocks_list_paragraph_compat():
    en = mb.split_blocks("para one\n\n- item a\n- item b\n")
    zh = mb.split_blocks("para one\n\nitem a, item b（翻译成段落）\n")
    pairs, errors = mb.pair_blocks(en, zh)
    assert errors == []
