#!/usr/bin/env bash
# Render the LaTeX manuscript to PDF.
# Requires: a TeX distribution (e.g. MacTeX / TeX Live) with latexmk and
# biber. Install with your package manager or from https://www.tug.org/texlive/.
#
# Engine selection (default: xelatex):
#   TEX_ENGINE=xelatex  manuscript/render_pdf.sh   # best for CJK / full UTF-8
#   TEX_ENGINE=luatex   manuscript/render_pdf.sh
#   TEX_ENGINE=pdflatex manuscript/render_pdf.sh
# The manuscript.tex preamble detects the engine via the iftex package and
# loads fontspec only under xelatex/luatex, so any of the three works.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

TEX_DIR="manuscript"
OUTPUT_DIR="manuscript/output"
OUTPUT_PDF="${OUTPUT_DIR}/article.pdf"

ENGINE="${TEX_ENGINE:-xelatex}"
case "${ENGINE}" in
  xelatex) LATEXMK_FLAG="-xelatex" ;;
  luatex)  LATEXMK_FLAG="-lualatex" ;;
  pdflatex) LATEXMK_FLAG="-pdf" ;;
  *)
    echo "Unknown TEX_ENGINE='${ENGINE}'. Use xelatex, luatex, or pdflatex." >&2
    exit 1
    ;;
esac

mkdir -p "${OUTPUT_DIR}"

# latexmk runs the selected engine + biber + the engine again as needed.
# -outdir keeps auxiliary files out of the source tree.
latexmk ${LATEXMK_FLAG} -interaction=nonstopmode -halt-on-error \
  -outdir="${TEX_DIR}/build" \
  "${TEX_DIR}/manuscript.tex"

# Move the final PDF to the output directory.
cp "${TEX_DIR}/build/manuscript.pdf" "${OUTPUT_PDF}"

# Clean auxiliary files (comment out to inspect logs).
latexmk -C -outdir="${TEX_DIR}/build" "${TEX_DIR}/manuscript.tex" || true

echo "Rendered ${OUTPUT_PDF} (engine: ${ENGINE})"
