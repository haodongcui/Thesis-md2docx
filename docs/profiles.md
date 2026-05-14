# Profile Development

Profile 是学校、学位和文档格式规则的边界。通用层负责 Markdown 扫描、图片、公式、表格和 DOCX 打包；profile 负责解释这些元素在某个论文格式中的含义。

## Profile 需要定义什么

新增一个学校或学位格式时，建议新建：

```text
thesis_md2docx/profiles/<school_degree_thesis>/
├── __init__.py
├── profile.py
├── body.py
├── document.py
├── frontmatter.py
├── styles.py
├── header_footer.py
└── format_requirements/
```

最少需要实现：

- `profile.py`：定义 `ThesisProfile` 子类，并在 `profiles/registry.py` 注册。
- `document.py`：定义封面、声明、摘要、目录、正文、致谢、附录等文档结构。
- `frontmatter.py`：定义封面、声明、任务书、摘要、关键词等前置页渲染。
- `body.py`：定义正文标题、参考文献、附录、图表题、公式编号等规则。
- `styles.py`：定义 Word 样式目录、样式角色映射、编号、字体表等。
- `header_footer.py`：定义该 profile 的页眉页脚。
- `format_requirements/`：保存学校格式文件或说明，作为 profile 维护依据。

Profile 还应显式提供：

- `front_matter_spec()`：前置页 key、标题文字、摘要关键词前缀。
- `front_matter_plan()`：前置页页面顺序、来源 key、标题、分页行为。
- `document_layout()`：封面、前置页、正文起始、正文延续等分节规则。
- `style_catalog()`：结构化声明 Word 样式，包括正文、标题、目录、图表题、参考文献、页眉页脚等。
- `style_roles()`：把通用语义角色映射到具体 Word 样式 ID，例如 `body.normal -> XjuBody`。
- `required_style_roles()`：声明该 profile 必须覆盖哪些语义角色；论文 profile 默认使用 `COMMON_THESIS_STYLE_ROLES`。
- `body_style_profile()`：返回 `BodyRenderProfile`，声明正文渲染会用到的样式引用、段落参数和特殊 hook。
- `style_bundle()`：styles、numbering、settings、font table、页眉页脚。
- `package_parts()`：DOCX 包内各 XML 部件路径；默认使用标准 Word 路径。

## 通用层和 profile 的边界

通用层可以处理：

- Markdown 段落、标题、代码块、公式块、图片、表格。
- 将 Markdown 正文解析为 `HeadingBlock`、`ParagraphBlock`、`TableBlock`、`ImageBlock` 等 IR block。
- 行内公式、行内代码、加粗、斜体、参考文献跳转。
- DOCX zip 包结构、媒体文件关系、PDF 后端调用。

Profile 应该处理：

- 哪些前置部分存在，例如封面、声明、任务书、摘要、目录。
- Markdown 前置部分 key 与最终显示标题的映射。
- 前置页的页面顺序、分页行为和是否为英文页。
- 正文从哪个标题开始。
- 哪些标题不编号，例如参考文献、致谢、附录。
- 章节、附录、公式、图、表的编号规则。
- 正文、标题、图表题、参考文献、页眉页脚、目录样式。
- 页面尺寸、页边距、分节、页码格式。
- 学校或学位专用封面字段和固定文本。

当前 XJU profile 已经把封面、前置页、页眉页脚、样式 ID、编号和字体表都放回 profile 内。通用层不应该直接出现 `XjuBody`、`XjuHeading1` 这类学校专用样式名。

## 转换链路

整体链路如下：

```text
Markdown 文件
  -> parse_markdown_document()
  -> front sections + body text
  -> parse_body_blocks()
  -> IR blocks
  -> build_document_blocks()
  -> profile document/frontmatter/body/styles/layout
  -> OOXML parts
  -> DOCX zip
  -> PDF backend（可选）
```

职责划分：

