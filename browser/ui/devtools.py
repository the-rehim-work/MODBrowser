"""Chromium DevTools paneli (Elements / Network / Console / Sources)."""

from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QDockWidget


class DevToolsDock(QDockWidget):
  def __init__(self, parent=None):
    super().__init__("DevTools", parent)
    self.setObjectName("devToolsDock")
    self.setAllowedAreas(
      Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
    )
    self.view = QWebEngineView()
    self.view.setObjectName("devToolsView")
    self.setWidget(self.view)
    self._inspected = None

  def inspect(self, page):
    if page is self._inspected:
      return
    if page is not None and not hasattr(page, "setDevToolsPage"):
      return
    self.detach()
    self._inspected = page
    if page is not None:
      page.setDevToolsPage(self.view.page())

  def detach(self):
    if self._inspected is not None:
      try:
        self._inspected.setDevToolsPage(None)
      except Exception:
        pass
    self._inspected = None
