from pathlib import Path
import pytest
import scripts.run as r

SAMPLE = Path(__file__).parent / "sample"
OUTPUTS_ALL = ["zh_md", "bilingual_pdf", "single_pdf", "bilingual_md"]

def test_parse_outputs():
    assert r.parse_outputs("zh_md,single_pdf") == ["zh_md", "single_pdf"]
    assert r.parse_outputs("") == ["zh_md", "bilingual_pdf", "single_pdf"]  # 默认集
    with pytest.raises(ValueError):
        r.parse_outputs("zh_md,unknown")

def test_resolve_source(tmp_path):
    # 目录模式：找到 full.md
    src = tmp_path / "src"
    src.mkdir()
    (src / "full.md").write_text("# t\n", encoding="utf-8")
    assert r.resolve_source(src) == src / "full.md"
    # 文件模式
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    assert r.resolve_source(pdf) == pdf
