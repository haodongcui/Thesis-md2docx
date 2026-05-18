# Usage Guide

本文档说明 Markdown 源稿应该怎样组织，以及常见论文元素应该怎样写。建议先复制 `example/thesis-demo.md`，再逐步替换为自己的论文内容。

## 输出文件建议

直接导出模式的 `--out` 表示输出目录；不传 `--out` 时，默认写入 Markdown 同级的 `output/`。建议源稿和生成物分开，Markdown 与图片放在外层，DOCX、PDF 和分页图放入 `output/`：

```text
paper/
├── thesis.md
├── img/
└── output/
    ├── thesis.docx
    ├── thesis.pdf
    └── pages/
```

Markdown 和 `img/` 是源文件；`output/` 是可删除、可重建的导出产物目录。示例目录也按这个约定组织。

## 基本结构

开始写作前建议先检查环境：

```bash
md2docx check
md2docx profiles
```

如果有公式，建议安装公式依赖：

```bash
npm install --prefix thesis_md2docx/math/latex2omml_node
```

推荐结构如下：

```markdown
# 论文题目

## 封面信息
论文题目：你的论文题目
学生姓名：张三
学号：2022xxxxxx
所属院系：某某学院
专业：某某专业
班级：某某班
指导教师：某某老师
日期：2026 年 4 月

---

## 声明
声明正文。

作者签名：__________
签字日期：__________

---

## 任务书
自动补全：是
届：2026
工作开始日期：2026 年 3 月 1 日
工作结束日期：2026 年 5 月 20 日
目的及意义：任务书中的目的及意义。
主要工作任务：任务书中的主要工作任务。
教研室主任：
接受任务日期：

---

## 摘要
中文摘要正文。

关键词：关键词1；关键词2；关键词3

---

## ABSTRACT
English abstract.

KEY WORDS: Keyword one; Keyword two; Keyword three

---

## 目录
这里可以放占位文字；导出器会写入 Word 目录域。

---

# 1 绪论
## 1.1 研究背景
### 1.1.1 三级标题示例
正文。

# 参考文献
[1] 作者. 文献题名[文献类型]. 出版信息.

# 致谢
致谢正文。

# 附录
## 附录 A 附加材料
附录正文。
```

## 前置部分

前置部分使用二级标题组织。当前内置的 `xju-undergraduate-thesis` profile 会识别这些标题：

- `## 封面信息`
- `## 声明`
- `## 任务书`
- `## 摘要`
- `## ABSTRACT`
- `## 目录`

`封面信息` 中的字段建议使用中文冒号或英文冒号，字段名保持稳定：

```markdown
论文题目：基于世界模型的高效自适应强化学习算法研究
学生姓名：张三
学号：2022xxxxxx
所属院系：软件学院
专业：软件工程
班级：软件工程 22-1 班
指导教师：李四
日期：2026 年 4 月
```

如果要在声明签名位置放电子签名图片，可以把 `作者签名：` 写成图片引用：

```markdown
作者签名：![电子签名](img/signature.png)
```

`任务书` 默认会用封面信息回填学院、班级、姓名、题目、指导教师。若要复刻学校范例中的空白任务书，可在任务书中写 `自动补全：否`。

## 正文标题

正文从第一个编号一级标题开始：

```markdown
# 1 绪论
## 1.1 研究背景
### 1.1.1 三级标题示例
```

注意：

- 只支持一级到三级标题作为正式论文标题层级。
- 一级标题建议写成 `# 1 绪论`。
- 二级标题建议写成 `## 1.1 研究背景`。
- 三级标题建议写成 `### 1.1.1 三级标题示例`。
- 导出器会尽量使用 Word 原生编号，避免把编号硬编码进最终标题文本。

## 段落

普通正文直接写 Markdown 段落即可。软换行会被合并成同一个段落，空行会结束当前段落。

```markdown
这是第一段正文。正文段落会按新疆大学本科毕业论文格式设置字体、字号、首行缩进和行距。

这是第二段正文。
```

如果需要保留 Word 段落内部的人工换行，可以在 Markdown 行末写两个空格，或写反斜杠：

```markdown
这一行导出后仍会在同一段落内换行。\
这一行不会被合并到上一行末尾。
```

普通论文正文不建议大量手动断行；只有复刻学校范例、固定封面字段或控制个别段落分页时才建议使用。

引用块和代码块支持基础导出：

````markdown
> 这是一段引用说明。

```python
def example():
    return "hello"
```
````

代码块只适合少量示例，不建议放大段程序。

## 图片

图片建议放在 Markdown 同级目录下的 `img/` 中，并使用相对路径：

```markdown
![实验流程图](img/pipeline.png)
图 2-1 实验流程图
```

约定：

