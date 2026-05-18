# 新疆大学本科毕业论文范例复刻检查

本目录用于对照学校范例文件验证 `xju-undergraduate-thesis` profile。

原始附件位于：

- `thesis_md2docx/profiles/xju_undergraduate_thesis/format_requirements/附件1：新疆大学本科毕业论文（设计）规范及格式要求.docx`
- `thesis_md2docx/profiles/xju_undergraduate_thesis/format_requirements/附件2：新疆大学本科毕业论文(设计)范例.docx`

本目录不修改原始附件，只抽取范例正文、图片和表格内容，生成：

- `xju-template-example.md`
- `output/xju-template-example.docx`
- `output/xju-template-example.pdf`
- `output/pages/page-*.png`

## 已对齐

| 项目 | 范例/规范依据 | 当前实现 |
| --- | --- | --- |
| 纸张与页边距 | A4；上/下 2.54cm；左/右 3.17cm；页眉 1.5cm；页脚 1.75cm | 已按相同 twips 写入各节 |
| 页眉 | 小五号宋体，居中，“新疆大学本科毕业论文（设计）”，下横线 | 已实现 |
| 封面标题 | 标题前空行、三号以上黑体、600 exact 行距 | 已按范例 OOXML 对齐 |
| 封面字段表 | 宽 6943 dxa；两列 1948/4995；行高 680；右列下划线 | 已实现，支持显式多行题目 |
| 声明页 | 标题三号黑体，段前 3 行、段后 2 行；正文四号宋体；签名区右对齐 | 已实现 |
| 任务书空白模板 | 范例任务书字段保持空白，不从封面回填 | 已支持 `自动补全：否` |
| 摘要/ABSTRACT/目录标题 | 三号；居中；段前 3 行、段后 2 行 | 已按范例 OOXML 对齐关键段落属性和首 run |
| 正文 | 小四号宋体，首行缩进 2 字符，1.5 倍行距 | 已实现 |
| 一级标题 | 三号宋体，居中，另起页，段前 3 行、段后 2 行 | 已实现 |
| 二级标题 | 小三号宋体，顶格，1.5 倍行距，段前 1 行、段后 0.5 行 | 已实现 |
| 三级标题 | 四号宋体，左起空 2 字符，1.5 倍行距，段前 0.5 行、段后 0 行 | 已实现 |
| 图题/表题 | 五号宋体加粗，居中，1.5 倍行距，段前/段后 0 | 已实现 |
| 三线表 | 通栏；顶线/底线 1.5 磅；中线 1 磅；无左右竖线 | 普通 Markdown 表和富表格均已实现 |
| 复杂表格 | 合并表头、固定列宽、特殊线宽、表题并入表格第一行 | `::: table` 已支持 `header_rows`、`caption`、`colspan`、`rowspan`、`widths`、逐行边框、单元格缩进、run 级属性和 Word 符号 run |
| 正文图片尺寸 | 范例 DOCX 中图片被手动缩放，`wp:extent` 与源图 DPI 推导值不一致 | 示例 Markdown 已用 `width_emu` / `height_emu` 显式复刻，两张正文图片 extent 已对齐；图片段落已支持 `p_style`、段前段后、段落标记样式和 `keep_next` 复刻 |
| 公式视觉对象 | 范例 DOCX 中部分公式为 WMF/OLE 视觉对象 | 示例 Markdown 已支持公式块 `image` 属性，第一条范例公式的 WMF 尺寸和公式编号段落已对齐；后续公式仍以当前公式转换链路为主 |
| 目录域 | 范例目录使用 `TOC \o "1-3" \h \u`，并缓存 PAGEREF 页码域 | 已生成目录缓存项、PAGEREF 域和正文标题书签；XJU profile 按范例排除附录目录项 |
| 公式编号 | 按章编号，如（1-1）、（2-1） | 已实现 |
| 参考文献条目 | 五号，编号顶格，续行悬挂 | `[n]` 条目已实现 |
| 附录总标题 | “附  录”居中，按一级标题格式 | 已实现 |

## 尚未完全一致

| 项目 | 当前差异 | 后续建议 |
| --- | --- | --- |
| 封面 logo 区 | 当前已用定位 drawing 复刻尺寸；段落 index 和 docPr id/name 仍不完全相同 | 视觉优先，docPr id 不影响排版 |
| 公式底层对象 | 范例 DOCX 含 Word/MathType 生成的 OLE 关系；当前不生成 OLE 编辑对象 | 视觉优先；若要继续压低公式页像素差异，需要另行实现 OLE 包结构，单纯插入 WMF 预览图不足以完全复刻 |
| 参考文献前说明文字 | 范例中说明段落与参考文献条目混排；当前 `[n]` 条目按参考文献样式，说明段落按正文样式 | 基本符合视觉，若严格复刻可增加参考文献说明段专用样式 |
| PDF 完全一致性 | 范例 PDF 与当前 Word 后端导出的 PDF 页数和页面尺寸一致，但逐页像素仍有差异 | 已增加 `compare-pdf` 像素审计；继续优先处理内容、字体、段落换行和公式对象差异 |

