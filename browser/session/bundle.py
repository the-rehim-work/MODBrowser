"""Sessiya bağlaması — açıq tablar, tarixçə və əlfəcinlərin JSON ixracı/idxalı."""

import json
from pathlib import Path


def build_session(tabs, history, bookmarks=None):
  open_tabs = []
  for url, title in tabs:
    url = (url or "").strip()
    if not url or url == "about:blank":
      continue
    open_tabs.append({"url": url, "title": title or url})
  data = {
    "version": 1,
    "tabs": open_tabs,
    "history": [
      {"url": e.url, "title": e.title, "visited_at": e.visited_at} for e in history
    ],
  }
  if bookmarks is not None:
    data["bookmarks"] = [{"url": b.url, "title": b.title} for b in bookmarks]
  return data


def write_session(data, path):
  Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_session(path):
  raw = json.loads(Path(path).read_text(encoding="utf-8"))
  tabs = [
    (row.get("url", ""), row.get("title", ""))
    for row in raw.get("tabs", [])
    if row.get("url")
  ]
  bookmarks = [
    (row.get("url", ""), row.get("title", ""))
    for row in raw.get("bookmarks", [])
    if row.get("url")
  ]
  return tabs, bookmarks