# Style references

Drop reference texts here that exemplify the prose style the manuscript
should imitate: published articles, book chapters, the author's own prior
writing, style guides, or any passage whose voice, register, sentence
rhythm, or argumentative shape is worth modeling.

- Accepted formats: `.txt`, `.md`, `.pdf`, `.docx`, `.epub`, etc.
- Non-plain-text files are converted to `.txt` under `style/processed/`
  following the same rules as `sources/` (see AGENTS.md): no OCR, preserve
  page markers where stable, regenerate when the original changes.
- These files are **style models, not evidence**. The agent consults them
  to match voice and rhythm; it must not cite them as sources or quote
  them into the manuscript unless the user explicitly asks.
- **Keep full files out of the agent's context.** The agent maintains a
  compact `style/profile.md` distillation (a few paragraphs plus a few
  representative sentences) and reads that when editing; it samples the
  originals only when rebuilding the profile.
- Add one file per reference, or a single `notes.md` collecting short
  excerpts with pointers to the originals.
