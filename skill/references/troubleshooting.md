# Troubleshooting

## Environment

Run:

```bash
bash scripts/check_env.sh
```

or directly:

```bash
md2docx check
md2docx check --backend auto
```

If `python` is missing on Linux, use `python3`.

## Formula Conversion

Problem: formulas export as LaTeX text.

Fix:

```bash
npm install --prefix thesis_md2docx/math/latex2omml_node
md2docx check
```

Complex formulas and accent commands such as `\hat{}` or `\bar{}` still need final Word/WPS inspection.

## Word Backend

Problem: `word` backend fails.

Check:

- Windows Microsoft Word is installed.
- Word can open manually without first-run, login, authorization, or privacy popups.
- PowerShell can create `Word.Application`.
- WSL can call Windows executables.
- Try setting `--tmp-root /mnt/c/Temp/thesis-word-docx2pdf`.

## LibreOffice Backend

Problem: LibreOffice PDF differs from Word.

This is expected. LibreOffice has different font fallback, layout, field refresh, and formula rendering behavior. Use Word as final baseline when available.

## Final Checks

Before submission, inspect in Word/WPS:

- TOC and page numbers refreshed.
- Headings and section breaks.
- Body indentation and line spacing.
- Figure and table captions.
- Table page breaks.
- Formula rendering.
- Reference formatting and citation links.
