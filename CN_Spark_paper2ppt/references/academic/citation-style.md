# Citation Style · 引文规范（四条路线通用）

> ⚠️ **主路径 = SVG**。引文页脚的实际写入由 SVG `<text>` + `<tspan>` 完成，混合字体分 tspan。详见 [executor-academic.md §2.2 引文页脚](executor-academic.md#22-引文页脚-citation_footer) 与 §2.3 tspan 分段规则。
>
> 本文件主要规定**条目格式（GB/T 7714）**与**引文密度**，对 SVG / python-pptx 两种写入路径通用。§III 以下的 python-pptx 代码仅在 `svg_to_pptx` 链路不可用时作 fallback 参考。

只要 PPT 正文中出现了他人的观点 / 数据 / 图表 / 模型，都必须满足三件事：

1. **正文角标**：在引用句末加 `[n]`，n 与该页页脚或参考文献页中的条目编号一一对应。
2. **页脚完整条目**：用 8pt 浅灰列出该页用到的完整 GB/T 7714 引用，置于 `bottom_banner` 上方。
3. **混合字体**：中文字符用 *微软雅黑*；数字、年份、卷期、页码、英文字母、DOI、URL 一律用 *Times New Roman*。

中文文献用中文，英文文献保留英文原文，**不要互译**。

---

## 默认格式 · GB/T 7714（顺序编码制）

PPT 答辩 / 课程报告 / 综述讲解默认使用 GB/T 7714—2015 的顺序编码格式。引文条目按**正文中首次出现的顺序**编号，与正文角标 `[n]` 对应。

### 各类型条目模板（直接复制可用）

**中文期刊论文**：
```
[1] 董文鸳. 我国谷歌学术搜索研究综述[J]. 新世纪图书馆, 2011, 9: 43-45.
```
结构：`[序号] 作者. 题目[J]. 期刊名, 出版年, 卷(期): 起止页码.`

**英文期刊论文**：
```
[2] Smith J, Doe A, Wang L. Title of the paper here[J]. Nature, 2024, 612(7940): 215-223.
```
结构：`[序号] 作者. 题目[J]. 期刊名, 年, 卷(期): 起止页码.`
作者多于 3 人：列前 3 + `等` / `et al.`。

**中文会议论文**：
```
[3] 张三, 李四. 文章标题[C]//会议名称. 出版地: 出版社, 2020: 12-18.
```

**英文会议论文**：
```
[4] Brown K, Lee M. Paper title[C]//Proceedings of NeurIPS 2023. Vancouver: NeurIPS Foundation, 2023: 4521-4533.
```

**中文专著**：
```
[5] 李四. 学术写作规范[M]. 北京: 高等教育出版社, 2019.
```

**英文专著**：
```
[6] Murphy K P. Probabilistic Machine Learning: An Introduction[M]. Cambridge: MIT Press, 2022.
```

**学位论文**：
```
[7] 王五. 论文题目[D]. 北京: 清华大学, 2023.
```

**政策文件 / 标准 / 报告**（Route B 常用）：
```
[8] 国务院办公厅. 关于推动 XXX 发展的指导意见: 国办发〔2024〕12 号[Z]. 2024-05-12.
[9] 国家统计局. 2024 年国民经济和社会发展统计公报[R]. 北京: 国家统计局, 2025.
```

**报纸文章**：
```
[10] 记者张某. 文章标题[N]. 人民日报, 2024-08-15(02).
```

**电子资源 / 网页**：
```
[11] 国家统计局. 第七次全国人口普查公报[EB/OL]. (2021-05-11)[2025-05-01]. https://www.stats.gov.cn/...
```
结构：`[序号] 作者. 题目[EB/OL]. (发布日期)[引用日期]. URL.`

**预印本**：
```
[12] Lee A, Chen B. Paper title[EB/OL]. (2024-09-10)[2025-04-20]. arXiv:2409.05678.
```

---

## 文献类型标识符速查

| 标识 | 含义 |
|---|---|
| `[J]` | 期刊文章 |
| `[C]` | 会议论文 |
| `[M]` | 专著 |
| `[D]` | 学位论文 |
| `[R]` | 报告 |
| `[Z]` | 政策 / 标准 / 法规 |
| `[N]` | 报纸文章 |
| `[EB/OL]` | 电子资源 / 网页 |
| `[DS/OL]` | 在线数据集 |
| `[CP/OL]` | 在线软件 / 代码 |

---

## 备选格式 · APA / MLA（用户明确要求时）

**APA 第 7 版**：
```
董文鸳. (2011). 我国谷歌学术搜索研究综述. 新世纪图书馆, 9, 43-45.
Smith, J., Doe, A., & Wang, L. (2024). Title of the paper. Nature, 612(7940), 215-223.
```
正文角标改为 `(董, 2011)` / `(Smith et al., 2024)`，不用方括号数字。

**MLA 第 9 版**：
```
董文鸳. "我国谷歌学术搜索研究综述." 新世纪图书馆, vol. 9, 2011, pp. 43-45.
Smith, John, et al. "Title of the Paper." Nature, vol. 612, no. 7940, 2024, pp. 215-223.
```
正文角标改为 `(董 43)` / `(Smith et al. 215)`，作者 + 页码。

切换格式时同时改：①正文角标形式 ②页脚 / 参考文献页条目 ③ Step 3 询问环节的勾选记录。

---

## python-pptx 实现要点（fallback only）

> 仅在 `svg_to_pptx.py` 链路不可用、必须直接调 python-pptx 写 PPTX 时使用。主路径请走 SVG `<tspan>`。

### 1 · 引文页脚的位置

每页页脚区在 `bottom_banner` **上方**留出固定带状区域（高约 1.5–2.0 cm），从左到右铺满除 logo 外的宽度。如该页没有底部横幅（甘特图、参考文献页），则页脚紧贴页面底部 0.5 cm。

参数（在 `LAYOUT` 中）：
- `cite_h = 1.6` （cm，页脚带高度）
- `cite_top_offset = layout["slide_h"] - layout["banner_h"] - cite_h` （从顶向下定位）
- `cite_left = layout["margin_left"]`
- `cite_w = layout["slide_w"] - layout["margin_left"] - layout["margin_right"]`

### 2 · 中英文混排的多 run 写法

python-pptx 的 `run.font.name` 只对该 run 生效，所以**必须把中文段、英文/数字段拆成多个 run**，每个 run 单独设字体。简化伪代码：

```python
def add_citation_run(paragraph, text, is_chinese, size_pt=8, color_hex='888888'):
    run = paragraph.add_run()
    run.text = text
    run.font.name = '微软雅黑' if is_chinese else 'Times New Roman'
    run.font.size = Pt(size_pt)
    run.font.color.rgb = rgb(color_hex)

def write_citation_line(paragraph, citation_text):
    # 用正则切分：连续的中文字符为一段，连续的非中文为一段
    import re
    parts = re.findall(r'[一-鿿]+|[^一-鿿]+', citation_text)
    for part in parts:
        is_zh = bool(re.match(r'[一-鿿]', part))
        add_citation_run(paragraph, part, is_zh)
```

调用时一行一条引用：

```python
tf = footer_box.text_frame
tf.word_wrap = True
for i, cite in enumerate(citations_for_this_slide):
    p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
    p.space_before = Pt(1)
    write_citation_line(p, cite)
```

### 3 · 正文角标 `[n]` 的样式

正文里的 `[n]`：
- 字号比正文小 1–2pt（如正文 14pt，角标 12pt）；
- 颜色用主题强调色或正文灰，不要红；
- 与前一个字之间留半角空格（python-pptx 中加 ` `，不是 ` `）；
- 同样按照中英文规则分 run：方括号和数字属于"非中文"，用 Times New Roman。

### 4 · 单页引用条目数量上限

8pt 灰字、行高 1.0、页脚带 1.6cm 高、宽约 30cm 的情况下：
- 单条平均长度 ≤ 60 字符 → 可放 2 条；
- 单条 60–100 字符 → 1 条；
- 超过 4 条 → 不要硬塞，前 3 条 + `等，详见参考文献页 P{n}`，把完整列表挪到独立的参考文献页。

Route D（综述讲解）一定会触发"挪到独立页"，参见 [route-literature-review.md](route-literature-review.md) 的"分级 1 · 极高密度页"。

### 5 · 颜色与对比度

- 默认灰：`#888888`（在白底上 4.5:1 对比度，AA 级可读，不抢注意力）；
- 深主题（极少数情况）：用 `#BBBBBB` 防止过暗；
- 不要用纯黑或带饱和度的颜色，否则会与正文抢眼。

### 6 · 字号选择

| 场景 | 字号 |
|---|---|
| 普通页底部页脚条目 | 8pt |
| 参考文献独立页（Route D 的 P16） | 10pt |
| 正文角标 `[n]` | 比正文小 1–2pt |
| 图注尾部"图来源：[3]" | 与图注同号（一般 9pt） |

---

## 与各路线的对接清单

| 路线 | 引用密度 | 是否需要独立参考文献页 | 默认引用形式 |
|---|---|---|---|
| Route A · 学术论文 | 低（论文本体即来源） | 可选（答辩时建议有） | GB/T 7714 |
| Route B · 课程报告 | 中（含政策、新闻、统计） | 可选 | GB/T 7714（必须含 [Z]/[N]/[EB/OL] 多类型） |
| Route C · 开题报告 | 高（国内外现状） | **必须有**，按引用顺序 | GB/T 7714 |
| Route D · 文献综述 | **极高** | **必须有，可跨多页** | GB/T 7714（顺序编码制） |

---

## 自检清单（生成后逐页检查）

- [ ] 正文每个 `[n]` 都能在页脚或参考文献页找到对应条目；
- [ ] 没有"裸"引用（出现外部观点但没有标 `[n]`）；
- [ ] 中文条目里的英文期刊名 / DOI / 页码全部走 Times New Roman，中文走微软雅黑；
- [ ] 页脚条目颜色为浅灰 `#888888`，不抢注意力；
- [ ] 引文条目没有遮挡 `bottom_banner` 或图片；
- [ ] 同一文献在同一页只出现一次完整条目；
- [ ] 参考文献页（如有）的编号与正文角标完全一致、无跳号无重号。
