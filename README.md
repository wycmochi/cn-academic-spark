# CN-Academic-PPT-Skills

面向中文学术汇报场景的可复用 skill 集合，核心目标是提升**学术内容的理解、组织与表达**，而不只是机械生成幻灯片。

当前仓库包含两个子 skill：
- `CN_Spark_paper2ppt`：把论文、开题、课程报告、文献综述等材料生成成一整套中文学术 `.pptx`
- `CN_Spark_workflow`：生成可编辑的技术路线图、研究框架图、概念框架图、思维导图、网络图、时间演化图等

本仓库适合：
- 论文答辩 / journal club / 组会汇报
- 开题报告 / 课程报告 / 文献综述讲解
- 需要把“学术内容”转化为“结构化、可讲清楚的 PPT 与图示”的场景

---

## Download

`CN-Academic-PPT-Skills` 本质上是一个由多个 `SKILL.md`、参考文档和脚本组成的可复用 skill 仓库。每一个二级文件夹CN_Spark_* 目录都构成一个可安装的单元。具体的安装方法取决于您使用的编程环境。


### 1. Clone

在终端使用git命令克隆仓库。

```bash
git clone https://github.com/wycmochi/CN-Academic-PPT-Skills.git
cd CN-Academic-PPT-Skills
```

### 2. Install for Codex

如果你希望把整个仓库作为本地 skill 使用，可以直接复制到 Codex skill 目录：

```bash
mkdir -p ~/.codex/skills
cp -R CN-Academic-PPT-Skills ~/.codex/skills/
```

如果你只想单独安装两个子 skill，也可以分别复制：

```bash
mkdir -p ~/.codex/skills
cp -R CN_Spark_paper2ppt ~/.codex/skills/
cp -R CN_Spark_workflow ~/.codex/skills/
```

完成后建议重启或重新打开 Codex 会话，让新 skill 被重新扫描。  
之后你就可以自然地提出请求，例如：

```text
帮我把这篇论文做成中文答辩 PPT。
请根据这段研究设计画一个技术路线图。
```

### 3. Install for Claude

这里给用户两种方式，二选一即可。

#### 方式 A：在 Claude 的 Customize 里导入这个仓库

这个仓库根目录已经包含 Claude 识别所需的元数据：
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

具体操作步骤：

1. 在Customize-Connectors-GitHub Integration授权连接
2. 打开 Claude 的 skill 市场 / 插件市场
3. 搜索：

```text
cn-academic-ppt-skills
```

如果没搜到，再搜索这些关键词：

```text
paper2ppt
academic ppt
workflow diagram
chinese academic
```

4. 安装或启用后，就可以在 Claude 里直接把它当成学术 PPT / 学术图示 skill 使用


#### 方式 B：直接在 Claude 里作为本地 command 使用

Claude Code 目前无法将 Codex 风格的 SKILL.md 文件夹加载为原生技能。其最接近的可复用基础组件包括：

- 子代理：~/.claude/agents/ 或 .claude/agents/
- 自定义命令：~/.claude/commands/ 或 .claude/commands/

推荐子代理模式使用。

**做法 1：作为本地 agent 使用**

```bash
mkdir -p ~/.claude/agents
cp CN_Spark_paper2ppt/SKILL.md ~/.claude/agents/cn-spark-paper2ppt.md
cp CN_Spark_workflow/SKILL.md ~/.claude/agents/cn-spark-workflow.md
```

然后在 Claude 里可以直接说：

```text
Use cn-spark-paper2ppt to turn this paper into a Chinese academic presentation.
```

或者：

```text
Use cn-spark-workflow to create a conceptual framework diagram for this literature review.
```

**做法 2：作为本地 command / prompt 使用**

如果你更喜欢命令式触发，也可以把对应 `SKILL.md` 内容整理进 Claude 的 command 目录或项目级 prompt 目录。

#### 用最通俗的话告诉用户

如果用户问“我怎么在 Claude 里找到这个 skill”，你可以直接回答：

**选法 1：市场里找**
- 先把这个仓库接入 Claude 的 skill/plugin 来源
- 在市场里搜 `cn-academic-ppt-skills`
- 或搜 `paper2ppt`、`academic ppt`
- 看到描述里写“Chinese academic PPT”或“workflow / diagram generation”的就是它

**选法 2：本地直接用**
- 不走市场也可以
- 把 `CN_Spark_paper2ppt/SKILL.md` 和 `CN_Spark_workflow/SKILL.md` 放进 Claude 可读的本地 agents / commands 目录
- 然后在 Claude 里直接点名调用

#### 给普通用户的一句解释

这个仓库不是“装完就只会生成一页图”的工具，而是一个面向中文学术汇报的 skill 包：
- 一个负责整套 PPT
- 一个负责技术路线图、研究框架图、综述概念图

所以无论是在 Claude 市场里装，还是在本地 agent 里用，最终用户都应该把它理解成：

