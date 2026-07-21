"""Minimal project script template.

Run with:
    venv/bin/python scripts/example.py
"""

from __future__ import annotations

from common import OUTPUTS_DIR


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "example.txt").write_text("hello from example.py\n")
    print(f"Wrote {OUTPUTS_DIR / 'example.txt'}")


if __name__ == "__main__":
    main()
