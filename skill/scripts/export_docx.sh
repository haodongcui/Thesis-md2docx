#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <input.md> [output.docx] [extra md2docx args...]" >&2
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
shift

ARGS=(docx "$INPUT")

if [ "$#" -gt 0 ] && [[ "$1" != --* ]]; then
  ARGS+=("$1")
  shift
fi

HAS_PROFILE=0
for arg in "$@"; do
  if [ "$arg" = "--profile" ]; then
    HAS_PROFILE=1
    break
  fi
done

if [ "$HAS_PROFILE" -eq 0 ]; then
  ARGS+=(--profile "${THESIS_MD2DOCX_PROFILE:-xju-undergraduate-thesis}")
fi

ARGS+=("$@")

cd "$REPO"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

exec "$PYTHON" md2docx.py "${ARGS[@]}"
