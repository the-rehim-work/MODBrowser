"""Incognito WebEngine profile — no persistent storage or logs."""

from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, qWebEngineChromiumVersion

from browser.session.settings import BrowserSettings
from browser.web.google_auth import GoogleAuthInterceptor, apply_firefox_identity
from browser.web.media import configure_media_settings


def configure_client_hints(profile: QWebEngineProfile):
  hints = profile.clientHints()
  if hints is None:
    return

  version = qWebEngineChromiumVersion()
  hints.setAllClientHintsEnabled(True)
  hints.setFullVersion(version)
  hints.setFullVersionList(
    {
      "Chromium": version,
      "Google Chrome": version,
      "Not-A.Brand": "99.0.0.0",
    }
  )
  if hasattr(hints, "setFormFactors"):
    hints.setFormFactors(["Desktop"])


def apply_browser_identity(profile: QWebEngineProfile, settings: BrowserSettings):
  profile.setHttpUserAgent(settings.user_agent())
  configure_client_hints(profile)


def create_incognito_profile(settings: BrowserSettings, parent=None):
  profile = QWebEngineProfile(parent)

  profile.setPersistentCookiesPolicy(
    QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
  )
  profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
  profile.setHttpCacheMaximumSize(64 * 1024 * 1024)
  profile.setPersistentPermissionsPolicy(
    QWebEngineProfile.PersistentPermissionsPolicy.StoreInMemory
  )
  profile.setUrlRequestInterceptor(GoogleAuthInterceptor())
  apply_browser_identity(profile, settings)

  web_settings = profile.settings()
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
  web_settings.setAttribute(QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, False)
  configure_media_settings(web_settings)

  return profile