- `markdown.py`：切分标题、前置部分和正文。
- `parser.py`：把正文 Markdown 扫描成 `HeadingBlock`、`ParagraphBlock`、`TableBlock` 等 IR。
- `ir.py`：定义中间结构，尽量不包含学校样式细节。
- `builders/document.py`：通用正文 IR 到 OOXML 的调度器，通过 profile hook 渲染特殊格式。
- `layout.py`：定义分节、前置页 plan、DOCX 包部件和样式 bundle 等结构化规格。
- `ooxml/`：提供段落、表格、图片、字段、包部件等基础 OOXML 构造。
- `profiles/<name>/`：决定某个学校/学位格式到底怎样排版。
- `pdf/`：负责 DOCX 到 PDF，不影响 DOCX 生成逻辑。

## 样式体系

样式要按“语义角色”组织，不要让通用正文渲染器直接依赖某个学校的样式 ID。推荐分成三层：

- `StyleCatalog`：声明 Word 样式本身，例如 `XjuBody`、`XjuHeading1`、`XjuReference`。
- `StyleRoleMap`：声明语义角色到样式 ID 的映射，例如 `body.heading.level1 -> XjuHeading1`。
- `StyleRole` / `COMMON_THESIS_STYLE_ROLES`：提供公共语义角色常量和默认论文必需角色清单。
- `BodyRenderProfile`：把正文渲染需要的样式引用、默认段落格式、默认 run 格式和渲染 hook 绑定起来。
- `StyleBundle`：把 catalog 和其他 DOCX 部件输出成最终 `styles.xml`、`numbering.xml`、`fontTable.xml` 等。
- `NumberingCatalog`：结构化声明多级标题编号，对应 `word/numbering.xml`。
- `FontTableSpec`：结构化声明字体表，对应 `word/fontTable.xml`。

新增 profile 时至少要覆盖这些语义角色：

- `body.normal`
- `body.heading.level1`
- `body.heading.level2`
- `body.heading.level3`
- `front.heading`
- `toc.field`
- `caption.default`
- `reference.item`
- `table.cell`
- `math.block`
- `header.default`
- `footer.default`

样式、布局和渲染规则要分清楚：字体字号、缩进、行距属于样式；页边距、分节、页码属于布局；图片缩放、表格列宽、公式编号属于渲染规则。

`thesis_md2docx.styles.properties` 提供了常用 OOXML 样式属性 helper。新增 profile 时，优先使用结构化 helper，而不是直接拼裸 XML 字符串：

```python
from thesis_md2docx.styles.properties import indent, run_fonts, run_size, spacing, style_props

StyleSpec(
    style_id="Body",
    name="Body",
    paragraph_props=style_props(
        spacing(after=0, line=360),
        indent(first_line_chars=200, first_line=480),
    ),
    run_props=style_props(
        run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
        run_size(24),
    ),
)
```

如果某个学校模板需要非常特殊的 Word 属性，仍可在 `style_props(...)` 里临时保留原始 XML 字符串。这样能兼顾结构化和复杂模板的逃生口。

`md2docx doctor` 会校验默认 profile 的样式目录和角色映射，能提前发现：

- 前置页 plan 缺少封面、目录或必要 source key；
- 重复的 style id；
- `basedOn` 或 `next` 指向不存在的样式；
- 必需语义角色未覆盖；
- 语义角色指向未声明的样式。
- 正文渲染 profile 引用了不存在的样式；
- 正文渲染 profile 缺少必要 hook。

## 正文解析规则

正文语义规则由 `BodyParseRules` 描述。不同学校通常需要调整：

- `reference_heading`
- `acknowledgement_heading`
- `appendix_heading`
- `unnumbered_headings`
- `reference_entry_pattern`
- `caption_pattern`
- `table_caption_prefixes`
- `chapter_number_pattern`

例如 XJU 本科论文的规则放在：

```text
thesis_md2docx/profiles/xju_undergraduate_thesis/body.py
```

## 正文渲染 Profile

`body_style_profile()` 返回 `BodyRenderProfile`。它负责连接“通用 IR 调度器”和“具体 profile 的排版规则”，主要包含：

