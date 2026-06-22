"""Session history page."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
  QHBoxLayout,
  QLabel,
  QPushButton,
  QScrollArea,
  QVBoxLayout,
  QWidget,
)

from browser.session.store import HistoryEntry, SessionStore


class HistoryListRow(QWidget):
  def __init__(self, entry: HistoryEntry, browser_window):
    super().__init__()
    self._entry = entry
    self._window = browser_window
    self.setObjectName("sessionListRow")

    layout = QHBoxLayout(self)
    layout.setContentsMargins(16, 10, 16, 10)
    layout.setSpacing(12)

    info = QVBoxLayout()
    info.setSpacing(2)

    title = QLabel(entry.title)
    title.setObjectName("sessionListTitle")

    meta = QLabel(f"{entry.visited_at} · {entry.url}")
    meta.setObjectName("sessionListMeta")

    info.addWidget(title)
    info.addWidget(meta)

    open_btn = QPushButton("Aç")
    open_btn.setObjectName("sessionActionBtn")
    open_btn.clicked.connect(self._open)

    layout.addLayout(info, 1)
    layout.addWidget(open_btn)

  def _open(self):
    tab = self._window.current_tab()
    if not tab:
      tab = self._window.add_tab()
    tab.navigate(self._entry.url)


class HistoryPage(QWidget):
  def __init__(self, session: SessionStore, browser_window, parent=None):
    super().__init__(parent)
    self._session = session
    self._window = browser_window
    self.setObjectName("sessionPage")

    root = QVBoxLayout(self)
    root.setContentsMargins(0, 0, 0, 0)

    header = QWidget()
    header.setObjectName("sessionPageHeader")
    hl = QHBoxLayout(header)
    hl.setContentsMargins(24, 20, 24, 12)
    title = QLabel("Tarixçə")
    title.setObjectName("sessionPageTitle")
    hl.addWidget(title)
    hl.addStretch()
    root.addWidget(header)

    self.empty = QLabel("Bu sessiyada tarixçə yoxdur")
    self.empty.setObjectName("sessionEmptyLabel")
    self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)

    self.scroll = QScrollArea()
    self.scroll.setObjectName("sessionScroll")
    self.scroll.setWidgetResizable(True)

    self.list_widget = QWidget()
    self._layout = QVBoxLayout(self.list_widget)
    self._layout.setContentsMargins(0, 0, 0, 0)
    self._layout.setSpacing(0)
    self._layout.addStretch()

    self._empty_wrap = QWidget()
    el = QVBoxLayout(self._empty_wrap)
    el.addStretch()
    el.addWidget(self.empty)
    el.addStretch()

    self.scroll.setWidget(self._empty_wrap)
    root.addWidget(self.scroll, 1)
    self.refresh()

  def refresh(self):
    while self._layout.count() > 1:
      item = self._layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()

    entries = self._session.history()
    if not entries:
      self.scroll.setWidget(self._empty_wrap)
      return

    self.scroll.setWidget(self.list_widget)
    for entry in entries:
      self._layout.insertWidget(0, HistoryListRow(entry, self._window))
