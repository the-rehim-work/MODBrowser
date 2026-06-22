"""Main browser window with multi-tab incognito UI."""

import sys

from PyQt6.QtCore import QEvent, QPoint, Qt, QTimer, QUrl, QSize
from PyQt6.QtGui import QAction, QIcon, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import (
  QApplication,
  QFileDialog,
  QHBoxLayout,
  QLineEdit,
  QMainWindow,
  QMenu,
  QMessageBox,
  QPushButton,
  QStackedWidget,
  QTabBar,
  QToolButton,
  QVBoxLayout,
  QWidget,
)

from browser.cleanup import cleanup_pycache
from browser.constants import BLANK_PAGE, HOME_URL, NEW_TAB_TITLE
from browser.features.bookmarks import BookmarksBar, BookmarksPage
from browser.features.bookmark_io import export_html, parse_html
from browser.features.downloads import DownloadManager, DownloadPanel, DownloadsPage, handle_download
from browser.features.history import HistoryPage
from browser.session.persistence import BookmarkStore
from browser.session.settings import BrowserSettings
from browser.session.store import SessionStore
from browser.ui.dialogs import SHORTCUTS_HTML, SettingsDialog, apply_proxy
from browser.ui.devtools import DevToolsDock
from browser.ui.find_bar import FindBar
from browser.ui.icons import back_icon, close_icon, forward_icon, plus_icon, reload_icon, stop_icon
from browser.ui.styles import DARK_STYLE
from browser.ui.toast import Toast
from browser.web.google_auth import apply_firefox_identity, is_google_auth_url
from browser.web.engine import preferred_engine
from browser.web.media import check_h264_support
from browser.web.profile import apply_browser_identity, create_incognito_profile
from browser.web.tab import BrowserTab, tab_display_title


class AddressBar(QLineEdit):
  def __init__(self, parent=None):
    super().__init__(parent)
    self._select_all_on_release = False

  def select_all_and_focus(self):
    if not self.hasFocus():
      self.setFocus(Qt.FocusReason.ShortcutFocusReason)
    QTimer.singleShot(0, self._select_all_if_focused)

  def _select_all_if_focused(self):
    if self.hasFocus():
      self.selectAll()

  def focusInEvent(self, event):
    window = self.window()
    if hasattr(window, "set_page_input_blocked"):
      window.set_page_input_blocked(True)
    super().focusInEvent(event)
    if event.reason() != Qt.FocusReason.MouseFocusReason:
      QTimer.singleShot(0, self._select_all_if_focused)

  def focusOutEvent(self, event):
    self._select_all_on_release = False
    window = self.window()
    if hasattr(window, "set_page_input_blocked"):
      window.set_page_input_blocked(False)
    super().focusOutEvent(event)

  def keyPressEvent(self, event: QKeyEvent):
    if (
      event.key() == Qt.Key.Key_A
      and event.modifiers() & Qt.KeyboardModifier.ControlModifier
    ):
      self.selectAll()
      event.accept()
      return
    super().keyPressEvent(event)

  def mousePressEvent(self, event):
    full_selection = (
      self.hasSelectedText()
      and self.text()
      and len(self.selectedText()) == len(self.text())
    )
    self._select_all_on_release = not (self.hasFocus() and full_selection)
    super().mousePressEvent(event)

  def mouseReleaseEvent(self, event):
    super().mouseReleaseEvent(event)
    if self._select_all_on_release:
      self._select_all_on_release = False
      self.selectAll()


class BrowserWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.settings = BrowserSettings()
    self._session = SessionStore()
    self._bookmarks = BookmarkStore()
    self._bookmarks.load()
    self._profile, self._content_blocker = create_incognito_profile(self.settings, self)
    self._profile.downloadRequested.connect(self._handle_download)
    self._download_manager = DownloadManager(self)
    self._download_manager.record_updated.connect(self._on_download_updated)
    self._tabs: list = []
    self._devtools = None
    self._google_auth_tabs = 0
    self._using_firefox_identity = False
    self._identity_sync_timer = QTimer(self)
    self._identity_sync_timer.setSingleShot(True)
    self._identity_sync_timer.timeout.connect(self._deferred_identity_sync)

    self.setWindowTitle("MOD Browser")
    self.setMinimumSize(1024, 680)
    self.resize(1280, 800)

    self._idle_timer = QTimer(self)
    self._idle_timer.setSingleShot(True)
    self._idle_timer.timeout.connect(self.close)

    self._build_ui()
    self._build_app_menu()
    self._build_shortcuts()
    self._shield_timer = QTimer(self)
    self._shield_timer.timeout.connect(self._update_shield)
    self._shield_timer.start(1000)
    QApplication.instance().installEventFilter(self)
    self.reset_idle_timer()
    apply_proxy(self.settings)
    self.add_tab(HOME_URL)
    QTimer.singleShot(1500, self._check_video_codecs)

  def _check_video_codecs(self):
    if preferred_engine() == "webview2" or not self._tabs:
      return
    page = self._tabs[0].view.page()
    if check_h264_support(page):
      return
    self._toast.show_message(
      "H.264 video dəstəklənmir. YouTube canlı yayımlar və bəzi saytlar işləməyə bilər. "
      "Windows-da WebView2 runtime quraşdırın.",
      12000,
    )

  def _build_ui(self):
    central = QWidget()
    self.setCentralWidget(central)
    root = QVBoxLayout(central)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    toolbar = QWidget()
    toolbar.setObjectName("toolbar")
    tb = QHBoxLayout(toolbar)
    tb.setContentsMargins(8, 4, 8, 4)
    tb.setSpacing(4)

    self.btn_back = self._make_nav_btn(back_icon(14), "Geri (Alt+Sol)", self._go_back)
    self.btn_forward = self._make_nav_btn(forward_icon(14), "İrəli (Alt+Sağ)", self._go_forward)
    self.btn_reload = self._make_nav_btn(reload_icon(14), "Yenilə (Ctrl+R)", self._toggle_reload_stop)

    self.address_bar = AddressBar()
    self.address_bar.setObjectName("addressBar")
    self.address_bar.setPlaceholderText("URL daxil edin və ya axtarın...")
    self.address_bar.returnPressed.connect(self._navigate_from_bar)

    self.star_btn = QPushButton("☆")
    self.star_btn.setObjectName("starBtn")
    self.star_btn.setToolTip("Əlfəcinə əlavə et (Ctrl+D)")
    self.star_btn.setFixedSize(32, 32)
    self.star_btn.setFlat(True)
    self.star_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.star_btn.clicked.connect(self._toggle_bookmark)

    self.shield_btn = QPushButton("🛡 0")
    self.shield_btn.setObjectName("shieldBtn")
    self.shield_btn.setToolTip("Reklam bloku")
    self.shield_btn.setFixedHeight(32)
    self.shield_btn.setFlat(True)
    self.shield_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.shield_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.shield_btn.clicked.connect(self._toggle_adblock)

    self.menu_btn = QPushButton("⋮")
    self.menu_btn.setObjectName("menuBtn")
    self.menu_btn.setToolTip("Menyu")
    self.menu_btn.setFixedSize(32, 32)
    self.menu_btn.setFlat(True)
    self.menu_btn.setAutoDefault(False)
    self.menu_btn.setDefault(False)
    self.menu_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.menu_btn.clicked.connect(self._show_app_menu)

    tb.addWidget(self.btn_back)
    tb.addWidget(self.btn_forward)
    tb.addWidget(self.btn_reload)
    tb.addWidget(self.address_bar, stretch=1)
    tb.addWidget(self.star_btn)
    tb.addWidget(self.shield_btn)
    tb.addWidget(self.menu_btn)

    self.find_bar = FindBar(self)
    self.find_bar.hide()

    tab_row = QWidget()
    tab_row.setObjectName("tabRow")
    tab_row_layout = QHBoxLayout(tab_row)
    tab_row_layout.setContentsMargins(6, 2, 6, 0)
    tab_row_layout.setSpacing(4)
    tab_row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    self.new_tab_btn = QToolButton()
    self.new_tab_btn.setObjectName("newTabBtn")
    self.new_tab_btn.setToolTip("Yeni tab (Ctrl+T)")
    self.new_tab_btn.setIcon(plus_icon(14))
    self.new_tab_btn.setIconSize(QSize(14, 14))
    self.new_tab_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    self.new_tab_btn.setFixedSize(24, 24)
    self.new_tab_btn.setAutoRaise(True)
    self.new_tab_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.new_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.new_tab_btn.clicked.connect(lambda: self.add_tab())
    tab_row_layout.addWidget(self.new_tab_btn, 0, Qt.AlignmentFlag.AlignVCenter)

    self.tab_bar = QTabBar()
    self.tab_bar.setObjectName("mainTabBar")
    self.tab_bar.setDrawBase(False)
    self.tab_bar.setExpanding(False)
    self.tab_bar.setMovable(True)
    self.tab_bar.setIconSize(QSize(14, 14))
    self.tab_bar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.tab_bar.currentChanged.connect(self._on_tab_changed)
    self.tab_bar.tabMoved.connect(self._on_tab_moved)
    self.tab_bar.installEventFilter(self)
    tab_row_layout.addWidget(self.tab_bar, 1, Qt.AlignmentFlag.AlignVCenter)

    self.stack = QStackedWidget()
    self.stack.setObjectName("tabStack")
    self.download_panel = DownloadPanel(self._download_manager)
    self._toast = Toast(central)

    self.bookmarks_bar = BookmarksBar(self._bookmarks, self)
    self.bookmarks_bar.hide()

    root.addWidget(toolbar)
    root.addWidget(self.bookmarks_bar)
    root.addWidget(self.find_bar)
    root.addWidget(tab_row)
    root.addWidget(self.stack, stretch=1)
    root.addWidget(self.download_panel)

  def _make_nav_btn(self, icon: QIcon, tooltip: str, handler):
    btn = QToolButton()
    btn.setObjectName("navBtn")
    btn.setIcon(icon)
    btn.setIconSize(QSize(14, 14))
    btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    btn.setFixedSize(32, 32)
    btn.setAutoRaise(True)
    btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setToolTip(tooltip)
    btn.clicked.connect(handler)
    return btn

  def _build_app_menu(self):
    self.menuBar().setVisible(False)
    self._app_menu = QMenu(self)
    self._app_menu.setObjectName("appMenu")

    new_tab = self._app_menu.addAction("Yeni tab")
    new_tab.setShortcut(QKeySequence("Ctrl+T"))
    new_tab.triggered.connect(lambda: self.add_tab())

    close_tab = self._app_menu.addAction("Tabı bağla")
    close_tab.setShortcut(QKeySequence("Ctrl+W"))
    close_tab.triggered.connect(lambda: self.close_tab(self.tab_bar.currentIndex()))

    restore_tab = self._app_menu.addAction("Son tabı bərpa et")
    restore_tab.setShortcut(QKeySequence("Ctrl+Shift+T"))
    restore_tab.triggered.connect(self.restore_closed_tab)

    bookmarks_action = self._app_menu.addAction("Əlfəcinlər")
    bookmarks_action.setShortcut(QKeySequence("Ctrl+B"))
    bookmarks_action.triggered.connect(self.open_bookmarks_page)

    bookmarks_bar_action = self._app_menu.addAction("Əlfəcin paneli")
    bookmarks_bar_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
    bookmarks_bar_action.triggered.connect(self._toggle_bookmarks_bar)

    export_bm = self._app_menu.addAction("Əlfəcinləri ixrac et")
    export_bm.triggered.connect(self.export_bookmarks)

    import_bm = self._app_menu.addAction("Əlfəcinləri idxal et")
    import_bm.triggered.connect(self.import_bookmarks)

    self._app_menu.addSeparator()

    history_action = self._app_menu.addAction("Tarixçə")
    history_action.setShortcut(QKeySequence("Ctrl+H"))
    history_action.triggered.connect(self.open_history_page)

    downloads_action = self._app_menu.addAction("Yükləmələr")
    downloads_action.setShortcut(QKeySequence("Ctrl+J"))
    downloads_action.triggered.connect(self.open_downloads_page)

    self._app_menu.addSeparator()

    settings_action = self._app_menu.addAction("Parametrlər")
    settings_action.triggered.connect(self._show_settings)

    shortcuts_action = self._app_menu.addAction("Qısayollar")
    shortcuts_action.triggered.connect(self._show_shortcuts)

    about_action = self._app_menu.addAction("Haqqında")
    about_action.triggered.connect(self._show_about)

    self._app_menu.addSeparator()

    quit_action = self._app_menu.addAction("Çıxış")
    quit_action.setShortcut(QKeySequence("Ctrl+Q"))
    quit_action.triggered.connect(self.close)

    for action in (
      new_tab, close_tab, restore_tab, bookmarks_action, bookmarks_bar_action,
      history_action, downloads_action, quit_action,
    ):
      self.addAction(action)

  def _build_shortcuts(self):
    shortcuts = [
      ("Ctrl+L", self._focus_address_bar),
      ("Ctrl+F", self.find_bar.show_bar),
      ("Ctrl+Tab", self._next_tab),
      ("Ctrl+Shift+Tab", self._prev_tab),
      ("Ctrl+R", self._reload),
      ("F5", self._reload),
      ("Ctrl+F5", self._hard_reload),
      ("Ctrl+Shift+R", self._hard_reload),
      ("Shift+F5", self._hard_reload),
      ("F6", self._cycle_focus),
      ("Escape", self._on_escape),
      ("Alt+Home", self._go_home),
      ("Ctrl+P", self._print_page),
      ("F12", self._toggle_devtools),
      ("Ctrl+Shift+I", self._toggle_devtools),
      ("Ctrl+Shift+J", self._toggle_devtools),
      ("F11", self.toggle_fullscreen),
      ("Ctrl++", self._zoom_in),
      ("Ctrl+=", self._zoom_in),
      ("Ctrl+-", self._zoom_out),
      ("Ctrl+0", self._zoom_reset),
      ("Alt+Left", self._go_back),
      ("Alt+Right", self._go_forward),
      ("Ctrl+D", self._toggle_bookmark),
    ]
    for seq, handler in shortcuts:
      action = QAction(self)
      action.setShortcut(QKeySequence(seq))
      action.triggered.connect(handler)
      self.addAction(action)

    for i in range(1, 9):
      action = QAction(self)
      action.setShortcut(QKeySequence(f"Ctrl+{i}"))
      action.triggered.connect(lambda _checked=False, idx=i - 1: self._jump_to_tab(idx))
      self.addAction(action)
    last_action = QAction(self)
    last_action.setShortcut(QKeySequence("Ctrl+9"))
    last_action.triggered.connect(self._last_tab)
    self.addAction(last_action)

  def _update_shield(self):
    blocker = self._content_blocker
    if blocker.is_enabled():
      self.shield_btn.setText(f"🛡 {blocker.blocked_count}")
      self.shield_btn.setToolTip(f"Reklam bloku aktiv · {blocker.blocked_count} bloklandı")
    else:
      self.shield_btn.setText("🛡 off")
      self.shield_btn.setToolTip("Reklam bloku söndürülüb")

  def _toggle_adblock(self):
    blocker = self._content_blocker
    blocker.set_enabled(not blocker.is_enabled())
    self.settings.adblock_enabled = blocker.is_enabled()
    state = "aktiv edildi" if blocker.is_enabled() else "söndürüldü"
    self._toast.show_message(f"Reklam bloku {state}")
    self._update_shield()

  def open_bookmarks_page(self):
    def create():
      page = BookmarksPage(self._bookmarks, self)
      self._add_special_tab(page, "Əlfəcinlər")
    self._open_special_page(BookmarksPage, "Əlfəcinlər", create)

  def _toggle_bookmark(self):
    tab = self.current_tab()
    if not tab:
      return
    url = tab.current_url().toString()
    if not url or url in ("", "about:blank"):
      return
    if self._bookmarks.contains(url):
      self._bookmarks.remove(url)
      self._toast.show_message("Əlfəcin silindi")
    else:
      self._bookmarks.add(url, tab.view.title())
      self._toast.show_message("Əlfəcinə əlavə edildi")
    self.refresh_bookmark_star()
    self.refresh_bookmarks_bar()

  def refresh_bookmark_star(self):
    tab = self.current_tab()
    marked = bool(tab and self._bookmarks.contains(tab.current_url().toString()))
    self.star_btn.setText("★" if marked else "☆")

  def refresh_bookmarks_bar(self):
    if getattr(self, "bookmarks_bar", None) is not None:
      self.bookmarks_bar.refresh()

  def _toggle_bookmarks_bar(self):
    if self.bookmarks_bar.isVisible():
      self.bookmarks_bar.hide()
    else:
      self.bookmarks_bar.refresh()
      self.bookmarks_bar.show()

  def export_bookmarks(self):
    items = self._bookmarks.items()
    if not items:
      self._toast.show_message("İxrac üçün əlfəcin yoxdur")
      return
    path, _ = QFileDialog.getSaveFileName(
      self, "Əlfəcinləri ixrac et", "bookmarks.html", "HTML (*.html)"
    )
    if not path:
      return
    try:
      export_html(items, path)
      self._toast.show_message(f"{len(items)} əlfəcin ixrac edildi")
    except OSError:
      self._toast.show_message("İxrac alınmadı")

  def import_bookmarks(self):
    path, _ = QFileDialog.getOpenFileName(
      self, "Əlfəcinləri idxal et", "", "HTML (*.html *.htm)"
    )
    if not path:
      return
    try:
      pairs = parse_html(path)
    except OSError:
      self._toast.show_message("Fayl oxunmadı")
      return
    added = self._bookmarks.import_items(pairs)
    self._toast.show_message(
      f"{added} əlfəcin idxal edildi" if added else "Yeni əlfəcin tapılmadı"
    )
    self.refresh_bookmark_star()
    self.refresh_bookmarks_bar()
    for tab in self._tabs:
      if isinstance(tab, BookmarksPage):
        tab.refresh()

  def reset_idle_timer(self):
    if self.settings.idle_minutes <= 0:
      self._idle_timer.stop()
      return
    self._idle_timer.start(self.settings.idle_minutes * 60 * 1000)

  def event(self, event):
    if event.type() in (
      QEvent.Type.MouseMove,
      QEvent.Type.KeyPress,
      QEvent.Type.MouseButtonPress,
      QEvent.Type.Wheel,
    ):
      self.reset_idle_timer()
    return super().event(event)

  def eventFilter(self, obj, event):
    if event.type() == QEvent.Type.MouseButtonPress and self.address_bar.hasFocus():
      click_pos = event.globalPosition().toPoint()
      if not self.address_bar.rect().contains(self.address_bar.mapFromGlobal(click_pos)):
        self.address_bar.clearFocus()
    if obj is self.tab_bar and event.type() == QEvent.Type.ContextMenu:
      index = self.tab_bar.tabAt(event.pos())
      if index >= 0:
        self._show_tab_context_menu(index, event.globalPos())
        return True
    return super().eventFilter(obj, event)

  def _show_tab_context_menu(self, index: int, global_pos: QPoint):
    menu = QMenu(self)
    menu.setObjectName("contextMenu")

    duplicate = menu.addAction("Dublikat et")
    duplicate.triggered.connect(lambda: self.duplicate_tab(index))

    close_all = menu.addAction("Bütün tabları bağla")
    close_all.triggered.connect(self.close_all_tabs)

    menu.exec(global_pos)

  def duplicate_tab(self, index: int):
    if index < 0 or index >= self.stack.count():
      return
    widget = self.stack.widget(index)
    if isinstance(widget, BrowserTab):
      url = widget.current_url().toString()
      if url in ("", "about:blank"):
        tab = self.add_tab()
      else:
        tab = self.add_tab(url)
      tab.set_zoom(widget.zoom_factor())
    elif isinstance(widget, HistoryPage):
      self.open_history_page()
    elif isinstance(widget, DownloadsPage):
      self.open_downloads_page()
    elif isinstance(widget, BookmarksPage):
      self.open_bookmarks_page()

  def close_all_tabs(self):
    while self.tab_bar.count() > 0:
      widget = self.stack.widget(0)
      if widget in self._tabs:
        self._tabs.remove(widget)
      self.tab_bar.removeTab(0)
      self.stack.removeWidget(widget)
      if isinstance(widget, BrowserTab) and hasattr(widget.view, "setPage"):
        widget.view.setPage(None)
      widget.deleteLater()
    self.add_tab(HOME_URL)

  def record_visit(self, url: str, title: str):
    self._session.add_history(url, title)

  def open_url_in_new_tab(self, url: str, background: bool = False):
    current = self.tab_bar.currentIndex()
    tab = self.add_tab(url)
    if background and current >= 0:
      self.tab_bar.setCurrentIndex(current)
    return tab

  def restore_closed_tab(self):
    entry = self._session.pop_closed_tab()
    if not entry:
      self._toast.show_message("Bərpa ediləcək tab yoxdur")
      return
    tab = self.add_tab(entry.url)
    self.update_tab_title(tab, tab_display_title(entry.title, QUrl(entry.url)))

  def _show_settings(self):
    dialog = SettingsDialog(self.settings, self._profile, self._content_blocker, self)
    if dialog.exec():
      self.reset_idle_timer()
      self._toast.show_message("Parametrlər yeniləndi")

  def _show_shortcuts(self):
    QMessageBox.information(self, "Qısayollar", SHORTCUTS_HTML)

  def _show_about(self):
    QMessageBox.about(
      self,
      "Haqqında",
      "<div align='center'><h3 style='margin: 0;'>MOD Browser</h3></div>"
      "<p align='center'>Copyright 2026 Proqramlaşdırma Şöbəsi. All rights reserved.</p>",
    )

  def _open_special_page(self, page_cls, tab_title: str, opener):
    for tab in self._tabs:
      if isinstance(tab, page_cls):
        self.tab_bar.setCurrentIndex(self._tab_index(tab))
        if hasattr(tab, "refresh"):
          tab.refresh()
        return
    opener()

  def open_downloads_page(self):
    def create():
      page = DownloadsPage(self._download_manager, self)
      self._add_special_tab(page, "Yükləmələr")
    self._open_special_page(DownloadsPage, "Yükləmələr", create)

  def open_history_page(self):
    def create():
      page = HistoryPage(self._session, self, self)
      self._add_special_tab(page, "Tarixçə")
    self._open_special_page(HistoryPage, "Tarixçə", create)

  def _add_special_tab(self, page: QWidget, title: str):
    index = self.tab_bar.addTab(title)
    self.stack.addWidget(page)
    self._attach_tab_close_button(index)
    self._tabs.append(page)
    self.tab_bar.setCurrentIndex(index)
    self._on_tab_changed(index)

  def _show_app_menu(self):
    pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft())
    self._app_menu.exec(pos)

  def _next_tab(self):
    if self.tab_bar.count() > 1:
      self.tab_bar.setCurrentIndex((self.tab_bar.currentIndex() + 1) % self.tab_bar.count())

  def _prev_tab(self):
    if self.tab_bar.count() > 1:
      self.tab_bar.setCurrentIndex((self.tab_bar.currentIndex() - 1) % self.tab_bar.count())

  def _sync_stack_index(self, index: int):
    if 0 <= index < self.stack.count():
      self.stack.setCurrentIndex(index)

  def _on_tab_moved(self, from_index: int, to_index: int):
    widget = self.stack.widget(from_index)
    self.stack.removeWidget(widget)
    self.stack.insertWidget(to_index, widget)
    tab = self._tabs.pop(from_index)
    self._tabs.insert(to_index, tab)

  def current_tab(self) -> BrowserTab | None:
    widget = self.stack.currentWidget()
    return widget if isinstance(widget, BrowserTab) else None

  def _tab_index(self, tab) -> int:
    return self._tabs.index(tab) if tab in self._tabs else -1

  def _attach_tab_close_button(self, index: int):
    wrap = QWidget()
    wrap.setFixedSize(22, 24)
    wrap_layout = QHBoxLayout(wrap)
    wrap_layout.setContentsMargins(0, 0, 0, 0)
    wrap_layout.setSpacing(0)
    wrap_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    close_btn = QToolButton()
    close_btn.setObjectName("tabCloseBtn")
    close_btn.setIcon(close_icon(10))
    close_btn.setIconSize(QSize(10, 10))
    close_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    close_btn.setFixedSize(18, 18)
    close_btn.setAutoRaise(True)
    close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    close_btn.setToolTip("Tabı bağla")
    close_btn.clicked.connect(lambda: self._close_tab_by_button(close_btn))
    wrap_layout.addWidget(close_btn)

    self.tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, wrap)

  def _close_tab_by_button(self, button):
    for i in range(self.tab_bar.count()):
      tab_btn = self.tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
      if tab_btn is None:
        continue
      if tab_btn is button or tab_btn.findChild(QToolButton, "tabCloseBtn") is button:
        self.close_tab(i)
        return

  def add_tab(self, url: str | None = None):
    tab = BrowserTab(self._profile, self, self)
    index = self.tab_bar.addTab(NEW_TAB_TITLE)
    self.stack.addWidget(tab)
    self._attach_tab_close_button(index)
    self._tabs.append(tab)
    self.tab_bar.setCurrentIndex(index)
    if url:
      tab.navigate(url)
    else:
      tab.view.setHtml(BLANK_PAGE, QUrl("about:blank"))
      self.address_bar.clear()
      self.address_bar.select_all_and_focus()
    return tab

  def reset_tab(self, tab: BrowserTab):
    tab.navigate(HOME_URL)

  def update_google_auth_state(self, tab: BrowserTab, url: QUrl, *, immediate: bool = False):
    is_auth = is_google_auth_url(url)
    if is_auth == getattr(tab, "_on_google_auth", False):
      return
    tab._on_google_auth = is_auth
    if is_auth:
      self._google_auth_tabs += 1
    else:
      self._google_auth_tabs = max(0, self._google_auth_tabs - 1)
    if immediate:
      self._sync_browser_identity()
    else:
      delay = 0 if is_auth else 300
      self._schedule_identity_sync(delay)

  def release_google_auth_tab(self, tab: BrowserTab):
    if not getattr(tab, "_on_google_auth", False):
      return
    tab._on_google_auth = False
    self._google_auth_tabs = max(0, self._google_auth_tabs - 1)
    self._schedule_identity_sync(300)

  def _schedule_identity_sync(self, delay_ms: int = 0):
    if self._identity_sync_timer.isActive():
      self._identity_sync_timer.stop()
    self._identity_sync_timer.start(delay_ms)

  def _deferred_identity_sync(self):
    self._sync_browser_identity()

  def _sync_browser_identity(self):
    want_firefox = self._google_auth_tabs > 0
    if want_firefox == self._using_firefox_identity:
      return
    self._using_firefox_identity = want_firefox
    if want_firefox:
      apply_firefox_identity(self._profile)
    else:
      apply_browser_identity(self._profile, self.settings)

  def close_tab(self, index: int):
    widget = self.stack.widget(index)
    if isinstance(widget, BrowserTab):
      self.release_google_auth_tab(widget)
      self._session.push_closed_tab(
        widget.current_url().toString(),
        self.tab_bar.tabText(index),
      )
    if self.tab_bar.count() <= 1:
      if isinstance(widget, BrowserTab):
        self.reset_tab(widget)
      else:
        self._tabs.remove(widget)
        self.tab_bar.removeTab(index)
        self.stack.removeWidget(widget)
        widget.deleteLater()
        self.add_tab(HOME_URL)
      return
    if widget in self._tabs:
      self._tabs.remove(widget)
    self.tab_bar.removeTab(index)
    self.stack.removeWidget(widget)
    widget.deleteLater()
    self._update_nav_buttons()

  def _on_tab_changed(self, index: int):
    if index < 0:
      return
    self._sync_stack_index(index)
    if index >= self.stack.count():
      return

    page = self.stack.widget(index)
    if not isinstance(page, BrowserTab):
      self.address_bar.clear()
      placeholder = {
        DownloadsPage: "Yükləmələr",
        HistoryPage: "Tarixçə",
        BookmarksPage: "Əlfəcinlər",
      }.get(type(page), "")
      self.address_bar.setPlaceholderText(placeholder)
      self.btn_back.setEnabled(False)
      self.btn_forward.setEnabled(False)
      self.btn_reload.setEnabled(False)
      self.star_btn.setText("☆")
      self.find_bar.hide_bar()
      return

    self.address_bar.setPlaceholderText("URL daxil edin və ya axtarın...")
    self.btn_reload.setEnabled(True)
    url = page.current_url().toString()
    if url and url not in ("", "about:blank"):
      self.address_bar.setText(url)
    else:
      self.address_bar.clear()
    self._update_nav_buttons()
    self.refresh_bookmark_star()
    if self._devtools is not None and self._devtools.isVisible():
      self._devtools.inspect(page.view.page())

  def set_page_input_blocked(self, blocked: bool):
    tab = self.current_tab()
    if tab is None:
      return
    view = tab.view
    if hasattr(view, "set_input_blocked"):
      view.set_input_blocked(blocked)
    elif blocked:
      view.clearFocus()

  def _focus_address_bar(self):
    self.address_bar.select_all_and_focus()

  def _navigate_from_bar(self):
    tab = self.current_tab()
    if tab:
      tab.navigate(self.address_bar.text())
      tab.view.setFocus()

  def _go_back(self):
    tab = self.current_tab()
    if tab:
      tab.go_back()

  def _go_forward(self):
    tab = self.current_tab()
    if tab:
      tab.go_forward()

  def _reload(self):
    tab = self.current_tab()
    if tab:
      tab.reload()

  def _stop(self):
    tab = self.current_tab()
    if tab:
      tab.stop()

  def _toggle_reload_stop(self):
    tab = self.current_tab()
    if not tab:
      return
    if tab.is_loading():
      tab.stop()
    else:
      tab.reload()

  def _hard_reload(self):
    tab = self.current_tab()
    if tab:
      tab.reload_bypass_cache()

  def _cycle_focus(self):
    if self.address_bar.hasFocus():
      tab = self.current_tab()
      if tab:
        tab.view.setFocus()
    else:
      self.address_bar.select_all_and_focus()

  def _on_escape(self):
    if self.find_bar.isVisible():
      self.find_bar.hide_bar()
      return
    tab = self.current_tab()
    if tab and tab.is_loading():
      tab.stop()

  def _go_home(self):
    tab = self.current_tab()
    if tab:
      tab.navigate(HOME_URL)
    else:
      self.add_tab(HOME_URL)

  def _print_page(self):
    tab = self.current_tab()
    if not tab:
      return
    page = tab.view.page()
    if not hasattr(page, "printToPdf"):
      self._toast.show_message("Çap yalnız WebEngine rejimində mövcuddur")
      return
    path, _ = QFileDialog.getSaveFileName(self, "PDF kimi saxla", "səhifə.pdf", "PDF (*.pdf)")
    if not path:
      return
    page.printToPdf(path)
    self._toast.show_message("PDF yadda saxlanıldı")

  def _jump_to_tab(self, index: int):
    if 0 <= index < self.tab_bar.count():
      self.tab_bar.setCurrentIndex(index)

  def _last_tab(self):
    if self.tab_bar.count() > 0:
      self.tab_bar.setCurrentIndex(self.tab_bar.count() - 1)

  def _toggle_devtools(self):
    tab = self.current_tab()
    if tab is None:
      return
    page = tab.view.page()
    if not hasattr(page, "setDevToolsPage"):
      self._toast.show_message("DevTools yalnız WebEngine rejimində mövcuddur")
      return
    if self._devtools is None:
      self._devtools = DevToolsDock(self)
      self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._devtools)
    if self._devtools.isVisible():
      self._devtools.detach()
      self._devtools.hide()
    else:
      self._devtools.inspect(page)
      self._devtools.show()

  def _zoom_in(self):
    tab = self.current_tab()
    if tab:
      tab.zoom_in()

  def _zoom_out(self):
    tab = self.current_tab()
    if tab:
      tab.zoom_out()

  def _zoom_reset(self):
    tab = self.current_tab()
    if tab:
      tab.reset_zoom()

  def toggle_fullscreen(self):
    self.showNormal() if self.isFullScreen() else self.showFullScreen()

  def update_zoom_display(self, _factor: float):
    pass

  def _update_nav_buttons(self):
    tab = self.current_tab()
    if not tab:
      return
    self.btn_back.setEnabled(tab.can_go_back())
    self.btn_forward.setEnabled(tab.can_go_forward())
    if tab.is_loading():
      self.btn_reload.setIcon(stop_icon(14))
      self.btn_reload.setToolTip("Dayandır")
    else:
      self.btn_reload.setIcon(reload_icon(14))
      self.btn_reload.setToolTip("Yenilə (Ctrl+R)")

  def update_tab_title(self, tab: BrowserTab, title: str):
    index = self._tab_index(tab)
    if index >= 0:
      display = title if len(title) <= 28 else title[:25] + "..."
      self.tab_bar.setTabText(index, display)
    if tab is self.current_tab():
      if title:
        self.setWindowTitle(f"{title} — MOD Browser")
      else:
        self.setWindowTitle("MOD Browser")

  def update_tab_icon(self, tab: BrowserTab, icon: QIcon):
    index = self._tab_index(tab)
    if index >= 0 and not icon.isNull():
      self.tab_bar.setTabIcon(index, icon)

  def update_address_bar(self, url: QUrl):
    tab = self.current_tab()
    if not tab or self.sender() != tab.view:
      return
    if (
      self.address_bar.hasFocus()
      or QApplication.focusWidget() is self.address_bar
    ):
      return
    url_str = url.toString()
    if url_str and url_str != "about:blank":
      self.address_bar.setText(url_str)
    elif tab is self.current_tab():
      self.address_bar.clear()
    self.refresh_bookmark_star()

  def update_load_progress(self, _progress: int):
    self._update_nav_buttons()

  def on_load_finished(self, _ok: bool):
    self._update_nav_buttons()
    self.refresh_bookmark_star()

  def _handle_download(self, download):
    handle_download(self, download, self._download_manager)

  def _on_download_updated(self, record):
    if record.state == "completed":
      self._toast.show_message(f"Yükləndi: {record.filename}")

  def closeEvent(self, event):
    QApplication.instance().removeEventFilter(self)
    for tab in list(self._tabs):
      if isinstance(tab, BrowserTab) and hasattr(tab.view, "setPage"):
        tab.view.setPage(None)
        tab.view.deleteLater()
    self._tabs.clear()
    self._profile.clearHttpCache()
    self._profile.cookieStore().deleteAllCookies()
    super().closeEvent(event)


def main():
  QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
  )
  app = QApplication(sys.argv)
  app.setApplicationName("MOD Browser")
  app.setOrganizationName("MOD")
  app.aboutToQuit.connect(cleanup_pycache)
  app.setStyle("Fusion")
  app.setStyleSheet(DARK_STYLE)
  window = BrowserWindow()
  window.show()
  sys.exit(app.exec())


if __name__ == "__main__":
  main()