- `BodyStyleRefs`：正文、标题、图表题、表格、公式、参考文献等样式 ID。
- `ParagraphFormatSpec`：正文首行缩进、额外段落属性等段落参数。
- `RunFormatSpec`：正文默认字体、字号、加粗、斜体等字符参数。
- 渲染 hook：处理标题、图表题、参考文献、表格、附录标题归一化、分节等复杂规则。

常用 hook 包括：

- `heading_builder`
- `acknowledgement_heading_builder`
- `caption_builder`
- `reference_builder`
- `table_builder`
- `appendix_heading_normalizer`
- `appendix_reference_normalizer`
- `section_pr_builder`

这些 hook 让通用正文构建器不需要知道具体学校规则。简单格式可以只调整样式和段落参数；复杂学校模板可以通过 hook 接管局部渲染。

## 前置页 Plan

`FrontMatterSpec` 描述 Markdown 前置部分使用哪些 key 和标题文字；`FrontMatterPlan` 描述这些页面按什么顺序装配。默认论文 plan 包含：

```text
cover -> declaration -> taskbook -> cn abstract -> en abstract -> toc
```

每个 `FrontMatterPageSpec` 至少包含：

- `kind`：页面类型，例如 `cover`、`declaration`、`taskbook`、`abstract`、`toc`。
- `source_key`：从 Markdown 前置部分读取哪个 key。
- `title`：最终显示标题。
- `keyword_prefix`：摘要关键词前缀。
- `english`：是否使用英文摘要渲染规则。
- `page_break_before` / `page_break_after`：分页行为。

复杂学校模板仍然可以在 profile 的 `document.py` 中保留专用渲染函数，但页面顺序和来源 key 应尽量由 plan 显式表达。

## 前置页字段 Spec

页面 plan 只描述“有哪些页面、按什么顺序出现”。页面内部字段建议继续用 profile 内的 spec 显式表达，例如 XJU 本科 profile 目前包含：

- `CoverFieldSpec`：封面字段来源 key 和最终显示标签。
- `TaskbookValueSpec`：任务书字段名、Markdown 任务书 key、封面回退 key、默认值。
- `DeclarationSignatureSpec`：声明页签名标签、日期标签、签名图片 alt、签名前空行数。

这类字段 spec 仍放在具体学校 profile 里，因为不同学校封面字段、任务书字段、签名区要求差异很大。通用层只需要提供前置页 plan 和基础渲染结构。

## DOCX Golden Test

`tests/test_docx_golden.py` 会用 `example/thesis-demo.md` 生成 DOCX，并对稳定 OOXML 部件做 SHA-256 回归检查。它覆盖：

- `word/document.xml`
- `word/styles.xml`
- `word/numbering.xml`
- `word/settings.xml`
- `word/fontTable.xml`
- `word/header1.xml`
- `word/footer1.xml`
- `word/footer2.xml`
- package relationships 和 content types

测试会跳过 `docProps/core.xml`，因为里面包含导出时间。测试也关闭公式转换，避免依赖 Node/npm 和外部公式转换环境。

如果版式改动是有意的，先确认 Word/PDF 效果，再更新 golden hash；如果不是有意的，优先修代码而不是直接改 hash。

## 当前限制

当前 profile 机制优先服务“毕业论文”扩展。它适合新增其他学校、本科、硕士、博士论文格式。项目已经引入轻量 IR 和结构化样式层；如果要扩展到简历、合同、标书、报告等任意 Word 文档，后续还需要继续抽象 front matter、封面页、特殊页面和动态对象布局。

## AST / IR 是什么

AST 是 Abstract Syntax Tree，抽象语法树；IR 是 Intermediate Representation，中间表示。这里的作用是让转换链路分成两步：

```text
Markdown 文本 -> IR blocks -> profile/layout 渲染 -> DOCX OOXML
```

IR block 不关心最终 Word 样式，只表达文档结构。例如：

- `HeadingBlock`
- `ParagraphBlock`
- `ImageBlock`
- `FigureRowBlock`
- `TableBlock`
- `MathBlock`
- `PageBreakBlock`

这样新增格式时，可以复用 Markdown 解析结果，只重写 profile/layout 规则。
