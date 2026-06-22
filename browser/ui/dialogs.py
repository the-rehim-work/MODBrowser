"""Settings and proxy dialogs."""

from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkProxy
from PyQt6.QtWidgets import (
  QCheckBox,
  QComboBox,
  QDialog,
  QDialogButtonBox,
  QFormLayout,
  QHBoxLayout,
  QLabel,
  QLineEdit,
  QSpinBox,
  QVBoxLayout,
  QWidget,
)

from browser.session.settings import BrowserSettings, USER_AGENT_PRESETS
from browser.web.profile import apply_browser_identity


def apply_proxy(settings: BrowserSettings):
  if not settings.proxy_enabled or not settings.proxy_host.strip():
    QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
    return

  proxy_type = {
    "http": QNetworkProxy.ProxyType.HttpProxy,
    "socks5": QNetworkProxy.ProxyType.Socks5Proxy,
  }.get(settings.proxy_type, QNetworkProxy.ProxyType.HttpProxy)

  proxy = QNetworkProxy(proxy_type, settings.proxy_host.strip(), settings.proxy_port)
  QNetworkProxy.setApplicationProxy(proxy)


class SettingsDialog(QDialog):
  def __init__(self, settings: BrowserSettings, profile, parent=None):
    super().__init__(parent)
    self._settings = settings
    self._profile = profile
    self.setWindowTitle("Parametrlər")
    self.setMinimumWidth(420)

    layout = QVBoxLayout(self)

    self.https_cb = QCheckBox("HTTPS yalnız rejimi")
    self.https_cb.setChecked(settings.https_only)

    idle_row = QHBoxLayout()
    idle_row.addWidget(QLabel("Hərəkətsizlikdən sonra bağla (dəq.):"))
    self.idle_spin = QSpinBox()
    self.idle_spin.setRange(0, 240)
    self.idle_spin.setValue(settings.idle_minutes)
    self.idle_spin.setSpecialValueText("Söndürülüb")
    idle_row.addWidget(self.idle_spin)

    self.ua_combo = QComboBox()
    for key, label in USER_AGENT_PRESETS.items():
      self.ua_combo.addItem(label, key)
    index = self.ua_combo.findData(settings.user_agent_key)
    if index >= 0:
      self.ua_combo.setCurrentIndex(index)

    self.proxy_cb = QCheckBox("Proxy aktiv")
    self.proxy_cb.setChecked(settings.proxy_enabled)

    form = QFormLayout()
    self.proxy_type = QComboBox()
    self.proxy_type.addItem("HTTP", "http")
    self.proxy_type.addItem("SOCKS5", "socks5")
    idx = self.proxy_type.findData(settings.proxy_type)
    if idx >= 0:
      self.proxy_type.setCurrentIndex(idx)

    self.proxy_host = QLineEdit(settings.proxy_host)
    self.proxy_host.setPlaceholderText("127.0.0.1")

    self.proxy_port = QSpinBox()
    self.proxy_port.setRange(1, 65535)
    self.proxy_port.setValue(settings.proxy_port)

    form.addRow("Proxy tipi:", self.proxy_type)
    form.addRow("Proxy host:", self.proxy_host)
    form.addRow("Proxy port:", self.proxy_port)

    layout.addWidget(self.https_cb)
    layout.addLayout(idle_row)
    layout.addWidget(QLabel("User-Agent:"))
    layout.addWidget(self.ua_combo)
    layout.addWidget(self.proxy_cb)
    layout.addLayout(form)

    buttons = QDialogButtonBox(
      QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(self._save)
    buttons.rejected.connect(self.reject)
    layout.addWidget(buttons)

  def _save(self):
    self._settings.https_only = self.https_cb.isChecked()
    self._settings.idle_minutes = self.idle_spin.value()
    self._settings.user_agent_key = self.ua_combo.currentData()
    self._settings.proxy_enabled = self.proxy_cb.isChecked()
    self._settings.proxy_type = self.proxy_type.currentData()
    self._settings.proxy_host = self.proxy_host.text().strip()
    self._settings.proxy_port = self.proxy_port.value()
    parent = self.parent()
    if hasattr(parent, "_sync_browser_identity"):
      parent._sync_browser_identity()
    else:
      apply_browser_identity(self._profile, self._settings)
    apply_proxy(self._settings)
    self.accept()


SHORTCUTS_HTML = """
<h3>Klaviatura qısayolları</h3>
<table cellspacing='6'>
<tr><td><b>Ctrl+T</b></td><td>Yeni tab</td></tr>
<tr><td><b>Ctrl+W</b></td><td>Tabı bağla</td></tr>
<tr><td><b>Ctrl+Shift+T</b></td><td>Son tabı bərpa et</td></tr>
<tr><td><b>Ctrl+L</b></td><td>Ünvan sətri</td></tr>
<tr><td><b>Ctrl+F</b></td><td>Səhifədə axtar</td></tr>
<tr><td><b>Ctrl+H</b></td><td>Tarixçə</td></tr>
<tr><td><b>Ctrl+J</b></td><td>Yükləmələr</td></tr>
<tr><td><b>Ctrl+R</b></td><td>Yenilə</td></tr>
<tr><td><b>Ctrl+Tab</b></td><td>Növbəti tab</td></tr>
<tr><td><b>Ctrl++ / Ctrl+-</b></td><td>Zoom</td></tr>
<tr><td><b>Ctrl+0</b></td><td>Zoom sıfırla</td></tr>
<tr><td><b>F11</b></td><td>Tam ekran</td></tr>
<tr><td><b>Alt+←/→</b></td><td>Geri / İrəli</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Çıxış</td></tr>
</table>
"""
