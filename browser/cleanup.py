"""Runtime cleanup helpers."""

import shutil
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def cleanup_pycache() -> None:
  for cache_dir in _PROJECT_ROOT.rglob("__pycache__"):
    if not cache_dir.is_dir():
      continue
    if any(part in ("venv", ".venv") for part in cache_dir.parts):
      continue
    shutil.rmtree(cache_dir, ignore_errors=True)
