"""Cookie capture and restore for the WebEngine profile."""

from PyQt6.QtCore import QDateTime, QObject, QUrl
from PyQt6.QtNetwork import QNetworkCookie

_SAME_SITE_TO_NAME = {}
_NAME_TO_SAME_SITE = {}
if hasattr(QNetworkCookie, "SameSite"):
  _SAME_SITE_TO_NAME = {
    QNetworkCookie.SameSite.None_: "none",
    QNetworkCookie.SameSite.Lax: "lax",
    QNetworkCookie.SameSite.Strict: "strict",
  }
  _NAME_TO_SAME_SITE = {name: policy for policy, name in _SAME_SITE_TO_NAME.items()}


def serialize_cookie(cookie: QNetworkCookie) -> dict:
  row = {
    "name": bytes(cookie.name()).decode("utf-8", "replace"),
    "value": bytes(cookie.value()).decode("utf-8", "replace"),
    "domain": cookie.domain(),
    "path": cookie.path(),
    "secure": cookie.isSecure(),
    "http_only": cookie.isHttpOnly(),
    "expires": None,
    "same_site": None,
  }
  if not cookie.isSessionCookie():
    expiry = cookie.expirationDate()
    if expiry.isValid():
      row["expires"] = expiry.toSecsSinceEpoch()
  if hasattr(cookie, "sameSitePolicy"):
    row["same_site"] = _SAME_SITE_TO_NAME.get(cookie.sameSitePolicy())
  return row


def deserialize_cookie(row: dict):
  domain = (row.get("domain") or "").strip()
  if not domain:
    return None, None
  cookie = QNetworkCookie()
  cookie.setName(str(row.get("name", "")).encode("utf-8"))
  cookie.setValue(str(row.get("value", "")).encode("utf-8"))
  cookie.setDomain(domain)
  cookie.setPath(row.get("path") or "/")
  cookie.setSecure(bool(row.get("secure")))
  cookie.setHttpOnly(bool(row.get("http_only")))
  expires = row.get("expires")
  if expires is not None:
    cookie.setExpirationDate(QDateTime.fromSecsSinceEpoch(int(expires)))
  same_site = row.get("same_site")
  if same_site in _NAME_TO_SAME_SITE and hasattr(cookie, "setSameSitePolicy"):
    cookie.setSameSitePolicy(_NAME_TO_SAME_SITE[same_site])
  host = domain[1:] if domain.startswith(".") else domain
  origin = QUrl(f"https://{host}/")
  return cookie, origin


class CookieJar(QObject):
  def __init__(self, profile, parent=None):
    super().__init__(parent)
    self._store = profile.cookieStore()
    self._cookies: dict = {}
    self._store.cookieAdded.connect(self._on_added)
    self._store.cookieRemoved.connect(self._on_removed)

  def _key(self, cookie: QNetworkCookie):
    return (cookie.domain(), cookie.path(), bytes(cookie.name()))

  def _on_added(self, cookie: QNetworkCookie):
    self._cookies[self._key(cookie)] = QNetworkCookie(cookie)

  def _on_removed(self, cookie: QNetworkCookie):
    self._cookies.pop(self._key(cookie), None)

  def export_cookies(self) -> list:
    return [serialize_cookie(cookie) for cookie in self._cookies.values()]

  def import_cookies(self, rows) -> int:
    count = 0
    for row in rows:
      cookie, origin = deserialize_cookie(row)
      if cookie is None:
        continue
      self._store.setCookie(cookie, origin)
      count += 1
    return count