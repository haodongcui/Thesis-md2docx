# xju-thesis-md2docx

新疆大学本科毕业论文（设计）`Markdown -> DOCX` 格式转换工具。

本项目面向希望用 Markdown 维护论文主稿、再导出为学校格式 Word 文档的写作流程。当前实现不依赖 Word 模板包替换，而是直接生成原生 OOXML `docx` 文件，并提供可选的 DOCX 转 PDF 后端，方便检查分页、目录、公式、图表和整体版式。

## 功能

- 从 Markdown 主稿生成新疆大学本科毕业论文（设计）DOCX。
- 自动生成封面、原创性声明、任务书、中英文摘要、目录域、正文、参考文献、致谢和附录。
- 写入学校论文格式所需的页面边距、页眉页脚、页码、标题、正文、题注、表格、公式和参考文献样式。
- 正文章节使用 Word 原生编号，不把章节号硬编码进标题文本。
- 支持一级到三级标题、行内公式、块公式、Markdown 管道表格、长表拆分、单图、并排图、引用块和代码块。
- 支持 LaTeX 公式转换为 Word 原生 OMML；依赖缺失时保留 LaTeX 文本并给出 warning。
- 可选调用 Windows Microsoft Word 或 LibreOffice 将 DOCX 导出为 PDF，用于人工或 AI 预览排版效果。

## 当前状态

- `Markdown -> DOCX` 是跨平台 Python 实现，不依赖学校 Word 模板包替换。
- `DOCX -> PDF` 已抽象为可选后端，当前支持 `word` 和 `libreoffice`。
- 统一入口是 `xju.py`；Linux / WSL 使用 `xju.sh`，Windows PowerShell 使用 `xju.ps1`，Windows cmd 使用 `xju.cmd`。
- Word 后端在原生 Windows 和 WSL 中可用，使用 Microsoft Word COM 自动化，当前是格式验收推荐后端。
- LibreOffice 后端在 Windows / Linux / WSL 中可用，适合无 Word 环境快速预览，但分页和细节不保证与 Word 完全一致。
- WPS 尚未接入。后续可以作为新 PDF 后端扩展，但需要先确认本地 WPS 是否有稳定命令行或自动化接口。

## 适用范围

适合：

- 新疆大学本科毕业论文（设计）正文写作和反复导出。
- 希望把论文源文件纳入 Git 版本管理的场景。
- 希望由 AI 修改 Markdown，并通过生成 PDF 图片检查 Word 版式效果的流程。
- 需要一个无需学校 DOCX 模板包替换的开源实现。

不适合：

- 完全跳过 Word / WPS 最终检查后直接提交。
- 复杂浮动对象、脚注尾注、修订痕迹、自动交叉题注等深度 Word 排版场景。
- 评议书、答辩委员会意见等过程性材料的整包合并。

## 安装

### Python 依赖

Linux / WSL：

```bash
git clone https://github.com/<your-name>/xju-thesis-md2docx.git
cd xju-thesis-md2docx
python3 -m pip install -r requirements.txt
```

Windows PowerShell：

```powershell
git clone https://github.com/<your-name>/xju-thesis-md2docx.git
cd xju-thesis-md2docx
py -3 -m pip install -r requirements.txt
```

最小依赖只需要 Python 和 Pillow，可以完成正文、封面、图片、表格、目录域和基础公式文本导出。

### 公式转换依赖

如果希望 LaTeX 公式尽量转换为 Word 原生公式，需要安装 Node.js 依赖：

```bash
cd xju_thesis_md2docx/world-math
npm install
```

公式依赖是可选项。没有安装时，导出不会失败，公式会以 LaTeX 文本形式写入 Word，并在命令行提示 warning。

### PDF 预览依赖

PDF 预览不是生成 DOCX 的必要条件。当前支持两个后端：

| 后端 | 适用环境 | 特点 |
| --- | --- | --- |
| `word` | Windows / WSL + Windows Microsoft Word | 默认高保真后端，最接近 Word 打开效果 |
| `libreoffice` | Windows / Linux / WSL / CI | 不依赖 Word，更通用，但版式可能与 Word 有差异 |

Word 后端诊断：

```bash
./xju.sh doctor --backend word
```

Windows PowerShell：

