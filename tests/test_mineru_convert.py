import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import scripts.mineru_convert as mc

def test_upload_file_calls_batch_api(tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    with patch("scripts.mineru_convert.requests") as mock_req:
        mock_req.post.return_value.json.return_value = {
            "code": 0,
            "data": {"batch_id": "b1", "file_urls": ["https://oss/upload"]},
        }
        batch_id = mc.upload_file(pdf, "token")
        assert batch_id == "b1"
        # 断言请求带 token 与文件信息
        post_kwargs = mock_req.post.call_args
        assert post_kwargs.kwargs["headers"]["Authorization"] == "Bearer token"
        assert post_kwargs.kwargs["json"]["files"] == [{"name": "paper.pdf"}]
        # PUT 上传到 OSS
        mock_req.put.assert_called_once()
        assert mock_req.put.call_args.kwargs["data"] == b"%PDF-1.4 fake"

def test_get_token_reads_env(tmp_path, monkeypatch):
    # .env 位于 config/ 目录
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ".env").write_text("MINERU_API_TOKEN=abc123\n")
    monkeypatch.setattr(mc, "CONFIG_DIR", config_dir)
    monkeypatch.delenv("MINERU_API_TOKEN", raising=False)  # 隔离环境变量
    assert mc.get_token() == "abc123"

def test_get_token_missing_raises(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ".env").write_text("MINERU_API_TOKEN=\n")
    monkeypatch.setattr(mc, "CONFIG_DIR", config_dir)
    monkeypatch.delenv("MINERU_API_TOKEN", raising=False)  # 隔离环境变量
    try:
        mc.get_token()
        assert False, "应抛出 ValueError"
    except ValueError:
        pass

def test_poll_and_download_done(tmp_path):
    # 模拟轮询一次成功（poll_result 消费第 1 个 get）+ zip 下载解压（download_result 消费第 2 个 get）
    out_dir = tmp_path / "out"
    zip_bytes = _make_zip({"full.md": "# title\n", "images/": None})
    with patch("scripts.mineru_convert.requests") as mock_req:
        mock_req.get.side_effect = [
            MagicMock(json=lambda: {"data": {"extract_result": [
                {"state": "done", "full_zip_url": "https://zip", "err_msg": ""}]}}),
            MagicMock(content=zip_bytes),
        ]
        file_result = mc.poll_result("b1", "token", timeout=1, interval=0)
        assert file_result["state"] == "done"
        full_md = mc.download_result(file_result["full_zip_url"], out_dir)
        assert full_md == out_dir / "full.md"
        assert (out_dir / "full.md").exists()

def _make_zip(files: dict) -> bytes:
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in files.items():
            if content is None:
                continue
            z.writestr(name, content)
    return buf.getvalue()
