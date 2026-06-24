"""Runtime cleanup helpers."""

import os
import shutil
import tempfile
from pathlib import Path

from browser.web.webview2_view import WEBVIEW2_DATA_PREFIX

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def sweep_webview2_data(keep: str | None = None) -> None:
  root = tempfile.gettempdir()
  try:
    names = os.listdir(root)
  except OSError:
    return
  keep_abs = os.path.abspath(keep) if keep else None
  for name in names:
    if not name.startswith(WEBVIEW2_DATA_PREFIX):
      continue
    path = os.path.join(root, name)
    if keep_abs and os.path.abspath(path) == keep_abs:
      continue
    shutil.rmtree(path, ignore_errors=True)


def cleanup_pycache() -> None:
  for cache_dir in _PROJECT_ROOT.rglob("__pycache__"):
    if not cache_dir.is_dir():
      continue
    if any(part in ("venv", ".venv") for part in cache_dir.parts):
      continue
    shutil.rmtree(cache_dir, ignore_errors=True)