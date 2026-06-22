"""Browser tab with embedded web view."""

import ipaddress

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from browser.constants import NEW_TAB_TITLE
from browser.web.adblock import is_local_host
from browser.web.engine import create_browser_view, preferred_engine
from browser.web.page import BrowserPage

_DIRECT_SCHEMES = (
  "http://",
  "https://",
  "file://",
  "about:",
  "data:",
  "view-source:",
  "blob:",
  "chrome://",
)


def _looks_like_raw_url(text: str) -> bool:
  return text.lower().startswith(_DIRECT_SCHEMES)


def _is_ip(text: str) -> bool:
  try:
    ipaddress.ip_address(text.strip("[]"))
    return True
  except ValueError:
    return False


def _looks_like_host(text: str) -> bool:
  if " " in text:
    return False
  head = text.split("/", 1)[0].split("?", 1)[0]
  if not head:
    return False
  host = head
  if head.count(":") == 1:
    maybe_host, maybe_port = head.rsplit(":", 1)
    if maybe_port.isdigit() and maybe_host:
      return True
    host = head
  if host == "localhost":
    return True
  if _is_ip(host):
    return True
  return "." in host and not host.startswith(".") and not host.endswith(".")


def tab_display_title(title: str = "", url: QUrl | None = None) -> str:
  cleaned = (title or "").strip()
  if (
    cleaned
    and cleaned.lower() not in ("about:blank", "yeni tab")
    and not _looks_like_raw_url(cleaned)
  ):
    return cleaned
  if url is None or not url.isValid():
    return NEW_TAB_TITLE

  scheme = url.scheme().lower()
  if scheme == "about" or url.toString().strip() == "about:blank":
    return NEW_TAB_TITLE
  if scheme == "data":
    return NEW_TAB_TITLE
  if scheme == "file":
    name = url.fileName().strip()
    return name or "Fayl"
  if scheme == "blob":
    return "Səhifə"

  host = url.host().strip()
  if host:
    return host.removeprefix("www.")

  url_text = url.toString().strip()
  if url_text and not _looks_like_raw_url(url_text):
    return url_text
  return NEW_TAB_TITLE


class BrowserTab(QWidget):
  def __init__(self, profile: QWebEngineProfile, browser_window, parent=None):
    super().__init__(parent)
    self._browser_window = browser_window
    self._zoom = 1.0
    self._uses_webengine = preferred_engine() == "webengine"

    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    self.view = create_browser_view(browser_window)
    if self._uses_webengine:
      page = BrowserPage(profile, browser_window, self.view)
      self.view.setPage(page)
    layout.addWidget(self.view)

    self.view.titleChanged.connect(self._on_title_changed)
    self.view.urlChanged.connect(self._on_url_changed)
    self.view.loadProgress.connect(self._on_load_progress)
    self.view.loadFinished.connect(self._on_load_finished)
    self.view.iconChanged.connect(self._on_icon_changed)

    self._on_title_changed(self.view.title())
    self._on_url_changed(self.view.url())

  def _on_title_changed(self, title: str):
    display = tab_display_title(title, self.view.url())
    self.window().update_tab_title(self, display)

  def _on_url_changed(self, url: QUrl):
    self._browser_window.update_google_auth_state(self, url)
    self.window().update_address_bar(url)
    display = tab_display_title(self.view.title(), url)
    self.window().update_tab_title(self, display)

  def _on_load_progress(self, progress: int):
    self.window().update_load_progress(progress)

  def _on_load_finished(self, ok: bool):
    self._browser_window.update_google_auth_state(self, self.view.url())
    if ok:
      url = self.view.url().toString()
      self.window().record_visit(url, self.view.title())
    self.window().on_load_finished(ok)

  def _on_icon_changed(self, icon: QIcon):
    self.window().update_tab_icon(self, icon)

  def _normalize_url(self, url: str) -> str:
    text = url.strip()
    if not text:
      return ""

    if _looks_like_raw_url(text):
      if (
        text.lower().startswith("http://")
        and self._browser_window.settings.https_only
        and not is_local_host(QUrl(text).host())
      ):
        return "https://" + text[7:]
      return text

    if _looks_like_host(text):
      head = text.split("/", 1)[0]
      prefix = "http://" if is_local_host(head) else "https://"
      return prefix + text

    query = bytes(QUrl.toPercentEncoding(text)).decode("ascii")
    return "https://www.google.com/search?q=" + query

  def navigate(self, url: str):
    text = self._normalize_url(url)
    if text:
      qurl = QUrl(text)
      self._browser_window.update_google_auth_state(self, qurl, immediate=True)
      self.view.setUrl(qurl)

  def go_back(self):
    self.view.back()

  def go_forward(self):
    self.view.forward()

  def reload(self):
    self.view.reload()

  def reload_bypass_cache(self):
    page = self.view.page()
    if hasattr(page, "triggerAction") and hasattr(page, "WebAction"):
      page.triggerAction(page.WebAction.ReloadAndBypassCache)
    else:
      self.view.reload()

  def stop(self):
    self.view.stop()

  def can_go_back(self) -> bool:
    return self.view.history().canGoBack()

  def can_go_forward(self) -> bool:
    return self.view.history().canGoForward()

  def is_loading(self) -> bool:
    page = self.view.page()
    if hasattr(page, "isLoading"):
      return page.isLoading()
    return getattr(self.view, "_loading", False)

  def current_url(self) -> QUrl:
    return self.view.url()

  def zoom_factor(self) -> float:
    return self._zoom

  def set_zoom(self, factor: float):
    self._zoom = max(0.25, min(factor, 5.0))
    self.view.setZoomFactor(self._zoom)
    self.window().update_zoom_display(self._zoom)

  def zoom_in(self):
    self.set_zoom(self._zoom * 1.1)

  def zoom_out(self):
    self.set_zoom(self._zoom / 1.1)

  def reset_zoom(self):
    self.set_zoom(1.0)
