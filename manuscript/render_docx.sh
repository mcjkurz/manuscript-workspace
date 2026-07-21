#!/usr/bin/env bash
# Render the Markdown manuscript to DOCX.
# Requires: quarto (https://quarto.org/) and a Python environment with lxml.
# Create the environment with:
#   python3 -m venv code/venv
#   code/venv/bin/pip install -r code/requirements.txt
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

RENDER_DIR="manuscript/rendering"
OUTPUT_DIR="manuscript/output"
OUTPUT_DOCX="${OUTPUT_DIR}/article.docx"

mkdir -p "${OUTPUT_DIR}"

# Build (or refresh) the reference DOCX that pins paragraph and font styles.
if [ -x "${RENDER_DIR}/build_reference_docx.py" ]; then
  if [ -x "code/venv/bin/python" ]; then
    PY="code/venv/bin/python"
  else
    PY="python3"
  fi
  "${PY}" "${RENDER_DIR}/build_reference_docx.py" \
    --docx "${RENDER_DIR}/reference.docx"
fi

quarto render "${RENDER_DIR}/article.qmd" --to docx
mv "${RENDER_DIR}/article.docx" "${OUTPUT_DOCX}"

# Optional post-processing of the generated DOCX (table widths, captions, etc.).
if [ -x "${RENDER_DIR}/postprocess_docx.py" ]; then
  if [ -x "code/venv/bin/python" ]; then
    PY="code/venv/bin/python"
  else
    PY="python3"
  fi
  "${PY}" "${RENDER_DIR}/postprocess_docx.py" --docx "${OUTPUT_DOCX}"
fi

echo "Rendered ${OUTPUT_DOCX}"
