# Seed URLs for CN_Spark_workflow

以下为 workflow 可用于检索和参考的学术搜索站点与期刊库（agent优先访问）：

- https://www.sciencedirect.com/
- https://scholar.google.com/
- https://www.cnki.net/

使用说明：
- 若在调用 `run_workflow_extract_svg(..., seed_urls=None)` 时未显式传入 `seed_urls`，
  workflow 会尝试从此文件读取默认的 seed URLs 列表用于后续的爬取/检索（若环境允许网络访问）。
- 请注意：爬取这些站点可能需要遵守其服务条款，且某些站点（如 CNKI、ScienceDirect）对爬虫/自动访问有限制或需要付费访问。
