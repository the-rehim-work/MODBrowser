"""Şəbəkə səviyyəsində reklam/izləyici bloku + https-only + Google auth eyniləşdirməsi."""

import ipaddress
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo

from browser.web.google_auth import FIREFOX_UA, is_google_auth_url

_FILTER_DIR = Path(__file__).resolve().parent.parent.parent / "filters"

SEED_FILTERS = [
  "||doubleclick.net^",
  "||googlesyndication.com^",
  "||googleadservices.com^",
  "||googletagservices.com^",
  "||googletagmanager.com^",
  "||google-analytics.com^",
  "||analytics.google.com^",
  "||adservice.google.com^",
  "||pagead2.googlesyndication.com^",
  "||partner.googleadservices.com^",
  "||amazon-adsystem.com^",
  "||adnxs.com^",
  "||rubiconproject.com^",
  "||pubmatic.com^",
  "||openx.net^",
  "||criteo.com^",
  "||criteo.net^",
  "||casalemedia.com^",
  "||smartadserver.com^",
  "||adform.net^",
  "||taboola.com^",
  "||outbrain.com^",
  "||scorecardresearch.com^",
  "||quantserve.com^",
  "||quantcount.com^",
  "||moatads.com^",
  "||bidswitch.net^",
  "||3lift.com^",
  "||sharethrough.com^",
  "||teads.tv^",
  "||yieldmo.com^",
  "||connect.facebook.net^",
  "||facebook.com/tr^",
  "||analytics.tiktok.com^",
  "||ads-twitter.com^",
  "||analytics.twitter.com^",
  "||static.ads-twitter.com^",
  "||hotjar.com^",
  "||mixpanel.com^",
  "||segment.com^",
  "||segment.io^",
  "||fullstory.com^",
  "||clarity.ms^",
  "||bat.bing.com^",
  "||mc.yandex.ru^",
  "||an.yandex.ru^",
  "||yandexadexchange.net^",
  "||adfox.ru^",
  "||top-fwz1.mail.ru^",
  "||ads.vk.com^",
  "||branch.io^",
  "||app-measurement.com^",
  "||crashlytics.com^",
]

GENERIC_COSMETIC_CSS = """
.adsbygoogle,
ins.adsbygoogle,
[id^="google_ads_"],
[id^="div-gpt-ad"],
[id^="aswift_"],
iframe[src*="doubleclick.net"],
iframe[src*="googlesyndication"],
iframe[src*="amazon-adsystem"],
iframe[src*="adnxs.com"],
.taboola,
[id^="taboola-"],
[class^="trc_related"],
.OUTBRAIN,
[data-widget-id^="AR_"],
.ad-banner,
.advertisement,
[class*="sponsored-ad"] {
  display: none !important;
}
"""


def is_local_host(host: str) -> bool:
  host = (host or "").strip().lower()
  if not host:
    return False
  if host in ("localhost", "127.0.0.1", "::1"):
    return True
  if "." not in host and ":" not in host:
    return True
  candidate = host.split(":", 1)[0] if host.count(":") == 1 and host.rsplit(":", 1)[1].isdigit() else host
  candidate = candidate.strip("[]")
  try:
    return ipaddress.ip_address(candidate).is_private
  except ValueError:
    return candidate == "localhost"


def _rule_domain(rule):
  rule = rule.strip()
  if not rule.startswith("||"):
    return ""
  body = rule[2:]
  end = len(body)
  terminator = ""
  for sep in ("^", "/", "*", "?", "$", "="):
    idx = body.find(sep)
    if idx != -1 and idx < end:
      end = idx
      terminator = sep
  if terminator == "/":
    return ""
  host = body[:end].strip().lower().lstrip(".")
  return host if "." in host else ""


def _host_of(url):
  try:
    return QUrl(url).host().lower()
  except Exception:
    return ""


