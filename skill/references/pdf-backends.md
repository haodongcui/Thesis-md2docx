# PDF Backends

DOCX generation does not require a PDF backend. PDF export is for layout preview.

## Backend Choice

| Backend | Use case | Notes |
| --- | --- | --- |
| `word` | Final layout check | Uses Microsoft Word COM. Best match for Word output. |
| `libreoffice` | Quick preview / Linux / CI | More portable. Pagination and fonts can differ from Word. |
| `auto` | Convenience | Uses `word` when available, otherwise `libreoffice`. |

## Commands

```bash
python3 md2docx.py doctor --backend auto
python3 md2docx.py pdf thesis.docx thesis.pdf --backend word
python3 md2docx.py pdf thesis.docx thesis.pdf --backend libreoffice
python3 md2docx.py all thesis.md thesis.docx thesis.pdf --profile xju-undergraduate-thesis --backend auto
```

Windows can use:

```powershell
py -3 md2docx.py pdf thesis.docx thesis.pdf --backend word
```

## Word Backend

- Works on native Windows with Microsoft Word.
- Works from WSL when Windows interop and Word COM are available.
- Does not need a `WINWORD.EXE` absolute path.
- Use `--tmp-root /mnt/c/Temp/thesis-word-docx2pdf` when WSL temporary paths cause trouble.

## LibreOffice Backend

- Requires `soffice`.
- Can be selected with `--backend libreoffice`.
- If `soffice` is not in PATH, pass `--soffice /path/to/soffice` or set `THESIS_LIBREOFFICE_BIN`.
- Treat output as preview, not final proof, when it differs from Word.

## Preview Images

Use `pdftoppm` to render PDF pages into PNG for visual checking:

```bash
mkdir -p pages
pdftoppm -png -f 1 -l 6 -r 120 thesis.pdf pages/page
```
