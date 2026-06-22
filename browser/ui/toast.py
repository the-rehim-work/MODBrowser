"""Toast notification widget."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Toast(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setObjectName("toast")
    self.setWindowFlags(Qt.WindowType.SubWindow)
    self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    layout = QVBoxLayout(self)
    layout.setContentsMargins(16, 10, 16, 10)

    self.label = QLabel()
    self.label.setObjectName("toastLabel")
    self.label.setWordWrap(True)
    layout.addWidget(self.label)

    self._timer = QTimer(self)
    self._timer.setSingleShot(True)
    self._timer.timeout.connect(self.hide)

    self.hide()

  def show_message(self, text: str, duration_ms: int = 3500):
    self.label.setText(text)
    self.adjustSize()
    if self.parent():
      parent = self.parent()
      x = parent.width() - self.width() - 24
      y = parent.height() - self.height() - 80
      self.move(max(12, x), max(12, y))
    self.show()
    self.raise_()
    self._timer.start(duration_ms)
