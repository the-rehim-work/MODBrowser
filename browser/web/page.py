"""Custom WebEngine page and view."""

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction, QContextMenuEvent
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMenu

from browser.ui.icons import back_icon, forward_icon, reload_icon
from browser.web.adblock import is_local_host

_LINK_OPEN_LABELS = (
  "open link in new tab",
  "open link in new window",
  "open in new tab",
  "open in new window",
)

_NAV_LABELS = ("back", "forward", "reload", "stop")


def _action_text(action: QAction) -> str:
  return action.text().replace("&", "").strip().lower()


def _is_duplicate_link_open_action(action: QAction) -> bool:
  if action.isSeparator():
    return False
  text = _action_text(action)
  return any(label in text for label in _LINK_OPEN_LABELS)


def _is_nav_action(action: QAction) -> bool:
  if action.isSeparator():
    return False
  return _action_text(action) in _NAV_LABELS


def _cleanup_menu_separators(menu: QMenu):
  actions = menu.actions()
  while actions and actions[0].isSeparator():
    menu.removeAction(actions[0])
    actions = menu.actions()
  while actions and actions[-1].isSeparator():
    menu.removeAction(actions[-1])
    actions = menu.actions()

  previous_was_separator = False
  for action in list(menu.actions()):
    if action.isSeparator():
      if previous_was_separator:
        menu.removeAction(action)
      previous_was_separator = True
    else:
      previous_was_separator = False


def _first_content_action(menu: QMenu) -> QAction | None:
  for action in menu.actions():
    if not action.isSeparator():
      return action
  return None


class BrowserView(QWebEngineView):
  def __init__(self, browser_window, parent=None):
    super().__init__(parent)
    self._browser_window = browser_window

  def _add_nav_actions(self, menu: QMenu, before: QAction | None):
    icon_color = "#e8eaed"
    back = QAction(back_icon(16, icon_color), "Geri", menu)
    back.setEnabled(self.page().history().canGoBack())
    back.triggered.connect(self.back)

    forward = QAction(forward_icon(16, icon_color), "İrəli", menu)
    forward.setEnabled(self.page().history().canGoForward())
    forward.triggered.connect(self.forward)

    reload = QAction(reload_icon(16, icon_color), "Yenilə", menu)
    reload.triggered.connect(self.reload)

    nav_actions = [back, forward, reload]
    if before is not None:
      for action in reversed(nav_actions):
        menu.insertAction(before, action)
      menu.insertSeparator(before)
      return

    for action in nav_actions:
      menu.addAction(action)
    menu.addSeparator()

  def contextMenuEvent(self, event: QContextMenuEvent):
    request = self.lastContextMenuRequest()
    link_url = request.linkUrl()
    has_link = link_url.isValid() and link_url.toString() not in ("", "about:blank")

    menu = self.createStandardContextMenu()
    if menu is None:
      menu = QMenu(self)
    menu.setObjectName("contextMenu")

    for action in list(menu.actions()):
      if _is_duplicate_link_open_action(action) or _is_nav_action(action):
        menu.removeAction(action)

    if has_link:
      url = link_url.toString()
      open_tab = QAction("Yeni tabda aç", menu)
      open_tab.triggered.connect(
        lambda _checked=False, link=url: self._browser_window.open_url_in_new_tab(
          link, background=True
        )
      )
      first = _first_content_action(menu)
      if first is not None:
        menu.insertAction(first, open_tab)
        menu.insertSeparator(first)
      else:
        menu.addAction(open_tab)
        menu.addSeparator()

    self._add_nav_actions(menu, _first_content_action(menu))
    _cleanup_menu_separators(menu)

    if menu.actions():
      menu.exec(event.globalPos())
    event.accept()


class BrowserPage(QWebEnginePage):
  def __init__(self, profile, browser_window, view: QWebEngineView):
    super().__init__(profile, view)
    self._browser_window = browser_window
    self.windowCloseRequested.connect(self._on_window_close_requested)
    self.permissionRequested.connect(self._on_permission_requested)
    self.featurePermissionRequested.connect(self._on_feature_permission_requested)

  def _on_permission_requested(self, permission):
    permission.grant()

  def _on_feature_permission_requested(self, url: QUrl, feature):
    self.setFeaturePermission(
      url,
      feature,
      QWebEnginePage.PermissionPolicy.PermissionGrantedByUser,
    )

  def javaScriptConsoleMessage(self, _level, _message, _line_number, _source_id):
    pass

  def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool):
    if (
      is_main_frame
      and self._browser_window.settings.https_only
      and url.scheme() == "http"
      and url.host()
      and not is_local_host(url.host())
    ):
      secure = QUrl(url)
      secure.setScheme("https")
      self.setUrl(secure)
      return False
    return super().acceptNavigationRequest(url, nav_type, is_main_frame)

  def createWindow(self, wtype):
    bw = self._browser_window
    background = wtype == QWebEnginePage.WebWindowType.WebBrowserBackgroundTab
    current_index = bw.tab_bar.currentIndex()
    tab = bw.add_tab()
    if background and current_index >= 0:
      bw.tab_bar.setCurrentIndex(current_index)
    return tab.view.page()

  def _on_window_close_requested(self):
    for i, tab in enumerate(self._browser_window._tabs):
      if not hasattr(tab, "view"):
        continue
      if tab.view.page() is self:
        if self._browser_window.tab_bar.count() <= 1:
          self._browser_window.reset_tab(tab)
        else:
          self._browser_window.close_tab(i)
        return
