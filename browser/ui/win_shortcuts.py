"""Application-level Win32 accelerator filter."""

import ctypes

from PyQt6.QtCore import QAbstractNativeEventFilter, QTimer

_WM_KEYDOWN = 0x0100
_WM_SYSKEYDOWN = 0x0104
_VK_CONTROL = 0x11
_VK_SHIFT = 0x10
_VK_MENU = 0x12


class _MSG(ctypes.Structure):
  _fields_ = [
    ("hwnd", ctypes.c_void_p),
    ("message", ctypes.c_uint),
    ("wParam", ctypes.c_void_p),
    ("lParam", ctypes.c_void_p),
    ("time", ctypes.c_uint),
    ("pt_x", ctypes.c_long),
    ("pt_y", ctypes.c_long),
  ]


class WindowsShortcutFilter(QAbstractNativeEventFilter):
  def __init__(self, window, table: dict):
    super().__init__()
    self._window = window
    self._table = table
    self._user32 = ctypes.windll.user32

  def _down(self, vk: int) -> int:
    return 1 if self._user32.GetKeyState(vk) & 0x8000 else 0

  def nativeEventFilter(self, event_type, message):
    if event_type != b"windows_generic_MSG":
      return False, 0
    msg = _MSG.from_address(int(message))
    if msg.message not in (_WM_KEYDOWN, _WM_SYSKEYDOWN):
      return False, 0
    if not self._window.isActiveWindow():
      return False, 0
    vk = int(msg.wParam or 0) & 0xFFFF
    combo = (self._down(_VK_CONTROL), self._down(_VK_SHIFT), self._down(_VK_MENU), vk)
    handler = self._table.get(combo)
    if handler is None:
      return False, 0
    QTimer.singleShot(0, handler)
    return True, 0