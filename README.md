# Thesis-md2docx

面向毕业论文的 `Markdown -> DOCX -> PDF` 转换工具。

Claude Code、Codex 等 agent 产品让 Markdown 写作很方便，但学校通常要求提交 Word 文档。本项目让 Markdown 负责写作和版本管理，DOCX 负责提交，PDF 负责检查版式。

当前以内置**新疆大学本科毕业论文** `xju-undergraduate-thesis` 为例，可扩展其他学校、其他学位的毕业论文模板。

## 特点

- [x] 内置 `xju-undergraduate-thesis`，按新疆大学本科毕设模板和格式规则实现原生 `md2docx` 转换器。
- [x] 支持封面、声明、任务书、摘要、目录、正文、参考文献、致谢、附录。
- [x] 支持标题、正文、图表、公式、参考文献等常用论文格式。
- [x] 支持 Markdown 表格、长表、单图、并排图、行内公式、块公式。
- [x] 支持 LaTeX 公式转 Word OMML；缺依赖时保留 LaTeX 文本。
- [x] 支持 DOCX 转 PDF：Microsoft Word 后端和 LibreOffice 后端。
- [x] 支持 profile 扩展其他学校和其他学位论文格式。

## 安装

Linux / WSL：

```bash
git clone https://github.com/haodongcui/Thesis-md2docx.git
cd Thesis-md2docx
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell：

```powershell
git clone https://github.com/haodongcui/Thesis-md2docx.git
cd Thesis-md2docx
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Conda 可选，项目依赖仍用 `pip`：

```bash
conda create -n thesis-md2docx python=3.10
conda activate thesis-md2docx
python -m pip install -r requirements.txt
```

公式依赖可选；有公式时建议安装。先安装 Node.js 和 npm，再运行：

```bash
npm install --prefix thesis_md2docx/math/latex2omml_node
```

不安装也能导出，公式会以 LaTeX 文本写入 DOCX。

可编辑安装：

```bash
python -m pip install -e .
md2docx doctor
```

## 快速开始

通用入口：

```bash
python3 md2docx.py doctor
python3 md2docx.py docx example/thesis-demo.md example/thesis-demo.generated.docx --profile xju-undergraduate-thesis
```

Windows 如果 `python` 命令不可用，可以改用：

```powershell
py -3 md2docx.py doctor
py -3 md2docx.py docx example\thesis-demo.md example\thesis-demo.generated.docx --profile xju-undergraduate-thesis
```

一键导出示例：

```bash
./export-example.sh
```

Windows 对应 `export-example.ps1` 或 `export-example.cmd`。

## 常用命令

```bash
# 检查环境
python3 md2docx.py doctor

# 生成 DOCX
python3 md2docx.py docx thesis.md thesis.docx --profile xju-undergraduate-thesis

# 生成 DOCX；不传输出路径时默认生成同名 .docx
python3 md2docx.py docx thesis.md --profile xju-undergraduate-thesis

# DOCX 转 PDF
python3 md2docx.py pdf thesis.docx thesis.pdf --backend word
python3 md2docx.py pdf thesis.docx thesis.pdf --backend libreoffice

# 从 Markdown 一步生成 DOCX 和 PDF
python3 md2docx.py all thesis.md thesis.docx thesis.pdf --profile xju-undergraduate-thesis --backend auto

# 查看可用格式和 PDF 后端
python3 md2docx.py list-profiles
python3 md2docx.py list-backends
```

可编辑安装后，也可以直接使用 `md2docx ...`。

## Markdown 写法

建议复制 `example/thesis-demo.md` 后再改。最小结构：

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
正文。

# 参考文献
[1] 作者. 文献题名[文献类型]. 出版信息.

# 致谢
致谢正文。
```

约定：

- 正文从编号一级标题开始，例如 `# 1 绪论`。
- 前置部分使用二级标题，例如 `## 封面信息`、`## 摘要`、`## ABSTRACT`、`## 目录`。
- 图题和表题单独成行，例如 `图 2-1 xxx`、`表 2-1 xxx`。
- 正文引用写作 `[1]`、`[1-3]`、`[1，3-4]`，导出器会尽量生成上标和文末跳转。
- 图片路径建议使用相对路径，例如 `img/pipeline.png`。

