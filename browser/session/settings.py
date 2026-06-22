"""Browser settings (session-only, not persisted to disk)."""

import re
from dataclasses import dataclass

from PyQt6.QtWebEngineCore import QWebEngineProfile, qWebEngineChromiumVersion

MOBILE_IPHONE_UA = (
  "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)

USER_AGENT_PRESETS = {
  "desktop": "Desktop",
  "iphone": "iPhone",
  "android": "Android",
}


def _chromium_major() -> str:
  return qWebEngineChromiumVersion().split(".", 1)[0]


def build_user_agent(key: str) -> str:
  if key == "desktop":
    ua = QWebEngineProfile.defaultProfile().httpUserAgent()
    return re.sub(r"QtWebEngine/\S+\s*", "", ua).strip()
  if key == "iphone":
    return MOBILE_IPHONE_UA
  if key == "android":
    major = _chromium_major()
    return (
      f"Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
      f"(KHTML, like Gecko) Chrome/{major}.0.0.0 Mobile Safari/537.36"
    )
  return build_user_agent("desktop")


@dataclass
class BrowserSettings:
  https_only: bool = True
  idle_minutes: int = 30
  user_agent_key: str = "desktop"
  adblock_enabled: bool = True
  proxy_enabled: bool = False
  proxy_type: str = "http"
  proxy_host: str = ""
  proxy_port: int = 8080

  def user_agent(self) -> str:
    return build_user_agent(self.user_agent_key)
