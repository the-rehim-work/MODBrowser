"""Windows WebView2 wrapper with a QWebEngineView-like API."""


from __future__ import annotations

import sys

from PyQt6.QtCore import Qt, QElapsedTimer, QEventLoop, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
from browser.web.adblock import is_local_host
try:
  from qtwebview2 import QtWebView2Widget

  WEBVIEW2_AVAILABLE = True
except ImportError:
  WEBVIEW2_AVAILABLE = False
  QtWebView2Widget = None


class WebView2PageStub:
  def __init__(self, view: "WebView2BrowserView"):
    self._view = view

  def isLoading(self) -> bool:
    return self._view._loading

  def findText(self, text: str, _flags=0, callback=None):
    if not text:
      self._view._widget.evaluate_js(
        "window.getSelection().removeAllRanges();",
        lambda _r: callback(0) if callback else None,
      )
      return
    script = (
      f"window.find({text!r}, false, false, true); "
      "window.getSelection().toString().length > 0"
    )
    self._view._widget.evaluate_js(
      script,
      lambda r: callback(1 if isinstance(r, dict) and r.get("success") and r.get("result") else 0)
      if callback
      else None,
    )


class WebView2BrowserView(QWidget):
  titleChanged = pyqtSignal(str)
  urlChanged = pyqtSignal(QUrl)
  loadProgress = pyqtSignal(int)
  loadFinished = pyqtSignal(bool)
  iconChanged = pyqtSignal(QIcon)

  def __init__(self, browser_window, parent=None):
    super().__init__(parent)
    self._browser_window = browser_window
    self._loading = False
    self._zoom = 1.0
    self._current_url = QUrl()
    self._page = WebView2PageStub(self)
    self._input_blocked = False

    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    self._widget = QtWebView2Widget(
      parent=self,
      context_menus=True,
      handle_new_window=True,
      lazyload=False,
      fullscreen_support=True,
    )
    layout.addWidget(self._widget)
    self._widget.bridge.domContentLoaded.connect(self._on_dom_loaded)
    self._widget.bridge.initialization_done.connect(self._on_initialized)

  def page(self):
    return self._page

  def _on_initialized(self, success: bool, _error: str):
    if not success:
      self.loadFinished.emit(False)
      return
    if self._input_blocked:
      self.set_input_blocked(True)
    self._hook_webview_events()

  def _hook_webview_events(self):
    if not self._widget.is_ready:
      return
    try:
      core = self._widget._webview.CoreWebView2
      core.DocumentTitleChanged += self._on_document_title_changed
      core.NavigationCompleted += self._on_navigation_completed
      core.NewWindowRequested += self._on_new_window_requested
      core.NavigationStarting += self._on_navigation_starting
      core.SourceChanged += self._on_source_changed
      self._install_resource_blocker(core)
    except Exception:
      pass

  def _on_navigation_starting(self, _sender, args):
    if not self._browser_window.settings.https_only:
      return
    try:
      uri = args.Uri
    except Exception:
      return
    q = QUrl(uri)
    if q.scheme() != "http" or not q.host() or is_local_host(q.host()):
      return
    secure = QUrl(q)
    secure.setScheme("https")
    try:
      args.Cancel = True
    except Exception:
      return
    QTimer.singleShot(0, lambda u=secure.toString(): self._widget.load_url(u))

  def _install_resource_blocker(self, core):
    try:
      from Microsoft.Web.WebView2.Core import CoreWebView2WebResourceContext
      core.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All)
    except Exception:
      try:
        core.AddWebResourceRequestedFilter("*", 0)
      except Exception:
        return
    try:
      core.WebResourceRequested += self._on_web_resource_requested
    except Exception:
      pass

  def _on_web_resource_requested(self, _sender, args):
    blocker = getattr(self._browser_window, "_content_blocker", None)
    if blocker is None or not blocker.is_enabled():
      return
    try:
      url = args.Request.Uri
      ctx = self._resource_context_name(args.ResourceContext)
    except Exception:
      return
    if not blocker.should_block(url, self._current_url.toString(), ctx):
      return
    try:
      env = self._widget._webview.CoreWebView2.Environment
      args.Response = env.CreateWebResourceResponse(None, 403, "Blocked", "")
    except Exception:
      pass

  def _resource_context_name(self, ctx):
    name = str(ctx).rsplit(".", 1)[-1]
    return {
      "Document": "document",
      "Stylesheet": "stylesheet",
      "Image": "image",
      "Media": "media",
      "Font": "font",
      "Script": "script",
      "XmlHttpRequest": "xmlhttprequest",
      "Fetch": "xmlhttprequest",
      "WebSocket": "websocket",
      "Ping": "ping",
    }.get(name, "other")

  def open_dev_tools(self):
    if not self._widget.is_ready:
      return
    try:
      self._widget._webview.CoreWebView2.OpenDevToolsWindow()
    except Exception:
      pass

  def _on_new_window_requested(self, _sender, args):
    try:
      uri = args.Uri
      args.Handled = True
    except Exception:
      return
    QTimer.singleShot(0, lambda: self._browser_window.open_url_in_new_tab(uri))

  def _on_document_title_changed(self, _sender, _args):
    QTimer.singleShot(0, self._emit_document_title)

  def _on_navigation_completed(self, _sender, _args):
    QTimer.singleShot(0, self._emit_document_title)
    QTimer.singleShot(0, self._refresh_metadata)

  def _on_source_changed(self, _sender, _args):
    QTimer.singleShot(0, self._emit_source)

  def _emit_source(self):
    if not self._widget.is_ready:
      return
    try:
      source = self._widget._webview.CoreWebView2.Source
    except Exception:
      return
    if not source:
      return
    url = QUrl(source)
    if url.isValid():
      self._current_url = url
      self.urlChanged.emit(url)

  def focus_page(self):
    self.setFocus()
    if not self._widget.is_ready:
      return
    webview = getattr(self._widget, "_webview", None)
    if webview is None or getattr(webview, "IsDisposed", False):
      return
    if sys.platform != "win32":
      return
    try:
      import ctypes
      ctypes.windll.user32.SetFocus(webview.Handle.ToInt32())
    except Exception:
      pass

  def _emit_document_title(self):
    title = self.title().strip()
    if title:
      self.titleChanged.emit(title)

  def _on_dom_loaded(self):
    self._loading = False
    self.loadProgress.emit(100)
    self.loadFinished.emit(True)
    self._refresh_metadata()

  def _refresh_metadata(self):
    self._widget.evaluate_js(
      "({ title: document.title, href: location.href })",
      self._metadata_callback,
    )

  def _metadata_callback(self, result: dict):
    if not isinstance(result, dict) or not result.get("success"):
      return
    payload = result.get("result")
    if not isinstance(payload, dict):
      return
    title = payload.get("title") or ""
    href = payload.get("href") or ""
    if title:
      self.titleChanged.emit(title)
    elif href:
      url = QUrl(href)
      if url.isValid() and url.host():
        self.titleChanged.emit(url.host().removeprefix("www."))
    if href:
      url = QUrl(href)
      if url.isValid():
        self._current_url = url
        self.urlChanged.emit(url)

  def setHtml(self, html: str, base_url: QUrl | None = None):
    self._loading = True
    self.loadProgress.emit(10)
    base = (
      base_url.toString()
      if isinstance(base_url, QUrl) and base_url.isValid()
      else "about:blank"
    )
    self._current_url = QUrl(base)
    self._widget.load_html(html, base)
    self.urlChanged.emit(self._current_url)

  def setUrl(self, url: QUrl):
    text = url.toString()
    self._loading = True
    self.loadProgress.emit(10)
    if not text or text == "about:blank":
      self._widget.load_html("<html><body></body></html>")
      self._current_url = QUrl("about:blank")
      self._loading = False
      self.urlChanged.emit(self._current_url)
      self.loadFinished.emit(True)
      return
    self._current_url = url
    self.urlChanged.emit(url)
    self._widget.load_url(text)

  def url(self) -> QUrl:
    if self._widget.is_ready:
      try:
        uri = self._widget._webview.CoreWebView2.Source
        if uri is not None:
          return QUrl(uri.ToString())
      except Exception:
        pass
    return self._current_url

  def title(self) -> str:
    if self._widget.is_ready:
      try:
        return self._widget._webview.CoreWebView2.DocumentTitle or ""
      except Exception:
        pass
    return ""

  def back(self):
    if not self._widget.is_ready:
      return
    core = self._widget._webview.CoreWebView2
    if core.CanGoBack:
      self._loading = True
      self.loadProgress.emit(10)
      core.GoBack()

  def forward(self):
    if not self._widget.is_ready:
      return
    core = self._widget._webview.CoreWebView2
    if core.CanGoForward:
      self._loading = True
      self.loadProgress.emit(10)
      core.GoForward()

  def reload(self):
    self._loading = True
    self.loadProgress.emit(10)
    self._widget.reload()

  def stop(self):
    if not self._widget.is_ready:
      return
    self._widget._webview.CoreWebView2.Stop()
    self._loading = False

  def open_dev_tools(self):
    if not self._widget.is_ready:
      return
    try:
      self._widget._webview.CoreWebView2.OpenDevToolsWindow()
    except Exception:
      pass

  def history(self):
    return self

  def canGoBack(self) -> bool:
    if not self._widget.is_ready:
      return False
    return bool(self._widget._webview.CoreWebView2.CanGoBack)

  def canGoForward(self) -> bool:
    if not self._widget.is_ready:
      return False
    return bool(self._widget._webview.CoreWebView2.CanGoForward)

  def setZoomFactor(self, factor: float):
    self._zoom = factor
    if not self._widget.is_ready:
      return
    try:
      self._widget._webview.ZoomFactor = float(factor)
    except Exception:
      pass

  def zoomFactor(self) -> float:
    if self._widget.is_ready:
      try:
        return float(self._widget._webview.ZoomFactor)
      except Exception:
        pass
    return self._zoom

  def set_input_blocked(self, blocked: bool):
    self._input_blocked = blocked
    container = getattr(self._widget, "_container", None)
    if container is not None:
      container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, blocked)
    if not self._widget.is_ready:
      return
    webview = getattr(self._widget, "_webview", None)
    if webview is None or webview.IsDisposed:
      return
    if sys.platform != "win32":
      return
    try:
      import ctypes
      ctypes.windll.user32.EnableWindow(webview.Handle.ToInt32(), not blocked)
    except Exception:
      pass

  def createStandardContextMenu(self):
    return None

  def lastContextMenuRequest(self):
    return None

  def _cookie_manager(self):
    if not self._widget.is_ready:
      return None
    try:
      return self._widget._webview.CoreWebView2.CookieManager
    except Exception:
      return None

  def export_cookies(self) -> list:
    manager = self._cookie_manager()
    if manager is None:
      return []
    try:
      task = manager.GetCookiesAsync(None)
    except Exception:
      return []
    app = QApplication.instance()
    if app is None:
      return []
    timer = QElapsedTimer()
    timer.start()
    while not task.IsCompleted and timer.elapsed() < 5000:
      app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents, 25)
    if not task.IsCompleted:
      return []
    try:
      cookies = task.Result
    except Exception:
      return []
    return self._serialize_cookies(cookies)

  def _serialize_cookies(self, cookies) -> list:
    rows = []
    for cookie in cookies:
      try:
        expires = float(cookie.Expires)
      except Exception:
        expires = -1.0
      session = bool(getattr(cookie, "IsSession", expires < 0))
      rows.append(
        {
          "name": cookie.Name,
          "value": cookie.Value,
          "domain": cookie.Domain,
          "path": cookie.Path,
          "secure": bool(cookie.IsSecure),
          "http_only": bool(cookie.IsHttpOnly),
          "expires": None if session or expires < 0 else expires,
          "same_site": self._same_site_name(cookie.SameSite),
        }
      )
    return rows

  def import_cookies(self, rows) -> int:
    manager = self._cookie_manager()
    if manager is None:
      return 0
    count = 0
    for row in rows:
      domain = (row.get("domain") or "").strip()
      if not domain:
        continue
      try:
        cookie = manager.CreateCookie(
          row.get("name", ""), row.get("value", ""), domain, row.get("path") or "/"
        )
        cookie.IsSecure = bool(row.get("secure"))
        cookie.IsHttpOnly = bool(row.get("http_only"))
        expires = row.get("expires")
        if expires is not None:
          cookie.Expires = float(expires)
        same_site = self._same_site_kind(row.get("same_site"))
        if same_site is not None:
          try:
            cookie.SameSite = same_site
          except Exception:
            pass
        manager.AddOrUpdateCookie(cookie)
        count += 1
      except Exception:
        continue
    return count

  def _same_site_name(self, kind):
    name = str(kind).rsplit(".", 1)[-1].lower()
    return name if name in ("none", "lax", "strict") else None

  def _same_site_kind(self, name):
    return {"none": 0, "lax": 1, "strict": 2}.get(name)