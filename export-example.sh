#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ -f "$ROOT/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  PYTHON=python
fi

PDF_BACKEND="${THESIS_DOCX2PDF_BACKEND:-auto}"
PREVIEW_DPI="${THESIS_PDF_PREVIEW_DPI:-120}"
OUTPUT_DIR="example/output"

"$PYTHON" md2docx.py \
  example/thesis-demo.md \
  --pdf \
  --pages \
  --out "$OUTPUT_DIR" \
  --profile xju-undergraduate-thesis \
  --backend "$PDF_BACKEND" \
  --dpi "$PREVIEW_DPI"

echo "Generated: $ROOT/$OUTPUT_DIR/thesis-demo.docx"
echo "Generated: $ROOT/$OUTPUT_DIR/thesis-demo.pdf"
echo "Generated PDF pages: $ROOT/$OUTPUT_DIR/pages/page-*.png"
