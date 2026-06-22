"""WebEngine media playback configuration and codec checks."""

from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWebEngineCore import QWebEngineSettings


def configure_media_settings(web_settings):
  web_settings.setAttribute(
    QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False
  )
  web_settings.setAttribute(
    QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True
  )
  web_settings.setAttribute(
    QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True
  )
  web_settings.setAttribute(
    QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True
  )


def check_h264_support(page) -> bool:
  loop = QEventLoop()
  result = {"ok": False}

  def done(value):
    result["ok"] = bool(value)
    loop.quit()

  page.runJavaScript(
    "document.createElement('video').canPlayType("
    "'video/mp4; codecs=\"avc1.42E01E, mp4a.40.2\"')"
    ")",
    done,
  )
  QTimer.singleShot(3000, loop.quit)
  loop.exec()
  return result["ok"]
