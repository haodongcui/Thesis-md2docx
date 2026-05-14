# 示例说明

本目录提供一份完整的新疆大学本科毕业论文（设计）Markdown 示例，用来验证 `thesis-md2docx` 的主要导出能力。

## 文件

```text
example/
├── thesis-demo.md
├── thesis-demo.docx
├── thesis-demo.pdf
├── img/
│   ├── benchmark4_summary_bars.png
│   └── benchmark4_eval_overview.png
└── pages/
```

`thesis-demo.md` 是示例主稿，`img/` 存放示例图片。`thesis-demo.docx`、`thesis-demo.pdf` 和 `pages/` 属于导出结果，默认不会提交到 Git。

## 运行

在仓库根目录执行：

```bash
./export-example.sh
```

Windows PowerShell：

```powershell
.\export-example.ps1
```

如果当前环境是 WSL，且 Windows 侧安装了 Microsoft Word，可以继续用高保真 Word 后端导出 PDF：

```bash
python3 md2docx.py pdf example/thesis-demo.docx example/thesis-demo.pdf --backend word
```

如果没有 Word，也可以使用 LibreOffice 后端做快速预览：

```bash
python3 md2docx.py pdf example/thesis-demo.docx example/thesis-demo.pdf --backend libreoffice
```

也可以一步生成 DOCX 和 PDF：

```bash
python3 md2docx.py all example/thesis-demo.md example/thesis-demo.docx example/thesis-demo.pdf --profile xju-undergraduate-thesis --backend auto
```

PDF 生成后，可以渲染分页图片到 `pages/`：

```bash
mkdir -p example/pages
pdftoppm -png -r 120 example/thesis-demo.pdf example/pages/page
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
5. 让输出文件与 Markdown 同名，例如 `thesis-demo.md`、`thesis-demo.docx`、`thesis-demo.pdf`。
6. 每次较大修改后重新导出 DOCX，并在 Word / WPS 中刷新目录和检查分页。
