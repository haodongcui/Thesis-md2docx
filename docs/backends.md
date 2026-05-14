# PDF Backend Guide

本文档说明 DOCX 转 PDF 的可选后端。生成 DOCX 不需要 PDF 后端；PDF 主要用于人工或 AI 预览 Word 版式。

## 后端选择

| 后端 | 适用系统 | 定位 | 说明 |
| --- | --- | --- | --- |
| `word` | Windows / WSL | 高保真预览和最终格式验收 | 通过 Microsoft Word COM 自动化导出 PDF，最接近 Word 打开效果 |
| `libreoffice` | Windows / Linux / WSL / CI | 快速预览 | 使用 LibreOffice headless 导出，更通用，但分页和字体细节可能不同 |
| `auto` | Windows / Linux / WSL | 自动选择 | 优先使用可用的 `word`，否则使用 `libreoffice` |

推荐：

- 最终格式验收优先使用 `word`。
- 没有 Microsoft Word 时，用 `libreoffice` 做快速预览。
- 如果只是生成 DOCX，不需要配置任何 PDF 后端。

## 通用命令

检查核心环境：

```bash
md2docx check
```

检查 PDF 后端：

```bash
md2docx check --backend auto
md2docx check --backend word
md2docx check --backend libreoffice
```

Markdown 生成 DOCX 和 PDF：

```bash
md2docx thesis.md --pdf --out output --backend word
md2docx thesis.md --pdf --out output --backend libreoffice
```

Markdown 生成 DOCX、PDF 和分页图片：

```bash
md2docx thesis.md --pdf --pages --out output --backend auto
```

## Word 后端

Word 后端通过 Windows COM 注册名 `Word.Application` 启动 Microsoft Word，不需要配置 `WINWORD.EXE` 的绝对路径。

适用环境：

- 原生 Windows + Microsoft Word
- WSL + Windows 侧 Microsoft Word + WSL interop

WSL 下可运行：

```bash
md2docx check --backend word
md2docx pdf thesis.docx thesis.pdf --backend word
```

如果临时目录需要指定到 Windows 本地磁盘：

```bash
md2docx pdf thesis.docx thesis.pdf --backend word --tmp-root /mnt/c/Temp/thesis-word-docx2pdf
```

Windows PowerShell：

```powershell
md2docx pdf thesis.docx thesis.pdf --backend word --tmp-root C:\Temp\thesis-word-docx2pdf
```

常见依赖：

- PowerShell
- `cscript`
- WSL 下需要 `wslpath`
- Windows 侧 Microsoft Word 能正常启动并完成首次授权

常用变量：

| 变量 | 作用 |
| --- | --- |
| `THESIS_WORD_DOCX2PDF_TMP_ROOT` | Word 后端临时目录，WSL 下建议指向 Windows 本地磁盘 |
| `THESIS_WORD_DOCX2PDF_VBS_TEMPLATE` | 覆盖内置 Word VBS 导出脚本 |
| `THESIS_WORD_DOCX2PDF_UPDATE_FIELDS=0` | 导出前不刷新域 |
| `THESIS_WORD_DOCX2PDF_KEEP_TMP=1` | 保留临时文件，便于排查 |
| `THESIS_WORD_DOCX2PDF_SKIP_WORD_CHECK=1` | 跳过前置 COM 可用性检查 |

如果 `check` 显示 Word COM 不可用，优先检查：

- Windows 侧 Word 是否安装并能手动打开。
- Word 是否还有首次启动、登录、授权或隐私弹窗。
- PowerShell 中是否能创建 `Word.Application` COM 对象。
- WSL 是否能访问 Windows 可执行环境。

## LibreOffice 后端

LibreOffice 后端使用 `soffice` headless 模式。它更容易在 Linux、WSL 和 CI 中使用，但渲染逻辑与 Microsoft Word 不完全一致。

安装示例：

```bash
sudo apt-get update
sudo apt-get install -y libreoffice
```

检查和导出：

```bash
md2docx check --backend libreoffice
md2docx pdf thesis.docx thesis.pdf --backend libreoffice
```

如果 `soffice` 不在 PATH 中，可以指定路径：

```bash
md2docx pdf thesis.docx thesis.pdf --backend libreoffice --soffice /path/to/soffice
```

或使用环境变量：

```bash
export THESIS_LIBREOFFICE_BIN=/path/to/soffice
```

常用变量：

| 变量 | 作用 |
| --- | --- |
| `THESIS_LIBREOFFICE_BIN` | 指定 LibreOffice/soffice 可执行文件 |
| `THESIS_LIBREOFFICE_DOCX2PDF_TMP_ROOT` | LibreOffice 后端临时目录 |
| `THESIS_LIBREOFFICE_DOCX2PDF_UPDATE_FIELDS=0` | 导出前不刷新域，改用纯 `--convert-to` |
| `THESIS_LIBREOFFICE_DOCX2PDF_FONT_SUBSTITUTION=0` | 关闭字体替换尝试 |
| `THESIS_LIBREOFFICE_DOCX2PDF_KEEP_TMP=1` | 保留临时文件和日志 |

当前实现会尽力做中文字体映射，例如：

- `宋体 -> SimSun`
- `黑体 -> SimHei`
- `楷体_GB2312 -> KaiTi`
- `仿宋 -> FangSong`

这只能改善 LibreOffice 预览效果，不能保证与 Word 完全一致。分页、目录位置、公式和字体 fallback 仍可能不同。

## PDF 转图片预览

如果需要让 AI 或人工逐页检查版式，可以用 `pdftoppm` 把 PDF 渲染成 PNG：

```bash
mkdir -p pages
pdftoppm -png -f 1 -l 6 -r 120 thesis.pdf pages/page
```

Ubuntu / Debian：

```bash
sudo apt-get install -y poppler-utils
```

`md2docx check` 会检查 `pdftoppm` 是否可用，但它不是生成 DOCX/PDF 的必要依赖。

## WPS 和其他后端

WPS 后端目前没有实现。可行方向包括：

- `wps-local-windows`：研究 Windows WPS 是否有稳定 COM/自动化接口。
- `wps-local-linux`：研究 Linux WPS 是否有稳定命令行导出 PDF。
- `wps-cloud`：接 WPS WebOffice 文档转换 API，但需要账号、鉴权和上传文件。

后续新增后端时，建议新增：

```text
thesis_md2docx/pdf/backends/<backend_name>/
```

然后在 `thesis_md2docx/pdf/registry.py` 注册。新增后端应实现：

- `convert()`
- `doctor()`
- `available()`

## 验收建议

- 学校最终提交格式以 Word/WPS 人工检查为准。
- 如果 Word 和 LibreOffice PDF 不一致，以 Word 后端为格式验收基准。
- 每次改动标题、分节、页眉页脚、目录、公式、图表或参考文献后，都应重新导出 DOCX 和 PDF。
- 自动化导出不能替代最终人工检查。
