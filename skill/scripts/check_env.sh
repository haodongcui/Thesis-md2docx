#!/usr/bin/env bash
set -euo pipefail

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

cd "$REPO"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

exec "$PYTHON" md2docx.py doctor "$@"
