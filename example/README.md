# 示例说明

本目录提供一份完整的新疆大学本科毕业论文（设计）Markdown 示例，用来验证 `thesis-md2docx` 的主要导出能力。

## 文件

```text
example/
├── thesis-demo.md
├── img/
│   ├── benchmark4_summary_bars.png
│   └── benchmark4_eval_overview.png
└── output/
    ├── thesis-demo.docx
    ├── thesis-demo.pdf
    └── pages/
```

`thesis-demo.md` 是示例主稿，`img/` 存放示例图片。`output/` 属于导出结果目录，默认不会提交到 Git。

## 运行

在仓库根目录执行：

```bash
./export-example.sh
```

Windows PowerShell：

```powershell
.\export-example.ps1
```

一键脚本会生成：

- `example/output/thesis-demo.docx`
- `example/output/thesis-demo.pdf`
- `example/output/pages/page-*.png`

默认 PDF 后端是 `auto`。如需指定后端：

```bash
THESIS_DOCX2PDF_BACKEND=word ./export-example.sh
THESIS_DOCX2PDF_BACKEND=libreoffice ./export-example.sh
```

分页图片需要 `pdftoppm`。Linux / WSL 可安装 `poppler-utils`；Windows 需要安装 Poppler 并把 `pdftoppm` 加入 PATH。

分页图片默认 120 DPI，可用 `THESIS_PDF_PREVIEW_DPI=160 ./export-example.sh` 调整。

如果当前环境是 WSL，且 Windows 侧安装了 Microsoft Word，可以继续用高保真 Word 后端导出 PDF：

```bash
md2docx example/thesis-demo.md --pdf --out example/output --backend word
```

如果没有 Word，也可以使用 LibreOffice 后端做快速预览：

```bash
md2docx example/thesis-demo.md --pdf --out example/output --backend libreoffice
```

也可以一次生成 DOCX、PDF 和分页图片：

```bash
md2docx example/thesis-demo.md --pdf --pages --out example/output --backend auto
```

PDF 生成后，也可以手动重新渲染分页图片到 `output/pages/`：

```bash
mkdir -p example/output/pages
pdftoppm -png -r 120 example/output/thesis-demo.pdf example/output/pages/page
```

## 示例覆盖内容

这份示例刻意覆盖真实论文中常见且容易出格式问题的元素：

- 封面信息、原创性声明、任务书、中英文摘要和目录；
- 一级、二级、三级标题；
- 正文段落、引用块和代码块；
- 行内公式、块公式和公式编号；
- Markdown 管道表格和长表拆分标记；
- 单图、并排图和图题；
- 正文参考文献引用、参考文献列表、致谢和附录。

## 写作约定

- 正文从第一个编号一级标题开始，例如 `# 1 绪论`。
- 前置部分使用二级标题，例如 `## 封面信息`、`## 摘要`、`## ABSTRACT`。
- 图题和表题单独成行，建议使用 `图 2-1 ...`、`表 2-1 ...`。
- 并排图使用 `:::figure-row` 容器，容器内每行放一张图片。
- 长表拆分标记写在表题和表格之间，例如 `<!-- thesis-table-split: 8, 10 -->`。
- 参考文献正文引用建议写作 `[1]`、`[1-3]`、`[1，3-4]`。

## 改成自己的论文

建议先复制 `thesis-demo.md`，再逐步替换：

1. 修改 `封面信息`、`声明`、`任务书`、`摘要` 和 `ABSTRACT`。
2. 保留正文标题的编号结构，例如 `# 1 绪论`、`## 1.1 研究背景`。
3. 把图片放到 Markdown 同级的 `img/` 目录，并使用相对路径引用。
4. 参考文献条目放在 `# 参考文献` 之后，致谢放在 `# 致谢` 之后。
5. 把生成物放入 `output/`，例如 `output/thesis-demo.docx`、`output/thesis-demo.pdf`。
6. 每次较大修改后重新导出 DOCX，并在 Word / WPS 中刷新目录和检查分页。
