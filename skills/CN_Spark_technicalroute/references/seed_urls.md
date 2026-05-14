# Seed URLs · 学术文献样式检索站点说明

> 由 `literature_search.py` 自动读取 [seed_sites.json](seed_sites.json) 调用。本文件用文字解释每个站点的特点 / 局限 / 何时切到 fallback。

## 优先级与适配场景

| Site | 适合的内容 | 不适合的场景 |
|---|---|---|
| **Google Scholar** | 所有学科的英文与部分中文文献。优先 — 检索能力最强，PDF 直链多 | 受墙 / 验证码概率高 |
| **Semantic Scholar API** | 计算机 / 信息 / 部分医学。返回 JSON，最适合自动化 | 中文文献覆盖弱 |
| **ScienceDirect** | Elsevier 期刊，地理 / 城市 / 环境 / 医学最强 | 全文需订阅；figure 缩略一般可见 |
| **CNKI** | 中文学位论文 / 中文期刊 | 访问需登录，自动化困难，**只作人工补充** |
| **arXiv** | 计算 / 机器学习 / 物理 / 量化金融的工作流图 | 文科少 |
| **Wikimedia Commons** | CC 授权图片，可直接下载 | 学术 figure 偏少，主要是科普图 |
| **ResearchGate** | 跨学科作者主页 | 需登录，优先级低 |
| **Baidu Scholar** | 中文文献补充 | 检索质量不如 Google Scholar |

## 实际抓取流程

1. **首选** — IDE 提供 `WebSearch` + `WebFetch`（Claude Code / Cursor / VS Code Copilot）：
   - `literature_search.py` 组装搜索 URL；
   - 主代理用 `WebSearch` 取前 10 条结果，过滤标题与摘要含 `technical route` / `research framework` / `技术路线` / `研究框架` 的论文；
   - 对每篇 paper 调 `WebFetch` 拿到 abstract + figure URLs；
   - 下载 figure 缩略到 `style_refs/`。

2. **降级** — 没有 IDE web 工具：
   - 输出搜索 URL 列表给用户；
   - 请用户挑 5–8 张图保存到 `projects/<project_name>/style_refs/`；
   - 用户保存后回到 SKILL.md Step 3。

3. **完全离线** — 用户上传 ≥ 3 张参考图：
   - `literature_search.py --offline --hints <folder>` 直接把用户图作为参考；
   - 跳过 Step 2，进入 Step 3。

## 图片过滤启发式

`literature_search.py` 抓到 figure 后按下述启发式过滤：

- **关键词命中**：title / caption / surrounding text 含 "technical route / research framework / pipeline / workflow / 技术路线 / 研究框架 / 研究设计" 加 +1；
- **关键词排除**：含 "regression / histogram / scatter / heatmap / boxplot / ROC / loss curve" 减 -1（结果图不是框架图）；
- **宽高比**：1.2 ≤ aspect ≤ 3.0；
- **像素**：宽 ≥ 800 px；
- 按得分排序取前 N（默认 8）。

## 学术伦理

- 仅作**视觉风格参考**，**不**复用文字与数值；
- 在 `style_refs/manifest.json` 保留 DOI / 期刊 / 标题 / 作者；
- 最终图在 paper2ppt 嵌入时**不需要**引用这些参考论文（只是风格参考）；
- 若用户希望致谢，可在 PPT 末页"图来源"栏列出。
