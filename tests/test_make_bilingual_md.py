from pathlib import Path
import scripts.make_bilingual_md as bmd

SAMPLE = Path(__file__).parent / "sample"

def test_make_bilingual_md(tmp_path):
    en = SAMPLE / "sample_en.md"
    zh = SAMPLE / "sample_zh.md"
    out = tmp_path / "bilingual.md"
    bmd.make_bilingual_md(en, zh, out)
    text = out.read_text(encoding="utf-8")
    assert "样例论文标题" in text
    assert "Sample Paper Title" in text
    assert "|" in text  # 表格结构
