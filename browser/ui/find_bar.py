"""In-page find bar (Ctrl+F)."""

from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FindBar(QWidget):
  def __init__(self, browser_window, parent=None):
    super().__init__(parent)
    self._window = browser_window
    self.setObjectName("findBar")

    layout = QHBoxLayout(self)
    layout.setContentsMargins(12, 6, 12, 6)
    layout.setSpacing(6)

    self.input = QLineEdit()
    self.input.setObjectName("findInput")
    self.input.setPlaceholderText("Səhifədə axtar...")
    self.input.returnPressed.connect(self._find_next)

    self.status = QLabel("")
    self.status.setObjectName("findStatus")

    prev_btn = QPushButton("↑")
    prev_btn.setObjectName("findBtn")
    prev_btn.setFixedSize(28, 28)
    prev_btn.clicked.connect(self._find_prev)

    next_btn = QPushButton("↓")
    next_btn.setObjectName("findBtn")
    next_btn.setFixedSize(28, 28)
    next_btn.clicked.connect(self._find_next)

    close_btn = QPushButton("×")
    close_btn.setObjectName("findBtn")
    close_btn.setFixedSize(28, 28)
    close_btn.clicked.connect(self.hide_bar)

    layout.addWidget(self.input, 1)
    layout.addWidget(self.status)
    layout.addWidget(prev_btn)
    layout.addWidget(next_btn)
    layout.addWidget(close_btn)

    self.input.textChanged.connect(self._find_next)
    self.hide()

  def show_bar(self):
    self.show()
    self.input.setFocus()
    self.input.selectAll()
    self._find_next()

  def hide_bar(self):
    self.hide()
    tab = self._window.current_tab()
    if tab:
      tab.view.page().findText("")

  def _find_next(self):
    self._find(backward=False)

  def _find_prev(self):
    self._find(backward=True)

  def _find(self, backward: bool):
    text = self.input.text()
    tab = self._window.current_tab()
    if not tab or not text:
      self.status.setText("")
      if tab:
        tab.view.page().findText("")
      return

    flags = QWebEnginePage.FindFlag(0)
    if backward:
      flags |= QWebEnginePage.FindFlag.FindBackward

    def callback(result):
      if result.numberOfMatches() == 0:
        self.status.setText("Tapılmadı")
      else:
        self.status.setText(f"{result.activeMatch()}/{result.numberOfMatches()}")

    tab.view.page().findText(text, flags, callback)