```text
一个专门帮我做中文学术 PPT 和学术图示的 Claude skill 包
```

### 4. Other agents or manual use

如果你使用的不是 Codex 或 Claude，而是其他支持 reusable prompts、agent profiles、prompt library、project instructions 的工具，这个仓库通常也可以直接复用。

最小可迁移单元是整个 skill 目录本身。只要你的工具支持“读取一份主提示词 + 若干参考文档 + 若干脚本说明”，这个仓库就能直接迁移过去。

推荐保留的最小结构是：

```text
CN_Spark_paper2ppt/
├── SKILL.md
├── references/
└── scripts/

CN_Spark_workflow/
├── SKILL.md
├── references/
└── scripts/
```

如果你的 agent 支持自定义 prompt / profile，可以按下面思路接入：

1. 把整个子 skill 目录复制到你的 agent 项目或提示词库中；
2. 保留 `SKILL.md` 与 `references/` 的相对结构，不要只拷贝一份主文件；
3. 如果目标 agent 需要自己的 frontmatter、JSON manifest 或 YAML agent 定义，再在外层包一层适配文件即可；
4. 只有在真正需要脚本执行时，再把 `scripts/` 一并挂载给对应运行环境。

如果你只是想手工参考，也完全可以把它当成一份“中文学术 PPT 设计规范 + 学术图示规范”来使用：
- 读 `CN_Spark_paper2ppt/SKILL.md` 和 `references/`，按 route 组织你的汇报；
- 读 `CN_Spark_workflow/SKILL.md` 和 `references/diagram-templates.md`，按图示拓扑整理技术路线与综述框架。

---

## Skill Index

| Skill | Status | Purpose | Typical triggers |
|---|---|---|---|
| `CN_Spark_paper2ppt` | Active | 生成完整中文学术 PPTX，包括路线分流、版式、引文页脚、演讲词与公式页组织 | `论文PPT` `答辩PPT` `开题PPT` `课程汇报` `文献综述PPT` |
| `CN_Spark_workflow` | Active | 生成可编辑学术图示，包括技术路线、研究框架、概念框架、思维导图、网络图、时间轴 | `技术路线图` `研究框架图` `概念图` `思维导图` `综述框架图` |

---

## Skill Overview

## `CN_Spark_paper2ppt`

这个 skill 面向“完整汇报”的生成。

它处理的不是单张图，而是一整套中文学术 `.pptx`。核心特性包括：
- 支持学术论文、课程报告、开题报告、文献综述四条 route
- 强调“论证主轴优先”，不是照搬原文目录
- 生成可编辑的 PPT 结构，而不是只输出 markdown 提纲
- 支持页脚 GB/T 7714 引文
- 支持 speaker notes
- 支持公式页的结构化表达

公式页规则已经内置为：
- 默认优先“模块化步骤公式页”
- 需要大量流程说明时再切换为“标题分段公式页”

适合：
- journal club
- 学位答辩
- 组会汇报
- 开题答辩
- 文献综述讲解

## `CN_Spark_workflow`

这个 skill 面向“单页学术图示”的生成。

它负责把研究流程、框架关系和综述结构转成可编辑图形，而不是截图式位图。当前支持：
- `pipeline`
- `matrix_framework`
- `mind_map`
- `network`
- `timeline`

典型用途：
- 技术路线页
- 研究框架页
- 文献综述概念框架页
- 主题争议关系图
- 方法演化时间轴

仓库中已经补齐了这些函数的可直接调用入口，包括：
- `make_mind_map_slide`
- `make_network_slide`
- `make_timeline_slide`
- `make_conceptual_framework_slide`
- `add_citation_footer`

---

## Repository Structure

```text
CN-Academic-PPT-Skills/
├── SKILL.md
├── README.md
├── GIT_UPLOAD_WORKFLOW.md
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── CN_Spark_paper2ppt/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
└── CN_Spark_workflow/
    ├── SKILL.md
    ├── references/
    └── scripts/
```

---

## Notes

- 本仓库强调“学术表达质量”，不是只追求自动化生成。
- 公式、图示、框架、引文、speaker notes 都围绕“让学术内容更容易被理解和讲述”来设计。
- 字体、主题色、版心等默认样式保留在脚本中作为 default，可根据用户需求替换。

---

## Acknowledgement

感谢 **Yuan1z0825** 开源的 `nature-skills` 项目。

本仓库在设计时参考了 `nature-skills` 中 `paper2ppt` 相关部分的思路，并在此基础上结合中文学术汇报场景，进行了进一步的：
- 路由细化
- 学术图示补充
- 公式页结构化表达补充
- 引文页脚与概念框架接口补充
- 中文答辩 / 课程汇报 / 开题 / 综述等场景化强化

站在巨人的肩膀上，目标不是简单复制，而是在原有启发上，继续把中文学术 PPT 的理解、组织和表达做得更细、更稳、更可复用。