## 验证命令

```bash
python3 md2docx.py example_xju/xju-template-example.md --pdf --pages --out example_xju/output --backend auto
```

```bash
python3 md2docx.py compare-pdf \
  "thesis_md2docx/profiles/xju_undergraduate_thesis/format_requirements/附件2：新疆大学本科毕业论文(设计)范例.pdf" \
  example_xju/output/xju-template-example.pdf \
  --out example_xju/output/pdf-audit.md \
  --diff-dir example_xju/output/pdf-diff \
  --dpi 144
```

当前验证结果：

- 生成 PDF 页数：25 页。
- 生成分页图片：25 张。
- 学校范例 PDF 页数：25 页。
- `compare-pdf` 页面尺寸已对齐：25 页均为 1191x1685 px（144 DPI）。
- `compare-pdf` 当前像素差异：25 页均有差异，总差异 576,985 / 50,170,875 像素，约 1.15%。
- 官方范例 PDF 由 Acrobat PDFMaker/Adobe PDF Library 生成；同一份官方范例 DOCX 用当前 Word 后端重导 PDF 后，与官方 PDF 自身仍有 466,906 / 50,170,875 像素差异，约 0.93%。因此官方 PDF 的像素差异包含 PDF 导出器差异，不完全等同于 DOCX 排版差异。
- 以“官方范例 DOCX 经当前 Word 后端重导的 PDF”为同后端基准，当前示例 PDF 的总差异为 186,363 / 50,170,875 像素，约 0.371%，已低于官方 PDFMaker 与 Word 后端之间的导出器基线。
- 差异较小页包括声明空白页（第 2 页，0%）、目录页（第 7 页，0%）、参考文献后半页（第 22 页，0%）、致谢页（第 24 页，0%）、正文第一页（第 8 页，同后端约 0.10%）、声明页（第 3 页，同后端约 0.25%）和附录页（第 25 页，同后端约 0.34%）。
- 差异较大页集中在英文摘要说明页、图 1-2/表格页、公式页和参考文献示例页；主要原因是 PDF 生成器、字体渲染、公式底层对象、Word 图片采样方式和范例中的人工 run 级属性仍未完全等价。
- `compare-docx` 分节数已对齐：reference=13，candidate=13；XJU profile 已按范例让“致谢”使用普通分页而非新分节。
- `compare-docx` 字段数已对齐：reference=30，candidate=30；目录使用 `TOC \o "1-3" \h \u`，并生成 PAGEREF 页码域。
- `compare-docx` 关键标题已对齐：封面标题、摘  要、ABSTRACT、目  录、绪论、参考文献均为 `status: same`。
- `compare-docx` 表格 core 已对齐：封面字段表、表1-1、表1-1续表、表1-2、表2-2、表2-3 的表宽、列宽、行数、外边框、`tblLayout`、`tblLook`、表级 cell margins 和行高/行标记均已一致。
- `compare-docx` 表格 detail 已对齐：上述 6 个范例表格的单元格宽度、合并、垂直居中、边框、段落缩进、run 字体属性摘要均已一致。
- `compare-docx` drawing 数量已对齐：reference=4，candidate=4。
- 目录页到正文第一页的分节结构已按范例补齐 TOC 字段结束段、3 个空段和承载分节属性的空一级标题段；TOC1/TOC2/TOC3 缩进和页码 tab 已与 Word 后端重导范例对齐，目录页同后端像素差异已降为 0。
- 参考文献到致谢的分页/分节已按范例收敛：参考文献页后普通分页进入致谢，附录前再创建分节；致谢页像素差异已降到约 0.14%。
- 声明页标题、正文和签名区坐标已按范例反推调整，声明页同后端像素差异约 0.25%。
- 任务书页按范例补齐空白横线段落的段落级 `rPr`、`snapToGrid`、下划线和行距细节，同后端像素差异已降到约 0.165%。
- Markdown 行末两个空格或反斜杠现在可保留为 Word 段内换行，`example_xju` 用于复刻范例中部分人工换行；摘要页正文和中英文关键词说明段的文本 bbox 已与同 Word 后端基准对齐，中文摘要页同后端像素差异约 0.21%。
- 第 2-9 章标题示例页已用显式 `thesis-blank` 复刻范例中的手工空段，标题、正文、公式说明和图题注的坐标已基本对齐；剩余差异主要来自公式对象渲染和少量 run 属性。
- 正文两张图片和第一条公式图片的 `wp:extent` 已与范例一致；图 1-1 所在图片段落的样式、段前段后和分页保持属性已对齐；图 1-2 页通过图片段落后距微调后，同后端差异约 1.15%；公式段落文字 `（1-1）` 已对齐。
- 剩余 drawing 差异主要是 docPr id/name/descr 等 Word 内部对象元数据，不影响页面版式。
- 关键页已对照：封面、声明、目录、正文第一页、三线表页、参考文献页、致谢页、附录页。
