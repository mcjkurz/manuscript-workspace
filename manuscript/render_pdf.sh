#!/usr/bin/env bash
# Render the LaTeX manuscript to PDF.
# Requires: a TeX distribution (e.g. MacTeX / TeX Live) with latexmk and
# biber. Install with your package manager or from https://www.tug.org/texlive/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

TEX_DIR="manuscript"
OUTPUT_DIR="manuscript/output"
OUTPUT_PDF="${OUTPUT_DIR}/article.pdf"

mkdir -p "${OUTPUT_DIR}"

# latexmk runs pdflatex + biber + pdflatex as many times as needed.
# -outdir keeps auxiliary files out of the source tree.
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir="${TEX_DIR}/build" \
  "${TEX_DIR}/manuscript.tex"

# Move the final PDF to the output directory.
cp "${TEX_DIR}/build/manuscript.pdf" "${OUTPUT_PDF}"

# Clean auxiliary files (comment out to inspect logs).
latexmk -C -outdir="${TEX_DIR}/build" "${TEX_DIR}/manuscript.tex" || true

echo "Rendered ${OUTPUT_PDF}"
