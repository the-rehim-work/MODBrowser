"""Choose the best embedded browser engine for the platform."""

import sys

from browser.web.page import BrowserView
from browser.web.webview2_view import WEBVIEW2_AVAILABLE, WebView2BrowserView


def preferred_engine() -> str:
  if sys.platform == "win32" and WEBVIEW2_AVAILABLE:
    return "webview2"
  return "webengine"


def create_browser_view(browser_window, parent=None):
  if preferred_engine() == "webview2":
    return WebView2BrowserView(browser_window, parent)
  return BrowserView(browser_window, parent)
