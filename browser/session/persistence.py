"""Əlfəcin anbarı və yerli saxlama yolu."""

import json
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QStandardPaths


def app_data_dir() -> Path:
  base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
  path = Path(base) / "MODBrowser"
  path.mkdir(parents=True, exist_ok=True)
  return path


def bookmarks_path() -> Path:
  return app_data_dir() / "bookmarks.json"


@dataclass
class Bookmark:
  url: str
  title: str


class BookmarkStore:
  def __init__(self):
    self._items: list[Bookmark] = []

  def load(self) -> None:
    path = bookmarks_path()
    if not path.is_file():
      return
    try:
      raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
      return
    self._items = [
      Bookmark(url=row.get("url", ""), title=row.get("title", ""))
      for row in raw
      if row.get("url")
    ]

  def save(self) -> None:
    data = [{"url": b.url, "title": b.title} for b in self._items]
    try:
      bookmarks_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
      )
    except OSError:
      pass

  def items(self) -> list[Bookmark]:
    return list(self._items)

  def contains(self, url: str) -> bool:
    return any(b.url == url for b in self._items)

  def add(self, url: str, title: str) -> None:
    url = url.strip()
    if not url or self.contains(url):
      return
    self._items.insert(0, Bookmark(url=url, title=title or url))
    self.save()

  def import_items(self, pairs) -> int:
    added = 0
    for url, title in pairs:
      url = url.strip()
      if not url or self.contains(url):
        continue
      self._items.insert(0, Bookmark(url=url, title=title or url))
      added += 1
    if added:
      self.save()
    return added

  def remove(self, url: str) -> None:
    self._items = [b for b in self._items if b.url != url]
    self.save()
