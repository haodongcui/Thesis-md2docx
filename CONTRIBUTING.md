# 贡献指南

感谢关注 `thesis-md2docx`。本项目的目标是把毕业论文 Markdown 主稿稳定导出为符合学校格式要求的 DOCX，并提供可检查的 PDF 预览流程。当前内置 `xju-undergraduate-thesis` profile，用于新疆大学本科毕业论文（设计）。

## 基本原则

- Markdown 是源文件，DOCX/PDF 是生成物。
- 优先修导出器或 Markdown 示例，不建议把手工修改后的 DOCX 作为长期来源。
- 格式改动应尽量对齐学校规范和范例，避免只针对单篇论文做特殊处理。
- 新功能应保持可选和可回退，避免破坏已有论文导出。

## 本地检查

建议先安装开发依赖：

```bash
python3 -m pip install -e ".[dev]"
```

提交前建议至少运行：

```bash
python3 -m py_compile md2docx.py $(find thesis_md2docx tests -name '*.py' -type f | sort)
python3 -m pytest tests
./export-example.sh
python3 md2docx.py doctor --backend auto
```

如果修改了公式转换或 PDF 预览相关代码，还建议运行：

```bash
python3 md2docx.py doctor --backend word
python3 md2docx.py pdf example/thesis-demo.docx example/thesis-demo.pdf --backend word
```

如果修改了 LibreOffice 后端，还建议运行：

```bash
python3 md2docx.py doctor --backend libreoffice
python3 md2docx.py pdf example/thesis-demo.docx example/thesis-demo.pdf --backend libreoffice
```

## 提交内容

建议提交：

- `thesis_md2docx/` 中的源码改动；
- `example/thesis-demo.md` 或 `example/README.md` 中的示例更新；
- `README.md`、`CONTRIBUTING.md` 等文档更新。

不建议提交：

- `example/*.docx`；
- `example/*.pdf`；
- `example/pages/*.png`；
- `example/preview/`；
- `thesis_md2docx/math/latex2omml_node/node_modules/`；
- 本地临时文件、缓存和手工备份文件。

## 格式类改动

如果改动标题、页边距、正文、图题、表题、参考文献、公式或目录相关逻辑，请在说明中写清楚：

- 修改前的问题；
- 对应的学校规范或范例位置；
- 导出后的检查方式；
- 是否会影响已有 Markdown 写法。

`tests/test_docx_golden.py` 会检查示例 DOCX 的稳定 OOXML 部件 hash。若确实有意调整版式，需要同步更新该测试中的 hash，并在提交说明中写清楚变更原因。
