# PaperTranslate

把英文论文 PDF 翻译为中文，并生成多形态输出（纯中文 md、对开双栏中英对照 PDF、中文单栏还原 PDF、对照版 md）。

## 依赖
- Python 3.10+（`pip install -r requirements.txt`）
- pandoc
- TeX Live（xelatex，含 ctex 宏包）
- 中文字体（Windows：SimSun/SimHei）

## 配置
复制 `config/.env.example` 为 `config/.env`，填入 `MINERU_API_TOKEN`（https://mineru.net/apiManage/token）。

## 使用（V1）
1. 解析：`python scripts/run.py --source <paper.pdf> --outputs zh_md`（或用本地 MinerU 产物目录）
2. 翻译：在 SKILL.md 流程指导下，agent 将 `full.md` 翻译为 `full_zh.md`
3. 生成：`python scripts/run.py --source <dir> --outputs bilingual_pdf,single_pdf`
