"""Session-only history and closed tabs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class HistoryEntry:
  url: str
  title: str
  visited_at: str


@dataclass
class ClosedTabEntry:
  url: str
  title: str


class SessionStore:
  def __init__(self):
    self._history: list[HistoryEntry] = []
    self._closed_tabs: list[ClosedTabEntry] = []

  def add_history(self, url: str, title: str):
    url = url.strip()
    if not url or url in ("about:blank", ""):
      return
    if self._history and self._history[0].url == url:
      self._history[0].title = title or url
      self._history[0].visited_at = datetime.now().strftime("%H:%M:%S")
      return
    self._history.insert(
      0,
      HistoryEntry(url=url, title=title or url, visited_at=datetime.now().strftime("%H:%M:%S")),
    )

  def history(self) -> list[HistoryEntry]:
    return list(self._history)

  def push_closed_tab(self, url: str, title: str):
    url = url.strip()
    if not url or url == "about:blank":
      return
    self._closed_tabs.append(ClosedTabEntry(url=url, title=title or url))

  def pop_closed_tab(self) -> ClosedTabEntry | None:
    return self._closed_tabs.pop() if self._closed_tabs else None

  def closed_tabs(self) -> list[ClosedTabEntry]:
    return list(self._closed_tabs)
