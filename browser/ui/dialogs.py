"""Settings and proxy dialogs."""

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
  def __init__(self, settings: BrowserSettings, profile, blocker, parent=None):
    super().__init__(parent)
    self._settings = settings
    self._profile = profile
    self._blocker = blocker
    self.setWindowTitle("Parametrlər")
    self.setMinimumWidth(420)

    layout = QVBoxLayout(self)

    self.https_cb = QCheckBox("HTTPS yalnız rejimi (daxili şəbəkə istisna)")
    self.https_cb.setChecked(settings.https_only)

    self.adblock_cb = QCheckBox("Reklam və izləyiciləri blokla")
    self.adblock_cb.setChecked(settings.adblock_enabled)

    self.block_count_label = QLabel(f"Bu sessiyada bloklandı: {blocker.blocked_count}")
    self.block_count_label.setObjectName("blockCountLabel")

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
    layout.addWidget(self.adblock_cb)
    layout.addWidget(self.block_count_label)
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
    self._settings.adblock_enabled = self.adblock_cb.isChecked()
    self._blocker.set_enabled(self._settings.adblock_enabled)
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
<tr><td><b>Ctrl+1…8 / Ctrl+9</b></td><td>Taba keç / son tab</td></tr>
<tr><td><b>Ctrl+Tab</b></td><td>Növbəti tab</td></tr>
<tr><td><b>Ctrl+L / F6</b></td><td>Ünvan sətri / fokus dəyiş</td></tr>
<tr><td><b>Ctrl+F</b></td><td>Səhifədə axtar</td></tr>
<tr><td><b>Esc</b></td><td>Dayandır / axtarışı bağla</td></tr>
<tr><td><b>Ctrl+B / Ctrl+D</b></td><td>Əlfəcinlər / əlavə et</td></tr>
<tr><td><b>Ctrl+H / Ctrl+J</b></td><td>Tarixçə / Yükləmələr</td></tr>
<tr><td><b>F5 / Ctrl+R</b></td><td>Yenilə</td></tr>
<tr><td><b>Ctrl+F5 / Ctrl+Shift+R</b></td><td>Keşsiz yenilə</td></tr>
<tr><td><b>F12 / Ctrl+Shift+I</b></td><td>DevTools</td></tr>
<tr><td><b>Ctrl+P</b></td><td>PDF kimi çap</td></tr>
<tr><td><b>Alt+Home</b></td><td>Ana səhifə</td></tr>
<tr><td><b>Ctrl++ / Ctrl+-</b></td><td>Zoom</td></tr>
<tr><td><b>Ctrl+0</b></td><td>Zoom sıfırla</td></tr>
<tr><td><b>F11</b></td><td>Tam ekran</td></tr>
<tr><td><b>Alt+←/→</b></td><td>Geri / İrəli</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Çıxış</td></tr>
</table>
"""
