"""Shared helpers for project scripts.

Centralize paths, configuration loading, and reusable IO here so that
individual scripts stay short and consistent.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "code" / "data"
OUTPUTS_DIR = REPO_ROOT / "code" / "outputs"
