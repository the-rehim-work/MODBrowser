"""Download manager, progress panel, and downloads page."""

import os
import subprocess
import sys
from dataclasses import dataclass

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtWidgets import (
  QFileDialog,
  QHBoxLayout,
  QLabel,
  QProgressBar,
  QPushButton,
  QScrollArea,
  QVBoxLayout,
  QWidget,
)


def _format_bytes(size: int) -> str:
  if size < 1024:
    return f"{size} B"
  if size < 1024 ** 2:
    return f"{size / 1024:.1f} KB"
  if size < 1024 ** 3:
    return f"{size / 1024 ** 2:.1f} MB"
  return f"{size / 1024 ** 3:.1f} GB"


@dataclass
class DownloadRecord:
  record_id: int
  filename: str
  filepath: str
  source_url: str
  download: QWebEngineDownloadRequest
  state: str = "in_progress"
  received_bytes: int = 0
  total_bytes: int = 0


class DownloadManager(QObject):
  record_added = pyqtSignal(object)
  record_updated = pyqtSignal(object)

  def __init__(self, parent=None):
    super().__init__(parent)
    self._records: list[DownloadRecord] = []
    self._next_id = 1

  def records(self) -> list[DownloadRecord]:
    return list(self._records)

  def add(self, download: QWebEngineDownloadRequest, filepath: str) -> DownloadRecord:
    record = DownloadRecord(
      record_id=self._next_id,
      filename=os.path.basename(filepath),
      filepath=filepath,
      source_url=download.url().toString(),
      download=download,
    )
    self._next_id += 1
    self._records.insert(0, record)

    download.receivedBytesChanged.connect(lambda: self._sync(record))
    download.totalBytesChanged.connect(lambda: self._sync(record))
    download.stateChanged.connect(lambda _s: self._on_state(record))
    download.isFinishedChanged.connect(lambda: self._sync(record))

    self._sync(record)
    self.record_added.emit(record)
    return record

  def _sync(self, record: DownloadRecord):
    record.received_bytes = record.download.receivedBytes()
    record.total_bytes = record.download.totalBytes()
    if record.download.isFinished():
      state = record.download.state()
      if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
        record.state = "completed"
      elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
        record.state = "cancelled"
      elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
        record.state = "interrupted"
    self.record_updated.emit(record)

  def _on_state(self, record: DownloadRecord):
    state = record.download.state()
    if state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
      record.state = "cancelled"
    elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
      record.state = "interrupted"
    elif state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
      record.state = "completed"
    self.record_updated.emit(record)

  def percent(self, record: DownloadRecord) -> int:
    if record.total_bytes > 0:
      return min(int(record.received_bytes * 100 / record.total_bytes), 100)
    return 0


def open_file(path: str):
  if os.path.exists(path):
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))


def show_in_folder(path: str):
  if os.path.exists(path):
    if sys.platform == "win32":
      subprocess.run(["explorer", "/select,", os.path.normpath(path)], check=False)
    elif sys.platform == "darwin":
      subprocess.run(["open", "-R", path], check=False)
    else:
      QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
    return
  folder = os.path.dirname(path)
  if os.path.isdir(folder):
    QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


def file_type_icon(filename: str) -> str:
  ext = os.path.splitext(filename)[1].lower()
  return {
    ".pdf": "📄",
    ".zip": "📦",
    ".rar": "📦",
    ".7z": "📦",
    ".mp4": "🎬",
    ".mp3": "🎵",
    ".png": "🖼",
    ".jpg": "🖼",
    ".jpeg": "🖼",
    ".gif": "🖼",
    ".exe": "⚙",
    ".msi": "⚙",
    ".doc": "📝",
    ".docx": "📝",
    ".xls": "📊",
    ".xlsx": "📊",
    ".txt": "📃",
  }.get(ext, "📁")