```powershell
.\xju.ps1 doctor --backend word
```

LibreOffice 后端诊断：

```bash
./xju.sh doctor --backend libreoffice
```

Ubuntu / Debian 可安装 LibreOffice：

```bash
sudo apt-get update
sudo apt-get install -y libreoffice
```

两个后端都不需要 Docker，也不需要 `docker pull`。

## 统一入口

```text
xju docx <input.md> [output.docx]
xju pdf <input.docx> [output.pdf] --backend word|libreoffice|auto
xju all <input.md> [output.docx] [output.pdf] --backend word|libreoffice|auto
xju doctor --backend word|libreoffice|auto
xju list-backends
```

不同系统只换启动器：

| 系统 | 启动器 | 示例 |
| --- | --- | --- |
| Linux / WSL | `./xju.sh` | `./xju.sh all thesis.md thesis.docx thesis.pdf --backend auto` |
| Windows PowerShell | `.\xju.ps1` | `.\xju.ps1 all thesis.md thesis.docx thesis.pdf --backend word` |
| Windows cmd | `xju.cmd` | `xju.cmd docx thesis.md thesis.docx` |
| 任意系统 | `python xju.py` | `python xju.py docx thesis.md thesis.docx` |

如果 PowerShell 执行策略拦截本地脚本，可以临时使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\xju.ps1 doctor --backend auto
```

## 快速开始

Linux / WSL 运行内置示例：

```bash
./xju.sh docx example/thesis-demo.md example/thesis-demo.generated.docx
```

Windows PowerShell：

```powershell
.\xju.ps1 docx example\thesis-demo.md example\thesis-demo.generated.docx
```

如果 PowerShell 执行策略拦截本地脚本，可以临时用：

```powershell
powershell -ExecutionPolicy Bypass -File .\xju.ps1 docx example\thesis-demo.md example\thesis-demo.generated.docx
```

Windows cmd：

```bat
xju.cmd docx example\thesis-demo.md example\thesis-demo.generated.docx
```

旧的 `bash demo.sh` 仍然可用。

导出自己的论文：

```bash
./xju.sh docx thesis.md thesis.docx
```

如果不传输出路径，默认生成同名 `.docx`：

```bash
./xju.sh docx thesis.md
```

常用参数：

```bash
./xju.sh docx thesis.md thesis.docx --assets-dir path/to/cover-assets
./xju.sh docx thesis.md thesis.docx --no-cover-assets
./xju.sh docx thesis.md thesis.docx --no-formula-conversion
```

`python3 xju_thesis_md2docx.py thesis.md thesis.docx` 这个底层入口也保留。

封面默认使用仓库内置资源：

```text
xju_thesis_md2docx/resources/xju-emblem.jpeg
xju_thesis_md2docx/resources/xju-wordmark.png
```

也可以在论文 Markdown 同级目录下放置本地资源，优先覆盖默认封面图：

```text
img/cover-assets/xju-emblem.jpeg
img/cover-assets/xju-wordmark.png
```

## PDF 预览

生成 DOCX 后，可以继续导出 PDF：

```bash
./xju.sh pdf example/thesis-demo.generated.docx example/thesis-demo.generated.pdf --backend word
```

使用 LibreOffice 后端：

```bash
./xju.sh pdf example/thesis-demo.generated.docx example/thesis-demo.generated.pdf --backend libreoffice
```

从 Markdown 一步生成 DOCX 和 PDF：

```bash
./xju.sh all thesis.md thesis.docx thesis.pdf --backend auto
```

Windows PowerShell 对应用法：

```powershell
.\xju.ps1 pdf thesis.docx thesis.pdf --backend word
.\xju.ps1 all thesis.md thesis.docx thesis.pdf --backend auto
```

如果要让 AI 或人工逐页检查版式，可以把 PDF 渲染成图片：

```bash
mkdir -p example/preview/thesis-demo
pdftoppm -png -f 1 -l 6 -r 120 \
  example/thesis-demo.generated.pdf \
  example/preview/thesis-demo/page
