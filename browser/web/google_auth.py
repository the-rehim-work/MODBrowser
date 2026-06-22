"""Google account login compatibility for embedded WebEngine."""

import re

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor

FIREFOX_UA = (
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) "
  "Gecko/20100101 Firefox/135.0"
)

_GMAIL_INBOX_PATH = re.compile(r"^/mail/u/\d+", re.IGNORECASE)


def _is_gmail_inbox(url: QUrl) -> bool:
  if url.host().lower() != "mail.google.com":
    return False
  path = url.path()
  if _GMAIL_INBOX_PATH.match(path):
    return True
  return path.lower().startswith("/mail/mu/")


def is_google_auth_url(url: QUrl) -> bool:
  if not url.isValid() or url.scheme() not in ("http", "https"):
    return False

  host = url.host().lower()

  if host == "accounts.google.com":
    return True

  if host == "mail.google.com":
    return not _is_gmail_inbox(url)

  if host in {"google.com", "www.google.com"}:
    path = url.path().lower()
    return path.startswith("/signin") or path.startswith("/servicelogin")

  return False


def apply_firefox_identity(profile: QWebEngineProfile):
  profile.setHttpUserAgent(FIREFOX_UA)
  hints = profile.clientHints()
  if hints is not None:
    hints.setAllClientHintsEnabled(False)


class GoogleAuthInterceptor(QWebEngineUrlRequestInterceptor):
  def interceptRequest(self, info: QWebEngineUrlRequestInfo):
    if not is_google_auth_url(info.requestUrl()):
      return

    info.setHttpHeader(b"User-Agent", FIREFOX_UA.encode("ascii"))
