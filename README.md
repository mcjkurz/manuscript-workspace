# manuscript-workspace

A compact workspace for researching, drafting, and rendering one academic
article or monograph chapter with an AI coding agent. Clone, rename, and
start writing.

> **Rename the folder** when you start a new project, and update the H1
> above to match.

## Quick start

```sh
# 1. Clone the repo and rename the folder for your project.
git clone https://github.com/mcjkurz/manuscript-workspace.git my-article && cd my-article

# 2. Install Python deps for the code/ environment.
python3 -m venv code/venv
code/venv/bin/pip install -r code/requirements.txt
```

Then:

1. **Rename the project.** Update the H1 at the top of this README to match
   your new folder name.
2. **Pick a manuscript format** (see below) and delete the other path's
   files.
3. **Install system prerequisites** (Quarto for DOCX; a TeX distribution
   with `latexmk` and `biber` for PDF). See Prerequisites below.
4. **Edit the canonical manuscript** (`manuscript/manuscript.md` by default)
   and `bibliography/references.bib`.
5. **Optionally drop style models** (articles, chapters, prior writing)
   into `style/` so the agent can match their voice and rhythm.
6. **Render:** `manuscript/render_docx.sh` (Markdown) or
   `manuscript/render_pdf.sh` (LaTeX). Output lands in `manuscript/output/`.
7. **Track issues** in `STATUS.md` and drop informal notes in `notes/`.

## Prerequisites

- **Markdown path (DOCX):** [Quarto](https://quarto.org/) (bundles pandoc)
  and a Python environment with `lxml`:
  ```sh
  python3 -m venv code/venv
  code/venv/bin/pip install -r code/requirements.txt
  ```
- **LaTeX path (PDF):** a TeX distribution (MacTeX / TeX Live) with
  `latexmk` and `biber`. The default engine is **xelatex** (native UTF-8
  and CJK font support). Override with `TEX_ENGINE=luatex` or
  `TEX_ENGINE=pdflatex` when invoking `manuscript/render_pdf.sh`; the
  `manuscript.tex` preamble detects the engine and loads `fontspec` under
  xelatex/luatex, falling back to `inputenc`/`fontenc` under pdflatex.

## Structure

| Path | Purpose |
| --- | --- |
| `manuscript/manuscript.md` | canonical editable text (Markdown path) |
| `manuscript/manuscript.tex` | optional LaTeX alternative |
| `manuscript/render_docx.sh` | Markdown → DOCX entry point |
| `manuscript/render_pdf.sh` | LaTeX → PDF entry point |
| `manuscript/rendering/` | Quarto wrapper, DOCX styles, CSL |
| `manuscript/figures/` | figures referenced from the manuscript |
| `manuscript/output/` | generated documents (git-ignored) |
| `manuscript/backups/` | per-session timestamped snapshots (see below) |
| `sources/original/` | original research material; never edit |
| `sources/processed/` | plain-text derivatives for searching |
| `style/` | reference texts exemplifying the target prose style |
| `style/processed/` | plain-text derivatives of style references |
| `notes/` | informal notes and excerpts |
| `bibliography/references.bib` | citation metadata |
| `code/` | optional scripts, data, experiments (delete if unused) |
| `STATUS.md` | current issues and next steps |
| `AGENTS.md` | instructions the agent follows on this repo |

## Choose a manuscript format

The repo ships with both a Markdown and a LaTeX path. Pick one and remove
the other.

- **Markdown (default).** Edit `manuscript/manuscript.md`. Render with
  `manuscript/render_docx.sh` (Quarto + pandoc). Delete
  `manuscript/manuscript.tex` and `manuscript/render_pdf.sh` if unused.
- **LaTeX.** Edit `manuscript/manuscript.tex`. Render with
  `manuscript/render_pdf.sh` (latexmk + biblatex). Delete
  `manuscript/manuscript.md`, `manuscript/render_docx.sh`, and the
  Quarto-specific files under `manuscript/rendering/` if unused.

If you switch, name the canonical file in `AGENTS.md` so the agent backs up
the right one.

## Render

```sh
manuscript/render_docx.sh   # Markdown → DOCX
manuscript/render_pdf.sh    # LaTeX    → PDF (default engine: xelatex)
TEX_ENGINE=pdflatex manuscript/render_pdf.sh   # override the engine
```

The generated document is disposable; the source manuscript remains
canonical. To match a target journal or press, swap
`manuscript/rendering/apa.csl` for the relevant CSL and edit the
`STYLE_CONFIG` dict in `manuscript/rendering/build_reference_docx.py` (or
the document class in `manuscript.tex`).

## Working with an agent

`AGENTS.md` tells the agent how to behave on this repo. It enforces three
things worth knowing up front:

- **Per-session backup.** At the start of each agent session, the canonical
  manuscript is copied to
  `manuscript/backups/manuscript-YYYY-MM-DD_HH-MM-SS.md` (or `.tex`). One
  backup per session, even if the manuscript is not changed.
- **No invention.** The agent will not invent sources, quotations, page
  numbers, dates, or identifiers. Unresolved points are marked `VERIFY`.
- **Propose then edit.** The agent proposes edits before applying them
  unless you have already authorized the change.

Edit `AGENTS.md` to match your project's conventions.