```

`xju.py` 是跨平台统一入口；`xju.sh`、`xju.ps1`、`xju.cmd` 只是不同系统上的启动器。`tools/docx2pdf/` 仍然提供底层 PDF 调度入口；实际后端资源位于 `tools/docx2pdf/backends/word/` 和 `tools/docx2pdf/backends/libreoffice/`。`tools/word-docx2pdf/`、`tools/libreoffice-docx2pdf/` 只是旧路径兼容入口。

Word 后端支持原生 Windows 和 WSL。它通过 Windows COM 注册名 `Word.Application` 启动 Microsoft Word，不需要设置 `WINWORD.EXE` 的绝对路径。确实需要指定临时目录时，可以使用：

```bash
./xju.sh pdf thesis.docx thesis.pdf --backend word --tmp-root /mnt/c/Temp/xju-word-docx2pdf
```

Windows PowerShell 示例：

```powershell
.\xju.ps1 pdf thesis.docx thesis.pdf --backend word --tmp-root C:\Temp\xju-word-docx2pdf
```

也可以参考环境变量示例：

```text
tools/docx2pdf/env.example
```

格式验收建议以 `word` 后端为准；`libreoffice` 后端更适合无 Word 环境下快速预览。

## PDF 后端

| 后端 | 适用系统 | 当前定位 | 已知效果 |
| --- | --- | --- | --- |
| `word` | Windows / WSL | 高保真预览和最终格式验收 | 与 Microsoft Word 打开/导出的效果一致；当前真实论文为 34 页 |
| `libreoffice` | Windows / Linux / WSL / CI | 无 Word 环境快速预览 | 可刷新目录/字段并导出；当前真实论文为 33 页，分页与 Word 不一致 |
| `auto` | Windows / Linux / WSL | 自动选择可用后端 | 优先 `word`，否则 `libreoffice` |

Word 后端不需要设置 `WINWORD.EXE` 绝对路径。它通过 Windows COM 注册名 `Word.Application` 启动 Word；如果 `doctor` 检查失败，通常要修复 Windows 侧 Word/Office 安装、首次启动授权弹窗或 COM 注册状态。

LibreOffice 后端使用 `soffice` headless 模式。默认会用临时 profile 打开文档，刷新目录、索引和文本域，再导出 PDF；`--no-update-fields` 可切换到纯 `--convert-to` 模式。导出时还会默认注入临时字体替换表，并改写临时 DOCX 副本中的字体名，尝试把 `宋体 -> SimSun`、`黑体 -> SimHei`、`楷体_GB2312 -> KaiTi` 等中文字体名映射到系统字体。可以用 `XJU_LIBREOFFICE_DOCX2PDF_FONT_SUBSTITUTION=0` 关闭该尝试。该优化是尽力而为：当前测试环境中 `SimHei` 和 `KaiTi` 能进入 LibreOffice PDF，但 `SimSun` 仍会被 LibreOffice 7.3 回退为 `UMingCN`，分页仍与 Word 不一致。

WPS 后端目前未实现。可行方向包括：

- `wps-local-windows`：研究 Windows WPS 是否有稳定 COM/自动化接口；
- `wps-local-linux`：研究 Linux WPS 是否有稳定 CLI 导出 PDF；
- `wps-cloud`：接 WPS WebOffice 文档转换 API，但需要账号、鉴权和上传文件，不适合作为默认本地后端。

后续如接入 WPS，只需要新增一个 `xju_thesis_md2docx/pdf/wps.py` 后端模块，并在 `xju_thesis_md2docx/pdf/registry.py` 注册。

当前文档集中维护在本 `README.md`。子目录中的 README 只保留底层入口说明和兼容说明，日常使用以本文件为准。

## Markdown 结构

推荐从 `example/thesis-demo.md` 复制结构，再替换为自己的论文内容。核心结构如下：

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

约定：

- 正文从第一个编号一级标题开始，例如 `# 1 绪论`。
- 前置部分使用二级标题组织，例如 `## 封面信息`、`## 摘要`。
- 图题、表题建议单独成行，例如 `图 2-1 xxx`、`表 2-1 xxx`。
- 正文引用写作 `[1]`、`[1-3]`、`[1，3-4]`，导出器会尽量生成上标和文末跳转。
- 长表可以在表题和表格之间写 `<!-- xju-table-split: 8, 10 -->`，按数据行拆分续表。
- 并排图使用 `:::figure-row` 容器，见示例文件。

