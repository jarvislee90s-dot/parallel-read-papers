"""MinerU API 解析：PDF → full.md + images/（API 模式参考 extract-report/pdf_to_md.py）。"""
import os
import re
import time
import zipfile
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# config/ 目录位于 skill 根（scripts/ 的上一级）
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

UPLOAD_API = "https://mineru.net/api/v4/file-urls/batch"
RESULT_API = "https://mineru.net/api/v4/extract-results/batch/{batch_id}"


def _load_env() -> None:
    env_file = CONFIG_DIR / ".env"
    if env_file.exists():
        if load_dotenv:
            load_dotenv(env_file)
        else:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())


def get_token() -> str:
    """从 config/.env 读取 MinerU token。"""
    _load_env()
    token = os.getenv("MINERU_API_TOKEN", "").strip()
    if not token:
        raise ValueError("未找到 MINERU_API_TOKEN，请在 config/.env 中配置（参考 config/.env.example）")
    return token


def upload_file(file_path: Path, token: str) -> str:
    """上传 PDF 到 MinerU，返回 batch_id。"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在：{file_path}")
    header = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        UPLOAD_API,
        headers=header,
        json={"files": [{"name": file_path.name}], "is_ocr": True, "enable_table": True},
        timeout=60,
    )
    resp.raise_for_status()
    info = resp.json()
    if info.get("code") != 0:
        raise ValueError(f"上传链接申请失败：{info.get('msg')}")
    upload_url = info["data"]["file_urls"][0]
    batch_id = info["data"]["batch_id"]
    with open(file_path, "rb") as f:
        resp = requests.put(upload_url, data=f.read(), timeout=300)
    resp.raise_for_status()
    return batch_id


def poll_result(batch_id: str, token: str, timeout: int = 600, interval: int = 5) -> dict:
    """轮询任务状态直到 done/failed，返回文件结果 dict。"""
    header = {"Authorization": f"Bearer {token}"}
    url = RESULT_API.format(batch_id=batch_id)
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        resp = requests.get(url, headers=header, timeout=60)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        extract = data.get("extract_result") or []
        if not extract:
            continue
        file_result = extract[0]
        state = file_result.get("state")
        if state == "done":
            return file_result
        if state == "failed":
            raise RuntimeError(f"MinerU 解析失败：{file_result.get('err_msg')}")
    raise TimeoutError(f"MinerU 任务超时（>{timeout}s）")


def download_result(zip_url: str, out_dir: Path) -> Path:
    """下载并解压 MinerU 结果到 out_dir，返回 full.md 路径。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    resp = requests.get(zip_url, timeout=300)
    resp.raise_for_status()
    zip_path = out_dir / "_result.zip"
    zip_path.write_bytes(resp.content)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(out_dir)
    zip_path.unlink()
    # 找 full.md（MinerU zip 内通常根目录或一级子目录）
    for cand in (out_dir / "full.md", *sorted(out_dir.glob("*/full.md"))):
        if cand.exists():
            return cand
    raise FileNotFoundError(f"未在 {out_dir} 中找到 full.md")


def convert_pdf(pdf_path: str | Path, out_dir: str | Path) -> Path:
    """完整转换：上传 → 轮询 → 下载解压 → 返回 full.md 路径。"""
    token = get_token()
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    batch_id = upload_file(pdf_path, token)
    file_result = poll_result(batch_id, token)
    full_md = download_result(file_result["full_zip_url"], out_dir)
    print(f"解析完成：{full_md}")
    return full_md


def find_local_full_md(source_dir: str | Path) -> Path | None:
    """在目录中查找已存在的 full.md（本地 MinerU 产物）。"""
    src = Path(source_dir)
    for cand in (src / "full.md", *sorted(src.glob("*/full.md"))):
        if cand.exists():
            return cand
    return None


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="MinerU API 解析 PDF 或查找本地 full.md")
    parser.add_argument("source", help="PDF 路径或含 full.md 的目录")
    parser.add_argument("--out-dir", default=None, help="解析结果输出目录")
    args = parser.parse_args()
    src = Path(args.source)
    if src.is_dir():
        full_md = find_local_full_md(src)
        if not full_md:
            print(f"未在 {src} 找到 full.md")
            return 1
        print(f"找到本地 full.md：{full_md}")
        return 0
    out_dir = Path(args.out_dir) if args.out_dir else src.parent
    convert_pdf(src, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