- 图题单独成行。
- 图题建议写成 `图 2-1 xxx`。
- 图片缺失时导出器会放置占位文本，最终提交前必须检查。

如果需要复刻模板中的精确图片尺寸，可以在图片后追加尺寸属性：

```markdown
![实验流程图](img/pipeline.png){width_emu=4942840 height_emu=2432685 crop_bottom=7802}
```

`width_emu` 和 `height_emu` 使用 Word OOXML 的 EMU 单位；只写其中一个时会按图片原比例自动计算另一个。`crop_top` / `crop_right` / `crop_bottom` / `crop_left` 使用 OOXML 的千分之一百分比裁剪值，适合复刻范例里被 Word 手动裁剪过的图片。普通论文写作通常不需要手动指定这些属性，只有对齐学校范例或固定版面时才建议使用。

需要复刻模板中图片所在段落的样式和段前段后时，也可以追加图片段落属性：

```markdown
![图1-1 标题](img/figure.png){width_emu=4942840 height_emu=2432685 p_style=af9 align=none line=360 before=120 after=120 keep_next=false}
```

常用属性包括 `p_style`、`align`、`line`、`before`、`after`、`before_lines`、`after_lines`、`mark_style` 和 `keep_next`。这些属性偏底层，主要用于 profile 示例复刻，不建议普通写作时频繁手调。

## 并排图

并排图使用 `:::figure-row` 容器：

```markdown
:::figure-row
![方法 A](img/method-a.png)
![方法 B](img/method-b.png)
:::
图 3-2 不同方法的可视化对比
```

建议并排图数量保持在 2 张。图片尺寸差异过大时，应先裁剪或统一图片比例，再导出。

## 表格

普通 Markdown 管道表格可以直接写：

```markdown
表 2-1 实验参数设置

| 参数 | 取值 | 说明 |
| --- | --- | --- |
| 学习率 | 0.001 | 优化器初始学习率 |
| 批大小 | 64 | 每轮训练样本数 |
```

约定：

- 表题放在表格前一行。
- 表题建议写成 `表 2-1 xxx`。
- 表格不适合写得过宽，列太多时建议拆分。

长表可以在表题和表格之间添加拆分标记：

```markdown
表 4-3 长表结果

<!-- thesis-table-split: 8, 10 -->

| 指标 | 实验1 | 实验2 |
| --- | --- | --- |
| ... | ... | ... |
```

标记中的数字表示按数据行拆分续表，例如 `8, 10` 表示第一段 8 行，第二段 10 行，剩余行自动进入后续表。

复杂表格使用 `::: table` 扩展语法。它用于学校范例中的合并表头、固定列宽和特殊三线表线宽：

```markdown
表 1-2 方弯管内流动最大速度比较

::: table {width=8529 width_type=dxa widths=2251,1546,1548,1547,1637 top_border=18 bottom_border=18 header_rows=2 header_bold=false}
| 项目 {rowspan=2 continue_left=44 continue_first_line=1764 continue_first_line_chars=840} | 层流 {colspan=2} | 紊流 {colspan=2} |
| 0°截面 | 90°截面 | 0°截面 | 90°截面 |
| 理论值 Vmax/m·s-1 | 0.04 | 0.03 | 1.30 | 1.25 |
| 计算值 Vmax/m·s-1 | 0.04 | 0.03 | 1.26 | 1.21 |
:::
```

可用参数：

- `width` / `width_type`：表格总宽度和单位，常用 `width_type=dxa` 或 `pct`。
- `widths`：逗号分隔的列宽，单位 dxa。
- `top_border` / `mid_border` / `bottom_border`：顶线、中线、底线线宽，OOXML 中 `8` 约等于 1 磅。
- `header_rows`：没有 Markdown 分隔线时，显式声明前几行是表头。
- `header_bold=false`：表头不加粗，适合复刻部分学校范例表格。
- `caption="表1-1 标题"`：把表题作为表格第一行，适合复刻范例中的特殊续表结构。
- `row_height` / `row_heights`：设置统一行高或逐行行高，单位 dxa。
- `repeat_header_rows` / `cant_split_rows`：精确控制重复表头行和禁止跨页拆分的行。
- `layout` / `look` / `cell_margins`：控制底层 Word 表布局、`tblLook` 和表格单元格边距。
- `cell_width_type` / `cell_widths`：当表宽用 `pct` 但网格列宽仍用 dxa 时，可单独控制单元格 `tcW`。
- `cell_style=none` / `font_size=inherit` / `paragraph_after=omit`：少写直接属性，尽量复刻模板继承出来的单元格样式。
- `header_bold_cs=true` / `rowspan_restart_bottom_border=false`：复刻复杂表头里只写复杂字体加粗、纵向合并起始格不写底线的情况。
- `body_bold_cs=true`：复刻表体 run 带复杂字体加粗标记的情况。
- `paragraph_first_line` / `paragraph_first_line_chars` / `header_top_border_size`：控制单元格内段落缩进和表头单元格顶线粗细。
- `row_top_borders` / `row_bottom_borders`：逐行声明单元格顶线/底线，值可写 `12`、`8`、`nil`、`none`。
- 单元格 `{colspan=2}`、`{rowspan=2}`：横向/纵向合并。
- 单元格 `{left=44}`、`{first_line=480}`、`{first_line_chars=200}`：覆盖单个单元格内段落缩进。
- 单元格 `{continue_left=44}`、`{continue_first_line=1764}`、`{continue_first_line_chars=840}`：覆盖纵向合并续接单元格的段落缩进。
- 单元格 `{bold_cs=false}`、`{style=10}`、`{font_size=21}`、`{font_size_cs=false}`、`{first_line=omit}`：覆盖单元格内 run 和段落属性。
- `{{sym:Times New Roman:0000}}` 可写入 Word 符号 run，用于复刻范例文件中的特殊符号结构。
- `{{sup:-1}}` / `{{sub:max}}` 可写入 Word 上标/下标 run；结合 `*...*` 可表达斜体变量下标，如 `*V{{sub:max}}*`。

