# Rendering utilities

Helpers for turning the canonical manuscript into a submission-ready
document.

## Markdown path (DOCX)

- `article.qmd`: Quarto wrapper that includes `../manuscript.md` and applies
  the bibliography and CSL.
- `apa.csl`: APA 7th edition citation style, included as a sensible default.
  Replace it with the CSL for your target journal or press
  (https://github.com/citation-style-language/styles).
- `build_reference_docx.py`: builds `reference.docx`, the deterministic
  style template that pandoc uses for DOCX output. Edit `STYLE_CONFIG` and
  the font constants at the top of the script to match your target style.
- `postprocess_docx.py`: cleans up the generated DOCX (table widths, image
  centering, reference list style). Edit `TABLE_RATIOS` to pin column
  proportions for specific tables.

Render with:

```sh
../render_docx.sh
```

## LaTeX path (PDF)

The LaTeX manuscript lives at `../manuscript.tex`. Render with:

```sh
../render_pdf.sh
```

Adjust the document class, fonts, and biblatex style in `../manuscript.tex`
to match your target journal or press.

## Required tools

- Markdown path: [Quarto](https://quarto.org/) and a Python environment with
  `lxml` (see `code/requirements.txt`).
- LaTeX path: a TeX distribution (MacTeX / TeX Live) with `latexmk` and
  `biber`.
