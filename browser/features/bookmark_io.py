"""Netscape formatlı əlfəcin HTML ixracı/idxalı (Chrome/Edge/Firefox uyğun)."""

import html
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

_IMPORTABLE_SCHEMES = ("http://", "https://", "ftp://", "file:")


def export_html(items, path) -> None:
  stamp = str(int(datetime.now(timezone.utc).timestamp()))
  lines = [
    "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    "<TITLE>Bookmarks</TITLE>",
    "<H1>Bookmarks</H1>",
    "<DL><p>",
  ]
  for item in items:
    title = html.escape(item.title or item.url)
    url = html.escape(item.url, quote=True)
    lines.append(f'    <DT><A HREF="{url}" ADD_DATE="{stamp}">{title}</A>')
  lines.append("</DL><p>")
  Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


class _BookmarkParser(HTMLParser):
  def __init__(self):
    super().__init__()
    self._href = None
    self._buf = []
    self.results = []

  def handle_starttag(self, tag, attrs):
    if tag.lower() != "a":
      return
    href = dict(attrs).get("href", "")
    if href:
      self._href = href
      self._buf = []

  def handle_data(self, data):
    if self._href is not None:
      self._buf.append(data)

  def handle_endtag(self, tag):
    if tag.lower() == "a" and self._href is not None:
      title = "".join(self._buf).strip()
      self.results.append((self._href, title or self._href))
      self._href = None
      self._buf = []


def parse_html(path):
  text = Path(path).read_text(encoding="utf-8", errors="ignore")
  parser = _BookmarkParser()
  parser.feed(text)
  seen = set()
  out = []
  for url, title in parser.results:
    url = url.strip()
    if not url or not url.lower().startswith(_IMPORTABLE_SCHEMES):
      continue
    if url in seen:
      continue
    seen.add(url)
    out.append((url, title))
  return out
