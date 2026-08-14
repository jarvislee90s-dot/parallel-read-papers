from pathlib import Path
import scripts.copy_images as ci

SAMPLE = Path(__file__).parent / "sample"

def test_copy_referenced_images(tmp_path):
    en_md = SAMPLE / "sample_en.md"
    src_dir = SAMPLE  # 包含 images/sample.jpg
    out_dir = tmp_path / "out"
    copied, missing = ci.copy_referenced_images(en_md, src_dir, out_dir)
    target = out_dir / "images" / "sample.jpg"
    assert missing == []  # 无缺失
    assert target.exists()
    assert target in copied

def test_missing_image_reported(tmp_path):
    en_md = SAMPLE / "sample_en.md"
    src_dir = tmp_path / "empty"  # 无 images
    src_dir.mkdir()
    copied, missing = ci.copy_referenced_images(en_md, src_dir, tmp_path / "out")
    assert copied == []
    assert "images/sample.jpg" in missing  # 返回缺失列表（完整相对引用路径）
