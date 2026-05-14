---
name: thesis-md2docx
description: Use this skill when an agent needs to write, check, or export thesis Markdown with the thesis-md2docx repository, especially Xinjiang University undergraduate thesis Markdown to DOCX/PDF workflows. Covers environment checks, Markdown structure, formula conversion, PDF backend choice, and final layout verification.
---

# Thesis MD2DOCX Skill

Use this skill when the user wants an agent to work with a thesis maintained as Markdown and exported with the `thesis-md2docx` repository.

Prefer Markdown as the source of truth. Treat DOCX/PDF files as generated outputs.

## Repository

Expected repository:

```text
https://github.com/haodongcui/Thesis-md2docx
```

If the current working directory is not the repository root, set:

```bash
export THESIS_MD2DOCX_REPO=/path/to/Thesis-md2docx
```

If the repository is missing, clone it first:

```bash
git clone https://github.com/haodongcui/Thesis-md2docx.git
```

## Workflow

1. Locate the repository root. It must contain `md2docx.py`.
2. Check the environment:

   ```bash
   bash scripts/check_env.sh
   ```

3. If the Markdown contains formulas, make sure the formula helper is installed:

   ```bash
   npm install --prefix thesis_md2docx/math/latex2omml_node
   ```

4. Check the source Markdown structure. Load `references/markdown-usage.md` when the document is missing front matter, numbered chapters, references, figures, tables, or appendices.
5. Export DOCX:

   ```bash
   md2docx thesis.md --out output --profile xju-undergraduate-thesis
   ```

6. Export PDF and page images when layout preview is needed:

   ```bash
   md2docx thesis.md --pdf --pages --out output --profile xju-undergraduate-thesis --backend auto
   ```

7. For the repository example, `./export-example.sh` / `.ps1` / `.cmd` should produce `example/output/thesis-demo.docx`, `example/output/thesis-demo.pdf`, and `example/output/pages/page-*.png`.
8. Use the Word backend as the final layout baseline when available. Use LibreOffice for quick preview only.
9. Remind the user that final Word/WPS inspection is still required for TOC refresh, pagination, figures, tables, formulas, and references.

## References

- `references/markdown-usage.md`: Markdown writing conventions and minimal structure.
- `references/pdf-backends.md`: Word, LibreOffice, and auto PDF backend guidance.
- `references/troubleshooting.md`: common warnings, formula dependency issues, and layout checks.

## Operating Rules

- Do not hand-edit generated DOCX as the long-term source.
- Fix Markdown, profile code, or exporter code instead.
- Keep generated DOCX/PDF files and preview images out of Git; prefer source files at the paper root and generated files under `output/`.
- For Xinjiang University undergraduate thesis output, use profile `xju-undergraduate-thesis`.
- When comparing output, focus first on page sections, headings, body indentation, captions, formulas, references, and PDF pagination.
