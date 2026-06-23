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
  QGridLayout,
  QScrollArea,
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

SHORTCUTS = [
  ("Ctrl+T", "Yeni tab"),
  ("Ctrl+W", "Tabı bağla"),
  ("Ctrl+Shift+T", "Son tabı bərpa et"),
  ("Ctrl+1…8 / Ctrl+9", "Taba keç / son tab"),
  ("Ctrl+Tab", "Növbəti tab"),
  ("Ctrl+L / F6", "Ünvan sətri / fokus dəyiş"),
  ("Ctrl+F", "Səhifədə axtar"),
  ("Esc", "Dayandır / axtarışı bağla"),
  ("Ctrl+B / Ctrl+D", "Əlfəcinlər / əlfəcinə əlavə et"),
  ("Ctrl+H / Ctrl+J", "Tarixçə / Yükləmələr"),
  ("F5 / Ctrl+R", "Yenilə"),
  ("Ctrl+F5 / Ctrl+Shift+R", "Keşsiz yenilə"),
  ("F12 / Ctrl+Shift+I", "DevTools"),
  ("Ctrl+P", "PDF kimi çap"),
  ("Alt+Home", "Ana səhifə"),
  ("Ctrl++ / Ctrl+-", "Zoom böyüt / kiçilt"),
  ("Ctrl+0", "Zoom sıfırla"),
  ("F11", "Tam ekran"),
  ("Alt+← / Alt+→", "Geri / İrəli"),
  ("Ctrl+Q", "Çıxış"),
]


class ShortcutsDialog(QDialog):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setObjectName("shortcutsDialog")
    self.setWindowTitle("Qısayollar")
    self.setMinimumSize(460, 540)

    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    header = QLabel("Klaviatura qısayolları")
    header.setObjectName("shortcutsHeader")
    layout.addWidget(header)

    scroll = QScrollArea()
    scroll.setObjectName("shortcutsScroll")
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    body = QWidget()
    grid = QGridLayout(body)
    grid.setContentsMargins(20, 12, 20, 16)
    grid.setHorizontalSpacing(16)
    grid.setVerticalSpacing(10)
    grid.setColumnStretch(1, 1)

    for row, (keys, desc) in enumerate(SHORTCUTS):
      key_label = QLabel(keys)
      key_label.setObjectName("shortcutKey")
      key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
      desc_label = QLabel(desc)
      desc_label.setObjectName("shortcutDesc")
      grid.addWidget(key_label, row, 0, Qt.AlignmentFlag.AlignTop)
      grid.addWidget(desc_label, row, 1)

    scroll.setWidget(body)
    layout.addWidget(scroll, 1)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(self.reject)
    buttons.accepted.connect(self.accept)
    footer = QHBoxLayout()
    footer.setContentsMargins(20, 8, 20, 16)
    footer.addStretch()
    footer.addWidget(buttons)
    layout.addLayout(footer)