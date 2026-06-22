"""Əlfəcinlər səhifəsi və əlfəcin paneli."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
  QHBoxLayout,
  QLabel,
  QPushButton,
  QScrollArea,
  QVBoxLayout,
  QWidget,
)

from browser.session.persistence import Bookmark, BookmarkStore


class BookmarkListRow(QWidget):
  def __init__(self, bookmark: Bookmark, store: BookmarkStore, browser_window, page):
    super().__init__()
    self._bookmark = bookmark
    self._store = store
    self._window = browser_window
    self._page = page
    self.setObjectName("sessionListRow")

    layout = QHBoxLayout(self)
    layout.setContentsMargins(16, 10, 16, 10)
    layout.setSpacing(12)

    info = QVBoxLayout()
    info.setSpacing(2)

    title = QLabel(bookmark.title)
    title.setObjectName("sessionListTitle")

    meta = QLabel(bookmark.url)
    meta.setObjectName("sessionListMeta")

    info.addWidget(title)
    info.addWidget(meta)

    open_btn = QPushButton("Aç")
    open_btn.setObjectName("sessionActionBtn")
    open_btn.clicked.connect(self._open)

    remove_btn = QPushButton("Sil")
    remove_btn.setObjectName("sessionActionBtn")
    remove_btn.clicked.connect(self._remove)

    layout.addLayout(info, 1)
    layout.addWidget(open_btn)
    layout.addWidget(remove_btn)

  def _open(self):
    self._window.open_url_in_new_tab(self._bookmark.url)

  def _remove(self):
    self._store.remove(self._bookmark.url)
    self._page.refresh()
    self._window.refresh_bookmark_star()
    self._window.refresh_bookmarks_bar()


class BookmarksPage(QWidget):
  def __init__(self, store: BookmarkStore, browser_window, parent=None):
    super().__init__(parent)
    self._store = store
    self._window = browser_window
    self.setObjectName("sessionPage")

    root = QVBoxLayout(self)
    root.setContentsMargins(0, 0, 0, 0)

    header = QWidget()
    header.setObjectName("sessionPageHeader")
    hl = QHBoxLayout(header)
    hl.setContentsMargins(24, 20, 24, 12)
    title = QLabel("Əlfəcinlər")
    title.setObjectName("sessionPageTitle")
    hl.addWidget(title)
    hl.addStretch()

    import_btn = QPushButton("İdxal et")
    import_btn.setObjectName("sessionActionBtn")
    import_btn.clicked.connect(browser_window.import_bookmarks)

    export_btn = QPushButton("İxrac et")
    export_btn.setObjectName("sessionActionBtn")
    export_btn.clicked.connect(browser_window.export_bookmarks)

    hl.addWidget(import_btn)
    hl.addWidget(export_btn)
    root.addWidget(header)

    self.empty = QLabel("Əlfəcin yoxdur")
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

    items = self._store.items()
    if not items:
      self.scroll.setWidget(self._empty_wrap)
      return

    self.scroll.setWidget(self.list_widget)
    for bookmark in items:
      self._layout.insertWidget(
        self._layout.count() - 1,
        BookmarkListRow(bookmark, self._store, self._window, self),
      )


class BookmarksBar(QWidget):
  def __init__(self, store: BookmarkStore, browser_window, parent=None):
    super().__init__(parent)
    self._store = store
    self._window = browser_window
    self.setObjectName("bookmarksBar")

    self._layout = QHBoxLayout(self)
    self._layout.setContentsMargins(6, 2, 6, 2)
    self._layout.setSpacing(2)
    self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    self.refresh()

  def refresh(self):
    while self._layout.count():
      item = self._layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()

    items = self._store.items()
    if not items:
      empty = QLabel("Əlfəcin yoxdur — Ctrl+D ilə əlavə edin")
      empty.setObjectName("bookmarksBarEmpty")
      self._layout.addWidget(empty)
      return

    for bookmark in items:
      btn = QPushButton(self._short(bookmark.title))
      btn.setObjectName("bookmarksBarBtn")
      btn.setToolTip(bookmark.url)
      btn.setFlat(True)
      btn.setCursor(Qt.CursorShape.PointingHandCursor)
      btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
      btn.clicked.connect(lambda _checked=False, url=bookmark.url: self._open(url))
      self._layout.addWidget(btn)
    self._layout.addStretch()

  def _short(self, title: str) -> str:
    title = (title or "").strip()
    return title if len(title) <= 24 else title[:21] + "..."

  def _open(self, url: str):
    tab = self._window.current_tab()
    if tab:
      tab.navigate(url)
    else:
      self._window.add_tab(url)