class DownloadRow(QWidget):
  def __init__(self, record: DownloadRecord, panel: "DownloadPanel"):
    super().__init__()
    self._record = record
    self._panel = panel
    self.setObjectName("downloadRow")

    layout = QHBoxLayout(self)
    layout.setContentsMargins(12, 6, 12, 6)
    layout.setSpacing(10)

    self.name_label = QLabel(f"{file_type_icon(record.filename)}  {record.filename}")
    self.name_label.setObjectName("downloadName")

    self.progress = QProgressBar()
    self.progress.setObjectName("downloadProgress")
    self.progress.setRange(0, 100)
    self.progress.setValue(0)
    self.progress.setTextVisible(True)
    self.progress.setFormat("%p%")

    self.status_label = QLabel("0%")
    self.status_label.setObjectName("downloadStatus")
    self.status_label.setMinimumWidth(120)
    self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    cancel_btn = QPushButton("×")
    cancel_btn.setObjectName("downloadCancelBtn")
    cancel_btn.setFixedSize(22, 22)
    cancel_btn.setFlat(True)
    cancel_btn.setToolTip("Ləğv et")
    cancel_btn.clicked.connect(record.download.cancel)

    layout.addWidget(self.name_label, 2)
    layout.addWidget(self.progress, 3)
    layout.addWidget(self.status_label, 1)
    layout.addWidget(cancel_btn)

    record.download.receivedBytesChanged.connect(self._refresh)
    record.download.totalBytesChanged.connect(self._refresh)
    record.download.isFinishedChanged.connect(self._on_finished)
    record.download.stateChanged.connect(self._on_state)
    self._refresh()

  def _refresh(self):
    received = self._record.download.receivedBytes()
    total = self._record.download.totalBytes()
    if total > 0:
      percent = int(received * 100 / total)
      self.progress.setRange(0, 100)
      self.progress.setValue(min(percent, 100))
      self.status_label.setText(
        f"{percent}% · {_format_bytes(received)} / {_format_bytes(total)}"
      )
    else:
      self.progress.setRange(0, 0)
      self.status_label.setText(f"Yüklənir... {_format_bytes(received)}")

  def _on_state(self, state):
    if state in (
      QWebEngineDownloadRequest.DownloadState.DownloadCancelled,
      QWebEngineDownloadRequest.DownloadState.DownloadInterrupted,
    ):
      self.status_label.setText("Ləğv edildi")
      QTimer.singleShot(2000, lambda: self._panel.remove_row(self))

  def _on_finished(self):
    if not self._record.download.isFinished():
      return
    self.progress.setRange(0, 100)
    self.progress.setValue(100)
    self.status_label.setText(f"100% · {_format_bytes(self._record.download.receivedBytes())}")
    QTimer.singleShot(2500, lambda: self._panel.remove_row(self))


class DownloadPanel(QWidget):
  def __init__(self, manager: DownloadManager, parent=None):
    super().__init__(parent)
    self._manager = manager
    self.setObjectName("downloadPanel")
    self._layout = QVBoxLayout(self)
    self._layout.setContentsMargins(0, 0, 0, 0)
    self._layout.setSpacing(0)
    self._rows: dict[int, DownloadRow] = {}
    self.hide()
    manager.record_added.connect(self._on_record_added)
    manager.record_updated.connect(self._on_record_updated)

  def _on_record_added(self, record: DownloadRecord):
    if record.state != "in_progress":
      return
    row = DownloadRow(record, self)
    self._rows[record.record_id] = row
    self._layout.addWidget(row)
    self.show()

  def _on_record_updated(self, record: DownloadRecord):
    if record.state != "in_progress" and record.record_id in self._rows:
      QTimer.singleShot(2500, lambda rid=record.record_id: self._remove_by_id(rid))

  def _remove_by_id(self, record_id: int):
    row = self._rows.pop(record_id, None)
    if row:
      self.remove_row(row)

  def remove_row(self, row: DownloadRow):
    for rid, item in list(self._rows.items()):
      if item is row:
        self._rows.pop(rid, None)
        break
    self._layout.removeWidget(row)
    row.deleteLater()
    if self._layout.count() == 0:
      self.hide()


