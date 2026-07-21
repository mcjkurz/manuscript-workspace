"""Smoke test for shared helpers.

Run with:
    venv/bin/python -m pytest tests/
"""

from __future__ import annotations

from common import REPO_ROOT


def test_repo_root_exists() -> None:
    assert REPO_ROOT.is_dir()
    assert (REPO_ROOT / "manuscript").is_dir()
