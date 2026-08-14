from pathlib import Path
import scripts.validate as v

SAMPLE_DIR = Path(__file__).parent / "sample"

def test_display_math_closed():
    ok = "para\n$$\na + b\n$$\nend\n"
    bad = "para\n$$\na + b  # 未闭合\nend\n"
    assert v.check_display_math(ok) == []
    assert len(v.check_display_math(bad)) >= 1

def test_inline_math_closed():
    assert v.check_inline_math("text $x$ and $y$") == []
    assert len(v.check_inline_math("text $x and $y$")) >= 1  # 奇数个 $（未闭合）
    assert v.check_inline_math("cost is \\$5 and $x$") == []  # \$ 转义不算

def test_html_tags_paired():
    assert v.check_html_tags("a<sup>1</sup>b") == []
    assert len(v.check_html_tags("a<sup>1</sup>b<sup>2</sup>c<sup>3")) >= 1  # 未闭合（3 开 2 闭）
    assert v.check_html_tags("a<sup>1</sup>b<sup>2</sup>") == []

def test_unicode_replacement():
    assert v.check_unicode_replacement("clean text") == []
    assert len(v.check_unicode_replacement("bad � char")) >= 1

def test_extract_image_refs():
    md = "![a](images/x.jpg)\n![b](images/y.png)\n"
    assert v.extract_image_refs(md) == {"images/x.jpg", "images/y.png"}

def test_check_images_consistency():
    en = "![f](images/sample.jpg)\n"
    zh = "![f](images/sample.jpg)\n"
    img_dir = SAMPLE_DIR  # image_dir 为 md 基础目录（含 images/），与 CLI --image-dir 语义一致
    assert v.check_images(en, zh, img_dir) == []  # sample.jpg 存在
    # 译文缺图 → 报错
    assert len(v.check_images("![f](images/sample.jpg)\n", "no image\n", img_dir)) >= 1
    # 引用不存在的图 → 报错
    assert len(v.check_images("![f](images/none.jpg)\n", "![f](images/none.jpg)\n", img_dir)) >= 1