def _load_local_lists():
  lists = []
  if _FILTER_DIR.is_dir():
    for path in sorted(_FILTER_DIR.glob("*.txt")):
      try:
        lists.append(path.read_text(encoding="utf-8", errors="ignore"))
      except OSError:
        continue
  return lists


def _build_resource_map():
  rt = QWebEngineUrlRequestInfo.ResourceType
  pairs = {
    "ResourceTypeMainFrame": "document",
    "ResourceTypeSubFrame": "subdocument",
    "ResourceTypeStylesheet": "stylesheet",
    "ResourceTypeScript": "script",
    "ResourceTypeImage": "image",
    "ResourceTypeFontResource": "font",
    "ResourceTypeObject": "object",
    "ResourceTypeMedia": "media",
    "ResourceTypeXhr": "xmlhttprequest",
    "ResourceTypePing": "ping",
    "ResourceTypeFavicon": "image",
    "ResourceTypeWebSocket": "websocket",
  }
  mapped = {}
  for name, kind in pairs.items():
    member = getattr(rt, name, None)
    if member is not None:
      mapped[member] = kind
  return mapped


class _RustEngine:
  def __init__(self, filters, extra_lists):
    import adblock

    filter_set = adblock.FilterSet()
    filter_set.add_filters(filters)
    for text in extra_lists:
      filter_set.add_filter_list(text)
    self._engine = adblock.Engine(filter_set=filter_set)

  def is_blocked(self, request_url, source_url, request_type):
    result = self._engine.check_network_urls(
      url=request_url,
      source_url=source_url or request_url,
      request_type=request_type,
    )
    return result.matched


class _DomainEngine:
  def __init__(self, filters, extra_lists):
    self._domains = set()
    for rule in filters:
      domain = _rule_domain(rule)
      if domain:
        self._domains.add(domain)
    for text in extra_lists:
      for line in text.splitlines():
        self._absorb_line(line)

  def _absorb_line(self, line):
    line = line.strip()
    if not line or line.startswith(("!", "#", "[", "@")):
      return
    domain = _rule_domain(line)
    if not domain and " " in line:
      parts = line.split()
      candidate = parts[-1].lower().lstrip(".")
      if "." in candidate and "/" not in candidate:
        domain = candidate
    if domain:
      self._domains.add(domain)

  def is_blocked(self, request_url, source_url, request_type):
    host = _host_of(request_url)
    while host:
      if host in self._domains:
        return True
      if "." not in host:
        return False
      host = host.split(".", 1)[1]
    return False


class ContentBlocker(QWebEngineUrlRequestInterceptor):
  def __init__(self, settings, parent=None):
    super().__init__(parent)
    self._settings = settings
    self._enabled = settings.adblock_enabled
    self._blocked_count = 0
    self._resource_map = _build_resource_map()
    self._engine = self._build_engine()

  def _build_engine(self):
    extra = _load_local_lists()
    try:
      return _RustEngine(SEED_FILTERS, extra)
    except Exception:
      return _DomainEngine(SEED_FILTERS, extra)

  @property
  def blocked_count(self):
    return self._blocked_count

  def is_enabled(self):
    return self._enabled

  def set_enabled(self, value):
    self._enabled = bool(value)

  def reset_count(self):
    self._blocked_count = 0

  def interceptRequest(self, info):
    url = info.requestUrl()

    if is_google_auth_url(url):
      info.setHttpHeader(b"User-Agent", FIREFOX_UA.encode("ascii"))

    request_type = self._resource_map.get(info.resourceType(), "other")

    if (
      self._settings.https_only
      and url.scheme() == "http"
      and url.host()
      and not is_local_host(url.host())
      and request_type in ("document", "subdocument")
    ):
      secure = QUrl(url)
      secure.setScheme("https")
      info.redirect(secure)
      return

    if not self._enabled or request_type == "document":
      return

    if self._engine.is_blocked(
      url.toString(),
      info.firstPartyUrl().toString(),
      request_type,
    ):
      info.block(True)
      self._blocked_count += 1
