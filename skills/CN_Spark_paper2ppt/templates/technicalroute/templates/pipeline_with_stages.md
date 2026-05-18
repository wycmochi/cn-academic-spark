# pipeline_with_stages

`pipeline_with_stages.svg` 是全文技术路线的默认可编辑模板。

使用顺序：
1. 先读 `templates_index.json`，确认 `workflow` / `horizontal-pipeline` 优先指向 `pipeline_with_stages`。
2. 再读 `pipeline_with_stages.slot_map.json`，把其中 `slot_map` 写入项目 `spec_lock.md` 的 `## slot_map`。
3. 按下面 schema 写 `content.yaml`，运行 `generate_route_image.py assemble --template-key pipeline_with_stages`。

## content.yaml 最小结构

```yaml
title: 全文技术路线
subtitle: 问题提出 -> 指标与数据 -> 模型解释 -> 结果验证 -> 规划启示
subtitle_detail: 每一阶段均来自论文正文，不引入参考图语义
flow_summary: 研究流程：原始数据 -> 指标构建 -> 模型估计 -> 结果检验 -> 规划启示
bottom_summary: 起点：研究问题与数据 —— 五阶段处理 —— 终点：规划建议
origin_label: 起点：研究问题与数据
destination_label: 终点：规划建议
stages:
  - title: 问题提出
    role: 研究缺口与核心问题
    steps:
      - {title: 研究背景, desc: 提炼现实冲击与恢复议题}
      - {title: 文献不足, desc: 归纳现有研究缺口}
      - {title: 核心问题, desc: 明确本文切入点}
    output: 问题链条
  - title: 指标与数据
    role: 指标定义与变量构建
    steps:
      - {title: 数据来源, desc: 说明样本与时间范围}
      - {title: 指标构建, desc: 提取恢复力核心指标}
      - {title: 变量控制, desc: 整理建成环境因素}
    output: 分析数据集
  - title: 模型解释
    role: 模型估计与机制识别
    steps:
      - {title: 模型设定, desc: 对应论文主模型}
      - {title: 机制检验, desc: 解释变量作用路径}
      - {title: 稳健性, desc: 验证结果可靠性}
    output: 模型结果
  - title: 结果验证
    role: 结果归纳与异质性比较
    steps:
      - {title: 总体发现, desc: 汇总核心结论}
      - {title: 分组比较, desc: 呈现场景差异}
      - {title: 敏感性分析, desc: 识别关键因素}
    output: 证据链条
  - title: 规划启示
    role: 管理含义与政策建议
    steps:
      - {title: 站点治理, desc: 对应微观干预}
      - {title: 片区协同, desc: 对应土地与交通协调}
      - {title: 长期韧性, desc: 对应恢复能力建设}
    output: 规划建议
```

## 文本约束

- 每个图形模块中的文本必须放在可换行文本框内。
- 文本框与背景图形边界保持 5pt 内距。
- 如果文本高度不足，先缩小字号，再压缩相邻图形之间的垂直/水平间距；不允许文字溢出文本框。