更多写法见：

- `example/README.md`
- `example/thesis-demo.md`
- `tools/docx2pdf/README.md`

## 格式对齐状态

当前实现已经按新疆大学本科毕业论文（设计）规范和范例重点对齐以下内容：

- A4 页面、页边距、页眉页脚、正文页码；
- 封面、声明、任务书、中英文摘要、目录、正文、参考文献、致谢、附录的文档顺序；
- 一级、二级、三级标题的字体、字号、缩进、段前段后和目录级别；
- 正文段落小四宋体、首行缩进两字符、1.5 倍行距；
- 图题、表题、表格文字、参考文献悬挂缩进；
- 公式块编号、常见 `\hat{}`、`\bar{}` 重音公式后处理；
- 正文参考文献引用上标和链接。

仍建议最终提交前人工检查：

- 在 Word / WPS 中刷新目录域和页码；
- 检查分页、孤行、图片位置、表格跨页和公式显示；
- 按学院或指导教师的额外要求调整非统一部分；
- 核对参考文献真实性和 GB/T 7714 细节。

## 项目结构

```text
xju-thesis-md2docx/
├── xju_thesis_md2docx.py              # 公开入口
├── xju.py                             # 跨平台统一入口
├── xju.sh                             # Linux / WSL 启动器
├── xju.ps1                            # Windows PowerShell 启动器
├── xju.cmd                            # Windows cmd 启动器
├── xju_thesis_md2docx/
│   ├── main.py                        # CLI 参数解析
│   ├── exporter.py                    # Markdown -> DOCX 编排入口
│   ├── builders/                      # 文档结构和内容块构建
│   ├── ooxml/                         # OOXML 段落、表格、图片、页眉页脚等渲染
│   ├── math/                          # LaTeX -> OMML 转换封装
│   ├── pdf/                           # 跨平台 DOCX -> PDF 调度和后端控制
│   │   ├── registry.py                # PDF 后端注册表
│   │   ├── word.py                    # Microsoft Word PDF 后端
│   │   └── libreoffice.py             # LibreOffice PDF 后端
│   ├── resources/                     # 默认封面资源
│   └── world-math/                    # LaTeX -> OMML helper
├── example/
│   ├── README.md
│   ├── thesis-demo.md
│   └── img/
├── tools/
│   ├── docx2pdf/                      # PDF 后端统一入口和实际后端实现
│   │   ├── docx2pdf.sh                # Linux / WSL wrapper
│   │   ├── docx2pdf.ps1               # Windows PowerShell wrapper
│   │   ├── docx2pdf.cmd               # Windows cmd wrapper
│   │   └── backends/
│   │       ├── word/                  # Windows / WSL Word PDF 后端
│   │       └── libreoffice/           # LibreOffice PDF 后端
│   ├── word-docx2pdf/                 # 旧路径兼容入口
│   └── libreoffice-docx2pdf/          # 旧路径兼容入口
├── demo.sh
├── requirements.txt
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## 开发与贡献

本项目以 Markdown 为源文件，DOCX/PDF 是生成物。提交改动时建议：

```bash
python3 -m py_compile xju.py xju_thesis_md2docx.py $(find xju_thesis_md2docx -name '*.py' -type f | sort)
bash demo.sh
./xju.sh all example/thesis-demo.md /tmp/thesis-demo.docx /tmp/thesis-demo.pdf --backend libreoffice
```

如果修改了 Word PDF 后端，在 Windows 或 WSL + Word 环境下再运行：

```bash
./xju.sh doctor --backend word
./xju.sh pdf example/thesis-demo.generated.docx example/thesis-demo.generated.pdf --backend word
```

如果修改了 LibreOffice 后端，再运行：

```bash
./xju.sh doctor --backend libreoffice
./xju.sh pdf example/thesis-demo.generated.docx example/thesis-demo.generated.pdf --backend libreoffice
```

欢迎围绕以下方向贡献：

- 更完整的学校格式细节对齐；
- LibreOffice / OnlyOffice 等可选 PDF 后端；
- 更稳健的公式、图表、引用和附录处理；
- 更小、更清晰的示例和测试文档。

更详细的提交约定见 `CONTRIBUTING.md`。

## License

MIT
