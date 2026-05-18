# Gallery · 用户 / 学科自补的真实风格参考

> 与 `../templates/` 的关系：
> - **templates** 是**抽象骨架** — 不绑学科 / 主题，用于生成 A 版模板可编辑 SVG；
> - **custom_gallery** 是**真实例子** — 由用户 / 实验室 / 学科共同体上传，按学科 / archetype 分桶存放，方便日后复用为风格 anchor。

本目录默认存放一些顶刊优秀技术路线图，需要时由你自己往里放。

## 推荐目录结构

```
gallery/
├── geography/                # 学科分桶
│   ├── thinking-quad/        # archetype × sub_variant 二级
│   │   ├── ref_001.png
│   │   ├── ref_002.png
│   │   └── manifest.json     # DOI / 标题 / 期刊
│   └── workflow-pipeline/
├── medicine/
├── computer-science/
└── ...
```

## 怎么用

1. 你 / 实验室在阅读文献时，遇到好的技术路线图 / 研究框架图 → 截图保存到对应 `<discipline>/<archetype>-<sub_variant>/` 下；
2. 保存时新建 / 追加 `manifest.json`：

```json
[
  {
    "ref_id": "geo_quad_001",
    "title": "...",
    "doi": "10....",
    "journal": "...",
    "year": 2024,
    "authors": "...",
    "note": "这一例的 bottom_anchor 用了红色 + 问号，非常适合答辩"
  }
]
```

3. 生图时 `literature_search.py offline --hints templates/technicalroute/Custom_gallery/<discipline>/<archetype>-<sub_variant>/` 会把这些图作为 B 版 AI参考生成图的结构 / 风格参考。

## 不要做的事

- ❌ 把没有引用元信息的图丢进来（必须有 DOI / 期刊 / 年份至少其一）；
- ❌ 把版权受保护图当作"风格参考"以外的用途使用；
- ❌ 在 manifest.json 里写出处的中文标题 + 英文标题混淆（一种语言一栏即可）；
- ❌ 上传训练好的 ML 模型 / 数据 / 数据集（这里只放**图片缩略**）。

## 学术伦理

复用其他论文的 figure 仅作"视觉风格 anchor"，最终生成图**不直接复用其文字 / 节点 / 公式**。最终图嵌入 paper2ppt 时，**不需要**引用这些参考图（因为只是风格参考，不是内容引用）。若你希望额外致谢风格参考来源，可在 PPT 末页"图来源"栏列出。


## Discipline Index

Before selecting any Custom_gallery reference, read `gallery_index.json`. The index maps each discipline to raster-only references, aliases, archetype/sub-variant hints, and source manifests. AI Version B may use these files only as style/structure anchors; SVG, PPTX, and the editable Version A route page are forbidden as AI references.
