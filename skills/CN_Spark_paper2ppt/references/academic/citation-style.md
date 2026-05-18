# Citation Style
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在任何页面需要引用文献、论文图表或参考文献页时读取；它规定 GB/T 7714 编号、页脚、参考文献页和中英文字体混排。

The main path is SVG. Citation footers are written as SVG `<text>` plus mixed-font `<tspan>` runs, then converted to editable DrawingML. Direct python-pptx citation writing is only a fallback idea; do not use it unless the SVG path is unavailable.

Whenever a slide uses another author's claim, data, figure, table, model, formula, policy text, or web resource, three things are required:
1. A body marker such as `[n]`.
2. A footer entry or reference-page entry matching `[n]`.
3. Mixed-font segmentation for CJK and Latin / numeric text.

## Default Style

Use GB/T 7714 numbered citation style by default. Number references in first-appearance order. The same number must be used in body markers, figure captions, citation footers, and reference pages.

Do not translate citation titles across languages. Keep Chinese-language sources in their original Chinese form when the output deck is allowed to contain Chinese; keep English-language sources in English. If the surrounding document must remain English-only, use placeholders in templates and fill final Chinese entries at deck-generation time.

## Common Entry Templates

Use these structures when building `citation_footer` or reference pages:

| Source type | Template |
|---|---|
| Journal article | `[n] Author A, Author B. Title[J]. Journal, Year, Volume(Issue): pages.` |
| Conference paper | `[n] Author A, Author B. Title[C]//Proceedings Name. Place: Publisher, Year: pages.` |
| Monograph | `[n] Author. Book Title[M]. Place: Publisher, Year.` |
| Thesis | `[n] Author. Thesis Title[D]. City: Institution, Year.` |
| Report | `[n] Organization. Report Title[R]. City: Organization, Year.` |
| Policy / standard | `[n] Organization. Policy or Standard Title: document number[Z]. Date.` |
| Newspaper | `[n] Author. Article Title[N]. Newspaper, Date(Page).` |
| Web resource | `[n] Organization. Page Title[EB/OL]. (Published date)[Accessed date]. URL.` |
| Online dataset | `[n] Organization. Dataset Title[DS/OL]. Version. (Published date)[Accessed date]. URL or DOI.` |
| Online software / code | `[n] Author or Organization. Software Title[CP/OL]. Version. (Published date)[Accessed date]. URL.` |
| Preprint | `[n] Author A, Author B. Title[EB/OL]. (Published date)[Accessed date]. arXiv:xxxx.xxxxx or DOI.` |

If there are more than three authors, list the first three and use `et al.` for English entries or the target-language equivalent for Chinese entries.

## Citation Markers In Slide Body

Rules:
- Put `[n]` at the end of the cited sentence or caption.
- Use a smaller size than body text when possible.
- Use neutral gray or the deck text color; do not use brick red for citation markers.
- Insert a normal half-width space before `[n]` if needed for readability.
- Segment brackets and numbers as Latin / numeric runs.

## Footer Rules

Every cited evidence page should include `citation_footer` unless the page is a high-density reference-matrix page that explicitly points to a full reference page.

Footer placement:
- above `bottom_banner`;
- above page number when both would collide;
- never over a figure, formula, or table;
- use the footer zone reserved in `spec_lock.md`.

Footer style:
- font size: 8-11 px;
- fill: `#888888` on light backgrounds, or a muted light gray on dark backgrounds;
- line height: 1.0-1.2;
- no boxes, shadows, decorative rules, or brick-red emphasis;
- no more than three full entries on an ordinary slide.

If a slide needs more than three entries:
- show the first three plus a pointer to the reference page;
- move the complete list to `references_page`;
- for Route D concept matrices, use only markers inside the matrix and place full entries on the reference page.

## Mixed-Font SVG Contract

Any citation containing CJK plus Latin letters, numbers, DOI strings, journal metadata, or URLs must be split into `<tspan>` runs:

```svg
<text x="60" y="650" font-size="10" fill="#888888">
  <tspan font-family="Microsoft YaHei, Source Han Sans SC, sans-serif">[1] Author. Title</tspan>
  <tspan font-family="Times New Roman, serif">[J]. Journal, 2025, 80(3): 512-528. DOI: ...</tspan>
</text>
```

Use CJK fonts for Chinese text. Use `Times New Roman` or the declared Latin serif stack for:
- numbers;
- years;
- volume / issue / pages;
- English journal names;
- DOI;
- URL;
- Latin author names.

Do not put Chinese journal names in `Times New Roman`.

## Figure And Table Source Captions

When embedding a source figure:
- add a concise caption near the figure;
- include a marker such as `Source: Fig. 2 in [3]`;
- include the full entry in the footer or reference page.

When using a complex table screenshot:
- use `crop: meet`;
- do not crop away row / column labels;
- add the source marker near the table;
- cite the original paper, report, or dataset.

## Route-Specific Citation Density

| Route | Citation density | Reference page |
|---|---|---|
| Route A academic paper | Low to medium; the paper itself is the main source | Optional but recommended |
| Route B course / policy / case report | Medium; policy, news, statistics, academic literature may mix | Optional |
| Route C proposal | High; research status and feasibility claims require sources | Required |
| Route D literature review | Very high; concept matrices may contain many references | Required, may span multiple pages |

## Reference Page Rules

Use `references_page` content type.

Rules:
- full entries in citation-number order;
- no missing numbers, duplicates, or numbering gaps;
- 10 px or equivalent readable size for reference pages;
- two columns are allowed for dense decks;
- keep header if the template requires it;
- omit bottom banner if it would reduce readability;
- preserve mixed-font runs.

## Self-Check

- [ ] Every body marker resolves to a footer or reference-page entry.
- [ ] No external claim appears without a marker.
- [ ] No source figure appears without a caption and citation.
- [ ] Footer entries do not overlap bottom banners or page numbers.
- [ ] Dense Route D pages point to a full reference page when footers cannot fit.
- [ ] Mixed CJK / Latin / numeric citation text is segmented by `<tspan>`.
- [ ] Citation color is muted and never brick red.