class DownloadsListRow(QWidget):
  def __init__(self, record: DownloadRecord, manager: DownloadManager):
    super().__init__()
    self._record = record
    self._manager = manager
    self.setObjectName("downloadsListRow")

    layout = QHBoxLayout(self)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(12)

    info = QVBoxLayout()
    info.setSpacing(4)

    self.title = QLabel(f"{file_type_icon(record.filename)}  {record.filename}")
    self.title.setObjectName("downloadsListTitle")

    self.subtitle = QLabel(record.source_url)
    self.subtitle.setObjectName("downloadsListSubtitle")

    self.status = QLabel("")
    self.status.setObjectName("downloadsListStatus")

    info.addWidget(self.title)
    info.addWidget(self.subtitle)
    info.addWidget(self.status)

    self.progress = QProgressBar()
    self.progress.setObjectName("downloadProgress")
    self.progress.setRange(0, 100)
    self.progress.setTextVisible(True)
    self.progress.setFormat("%p%")
    self.progress.hide()

    actions = QHBoxLayout()
    actions.setSpacing(6)

    self.open_btn = QPushButton("Aç")
    self.open_btn.setObjectName("downloadsActionBtn")
    self.open_btn.clicked.connect(lambda: open_file(record.filepath))

    self.folder_btn = QPushButton("Qovluq")
    self.folder_btn.setObjectName("downloadsActionBtn")
    self.folder_btn.clicked.connect(lambda: show_in_folder(record.filepath))

    self.cancel_btn = QPushButton("Ləğv et")
    self.cancel_btn.setObjectName("downloadsActionBtn")
    self.cancel_btn.clicked.connect(record.download.cancel)

    actions.addWidget(self.open_btn)
    actions.addWidget(self.folder_btn)
    actions.addWidget(self.cancel_btn)

    right = QVBoxLayout()
    right.addLayout(actions)

    layout.addLayout(info, 1)
    layout.addWidget(self.progress, 2)
    layout.addLayout(right)

    manager.record_updated.connect(self._refresh)
    self._refresh()

  def _refresh(self, record: DownloadRecord | None = None):
    if record is not None and record.record_id != self._record.record_id:
      return
    rec = self._record
    if rec.state == "in_progress":
      self.progress.show()
      percent = self._manager.percent(rec)
      self.progress.setValue(percent)
      if rec.total_bytes > 0:
        self.status.setText(
          f"Yüklənir... {percent}% · {_format_bytes(rec.received_bytes)} / "
          f"{_format_bytes(rec.total_bytes)}"
        )
      else:
        self.status.setText(f"Yüklənir... {_format_bytes(rec.received_bytes)}")
      self.open_btn.setEnabled(False)
      self.folder_btn.setEnabled(False)
      self.cancel_btn.setEnabled(True)
      self.cancel_btn.show()
    elif rec.state == "completed":
      self.progress.hide()
      self.status.setText(f"Tamamlandı · {_format_bytes(rec.received_bytes)}")
      self.open_btn.setEnabled(os.path.exists(rec.filepath))
      self.folder_btn.setEnabled(os.path.exists(rec.filepath))
      self.cancel_btn.hide()
    elif rec.state == "cancelled":
      self.progress.hide()
      self.status.setText("Ləğv edildi")
      self.open_btn.setEnabled(False)
      self.folder_btn.setEnabled(False)
      self.cancel_btn.hide()
    else:
      self.progress.hide()
      self.status.setText("Xəta ilə dayandı")
      self.open_btn.setEnabled(False)
      self.folder_btn.setEnabled(False)
      self.cancel_btn.hide()


class DownloadsPage(QWidget):
  def __init__(self, manager: DownloadManager, parent=None):
    super().__init__(parent)
    self._manager = manager
    self.setObjectName("downloadsPage")

    root = QVBoxLayout(self)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    header = QWidget()
    header.setObjectName("downloadsPageHeader")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(24, 20, 24, 12)

    title = QLabel("Yükləmələr")
    title.setObjectName("downloadsPageTitle")
    header_layout.addWidget(title)
    header_layout.addStretch()

    self.empty_label = QLabel("Bu sessiyada yükləmə yoxdur")
    self.empty_label.setObjectName("downloadsEmptyLabel")
    self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    self.scroll = QScrollArea()
    self.scroll.setObjectName("downloadsScroll")
    self.scroll.setWidgetResizable(True)
    self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    self.list_widget = QWidget()
    self.list_widget.setObjectName("downloadsList")
    self._list_layout = QVBoxLayout(self.list_widget)
    self._list_layout.setContentsMargins(0, 0, 0, 0)
    self._list_layout.setSpacing(0)
    self._list_layout.addStretch()

    self._empty_container = QWidget()
    empty_layout = QVBoxLayout(self._empty_container)
    empty_layout.addStretch()
    empty_layout.addWidget(self.empty_label)
    empty_layout.addStretch()

    self.scroll.setWidget(self._empty_container)

    root.addWidget(header)
    root.addWidget(self.scroll, stretch=1)

    self._rows: dict[int, DownloadsListRow] = {}
    manager.record_added.connect(self._add_row)

    for record in manager.records():
      self._add_row(record)

  def _add_row(self, record: DownloadRecord):
    if record.record_id in self._rows:
      return
    row = DownloadsListRow(record, self._manager)
    self._rows[record.record_id] = row
    self._list_layout.insertWidget(0, row)
    if self.scroll.widget() is not self.list_widget:
      self.scroll.setWidget(self.list_widget)


def handle_download(
  parent: QWidget,
  download: QWebEngineDownloadRequest,
  manager: DownloadManager,
) -> None:
  suggested = download.suggestedFileName() or "download"
  downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
  default_path = os.path.join(downloads_dir, suggested)

  path, _ = QFileDialog.getSaveFileName(
    parent,
    "Faylı yadda saxla",
    default_path,
  )
  if not path:
    download.cancel()
    return

  download.setDownloadDirectory(os.path.dirname(path) or ".")
  download.setDownloadFileName(os.path.basename(path))
  download.accept()
  manager.add(download, path)
