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

"$PYTHON" md2docx.py docx \
  example/thesis-demo.md \
  example/thesis-demo.generated.docx \
  --profile xju-undergraduate-thesis

echo "Generated: $ROOT/example/thesis-demo.generated.docx"