完整写法见 [docs/usage.md](docs/usage.md)，示例见 [example/README.md](example/README.md)。

## 公式支持

基础导出只需要 Python 和 Pillow。安装公式依赖后，LaTeX 公式会尽量转为 Word OMML；未安装时保留 LaTeX 文本。

## PDF 预览

DOCX 转 PDF：

```bash
python3 md2docx.py pdf thesis.docx thesis.pdf --backend word
python3 md2docx.py pdf thesis.docx thesis.pdf --backend libreoffice
```

后端：

| 后端 | 适用环境 | 定位 |
| --- | --- | --- |
| `word` | Windows / WSL + Microsoft Word | 高保真预览，最终验收基准 |
| `libreoffice` | Windows / Linux / WSL / CI | 无 Word 环境下快速预览 |
| `auto` | Windows / Linux / WSL | 优先选择可用的 `word`，否则使用 `libreoffice` |

Word 后端不需要设置 `WINWORD.EXE` 绝对路径。LibreOffice 更通用，但分页、字体和公式细节可能与 Word 不一致。

更多后端配置见 [docs/backends.md](docs/backends.md)。

## 支持范围

- [x] 适合新疆大学本科毕业论文正文写作和反复导出。
- [x] 适合 Git 管理论文源稿。
- [x] 适合 AI 修改 Markdown，再用 PDF 检查 Word 版式。
- [x] 适合继续扩展其他学校毕设论文模板。
- [ ] 不能替代最终 Word / WPS 人工检查。
- [ ] 不覆盖复杂浮动对象、脚注尾注、修订痕迹等深度 Word 排版。

## 扩展格式

论文格式规则通过 profile 组织：

| Profile | 说明 |
| --- | --- |
| `xju-undergraduate-thesis` | 新疆大学本科毕业论文（设计）格式 |

新增格式时，新建 `thesis_md2docx/profiles/<name>/` 并在 `thesis_md2docx/profiles/registry.py` 注册。

通用能力放在公共层；学校特有的封面、前置页、标题、页眉页脚、附录编号等放入 profile。

## 文档

- [docs/usage.md](docs/usage.md)：Markdown 写作约定。
- [docs/backends.md](docs/backends.md)：DOCX 转 PDF 后端、环境变量和排查。
- [example/README.md](example/README.md)：示例文件说明。
- [CONTRIBUTING.md](CONTRIBUTING.md)：开发和提交检查。
- [skill/SKILL.md](skill/SKILL.md)：面向 agent 的 skill 入口。

## Agent Skill

仓库内置 `skill/`，可复制到 Codex 或 Claude 的 skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -r skill ~/.codex/skills/thesis-md2docx
mkdir -p ~/.claude/skills
cp -r skill ~/.claude/skills/thesis-md2docx
```

如果 skill 不在仓库目录内，使用前设置：

```bash
export THESIS_MD2DOCX_REPO=/path/to/Thesis-md2docx
```

## 项目结构

```text
Thesis-md2docx/
├── md2docx.py                  # 跨平台统一入口
├── export-example.sh           # Linux / WSL 一键导出示例
├── export-example.ps1          # Windows PowerShell 一键导出示例
├── export-example.cmd          # Windows cmd 一键导出示例
├── thesis_md2docx/             # Markdown -> DOCX/PDF 核心代码
│   ├── profiles/               # 学校/格式 profile
│   │   └── xju_undergraduate_thesis/format_requirements/
│   ├── pdf/                    # DOCX -> PDF 后端
│   ├── math/                   # LaTeX -> OMML 公式转换
│   ├── builders/               # 文档结构构建
│   └── ooxml/                  # OOXML 渲染
├── docs/
├── example/
├── skill/                      # Agent skill
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 开发

提交改动前建议运行：

```bash
python3 -m py_compile md2docx.py $(find thesis_md2docx -name '*.py' -type f | sort)
python3 md2docx.py doctor
python3 md2docx.py docx example/thesis-demo.md /tmp/thesis-demo.docx --profile xju-undergraduate-thesis
```

如果修改了 PDF 后端，再按需运行：

```bash
python3 md2docx.py doctor --backend word
python3 md2docx.py doctor --backend libreoffice
```

## License

MIT
