# Project code

Optional scripts, data, and computational experiments for the manuscript.

## Setup

```sh
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Run scripts through the environment:

```sh
venv/bin/python scripts/<script>.py
```

## Layout

- `scripts/`: project scripts. Put shared helpers in `scripts/common.py`.
- `tests/`: unit tests (run with `venv/bin/python -m pytest`).
- `data/`: input data (large files should be git-ignored; document their
  schema at the top of the script that first reads them).
- `outputs/`: generated artifacts (git-ignored; regenerate from scripts).

Replace this README with the specifics of your project's pipeline.
