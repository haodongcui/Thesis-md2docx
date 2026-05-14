#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <input.docx> <output.pdf> [backend] [extra md2docx args...]" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -n "${THESIS_MD2DOCX_REPO:-}" ]; then
  REPO="$THESIS_MD2DOCX_REPO"
elif [ -f "$PWD/md2docx.py" ]; then
  REPO="$PWD"
elif [ -f "$SCRIPT_DIR/../../md2docx.py" ]; then
  REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
  echo "Cannot locate md2docx.py. Set THESIS_MD2DOCX_REPO=/path/to/Thesis-md2docx." >&2
  exit 2
fi

INPUT="$1"
OUTPUT="$2"
shift 2
if [[ "$INPUT" != /* ]]; then
  INPUT="$PWD/$INPUT"
fi
if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PWD/$OUTPUT"
fi

BACKEND="${1:-${THESIS_DOCX2PDF_BACKEND:-word}}"
if [ "$#" -gt 0 ]; then
  shift
fi

cd "$REPO"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

exec "$PYTHON" md2docx.py pdf "$INPUT" "$OUTPUT" --backend "$BACKEND" "$@"