## 公式

行内公式使用单个 `$`：

```markdown
状态表示为 $s_t$，动作表示为 $a_t$。
```

块公式使用独立的 `$$`：

```markdown
$$
J(\theta)=\mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^{T}\gamma^t r_t\right]
$$
```

如果安装了公式转换依赖，公式会尽量转换为 Word 原生 OMML；否则会以 LaTeX 文本保底导出。

需要复刻 Word 模板中已经排好的公式视觉效果时，可以给公式块指定图片：

```markdown
$$ {image=img/formula-1-1.wmf image_alt="公式 1-1" width_emu=750570 height_emu=284480}
q = k_d H^x
$$
```

这种写法保留 LaTeX 作为源文本，但导出时优先嵌入 `image` 指定的图片，并继续使用自动公式编号。`width_emu` / `height_emu` 使用 Word OOXML 的 EMU 单位；普通论文写作优先使用纯 LaTeX 公式，只有对齐学校范例或固定版面时才建议指定公式图片。

安装公式依赖：

```bash
cd thesis_md2docx/math/latex2omml_node
npm install
```

常见 `\hat{}`、`\bar{}` 等重音公式已经有后处理，但复杂公式仍建议最终在 Word/WPS 中检查。

## 参考文献与引用

正文引用建议写成：

```markdown
已有研究表明该方法能够提升样本效率[1-2]。
也可以引用多个来源[1，3-4]。
```

参考文献列表写在 `# 参考文献` 后：

```markdown
# 参考文献

[1] 作者. 文献题名[文献类型]. 出版信息.
[2] 作者. 文献题名[文献类型]. 出版信息.
```

导出器会尽量生成正文上标引用和文末跳转链接。参考文献条目的真实性和 GB/T 7714 细节仍需要人工核对。

## 致谢和附录

致谢使用一级标题：

```markdown
# 致谢

致谢正文。
```

附录结构：

```markdown
# 附录

## 附录 A 附加材料

附录正文。
```

附录中的图表引用会按当前 profile 做一定归一化处理，但仍建议最终检查编号和正文引用是否一致。

## 常见问题

- 不要把正文内容写在 `## 目录` 前面，否则可能被当作前置部分。
- 不要跳过一级标题直接从 `## 1.1` 开始正文。
- 图题、表题不要和正文混在同一段。
- 图片路径尽量使用相对路径，不要使用本机绝对路径。
- 生成 DOCX 后需要在 Word/WPS 中打开并刷新目录域和页码。
- 最终提交前必须人工检查分页、孤行、表格跨页、公式和参考文献格式。

## 推荐导出流程

日常写作时：

```bash
md2docx thesis.md
```

需要预览版式时：

```bash
md2docx thesis.md --pdf --pages --out output --backend auto
```

最终检查时，优先使用 Microsoft Word 后端导出 PDF：

```bash
md2docx thesis.md --pdf --out output --backend word
```

LibreOffice 后端适合快速预览或没有 Word 的环境，但最终分页和字体效果仍以 Word/WPS 人工检查为准。

如果要和学校范例或历史版本做视觉回归，可以对比 PDF 页面像素：

```bash
md2docx compare-pdf reference.pdf output/thesis.pdf --out output/pdf-audit.md --diff-dir output/pdf-diff
```

`--diff-dir` 会为存在差异的页面生成红色差异图。该命令依赖 `pdftoppm`，DPI 可用 `--dpi` 调整。
