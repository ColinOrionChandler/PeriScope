"""Utilities for locating and reading PeriScope target lists."""

from __future__ import annotations

from pathlib import Path

DEFAULT_TARGET_LIST = Path("target_lists") / "aa_year1_paper.lst"


def load_target_names(path: str | Path) -> list[str]:
    """Read one target name per non-empty line from a text file."""
    target_path = Path(path).expanduser()
    if not target_path.is_file():
        raise FileNotFoundError(f"Target list not found: {target_path}")

    with target_path.open("r", encoding="utf-8") as handle:
        targets = [line.strip() for line in handle if line.strip()]

    if not targets:
        raise ValueError(f"Target list is empty: {target_path}")
    return targets
