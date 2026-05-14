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
md2docx check --backend auto
md2docx thesis.md --pdf --out output --backend word
md2docx thesis.md --pdf --out output --backend libreoffice
md2docx thesis.md --pdf --pages --out output --backend auto
```

Windows can use:

```powershell
md2docx thesis.md --pdf --out output --backend word
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

The repository example launchers generate DOCX, PDF, and page images under `example/output/` automatically:

```bash
./export-example.sh
```
