import shutil
from pathlib import Path
import pytest
import scripts.make_single as ms

SAMPLE = Path(__file__).parent / "sample"

@pytest.mark.skipif(shutil.which("pandoc") is None or shutil.which("xelatex") is None,
                    reason="需要 pandoc 与 xelatex")
def test_render_single_pdf(tmp_path):
    zh_md = SAMPLE / "sample_zh.md"
    out_pdf = tmp_path / "out.pdf"
    result = ms.render_single_pdf(zh_md, SAMPLE, out_pdf, Path(__file__).parent.parent / "templates")
    assert result.exists()
    assert result.stat().st_size > 1000  # 非空 PDF

def test_tex_body_generated(tmp_path):
    """不依赖 xelatex 的纯逻辑测试：pandoc body 应包含标题 section、公式内容与编号。"""
    zh_md = SAMPLE / "sample_zh.md"
    tex = ms.zh_md_to_tex(zh_md, SAMPLE)
    assert "\\section" in tex  # 标题 → section
    assert "E = m c" in tex  # 公式内容保留
    assert "\\tag{1}" in tex  # 公式编号保留
