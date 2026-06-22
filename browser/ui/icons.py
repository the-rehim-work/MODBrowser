"""Small UI icons for browser controls."""

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def _draw_icon(draw_fn, size: int = 16, color: str = "#9aa0a6") -> QIcon:
  pix = QPixmap(size, size)
  pix.fill(Qt.GlobalColor.transparent)
  painter = QPainter(pix)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  draw_fn(painter, size, QColor(color))
  painter.end()
  return QIcon(pix)


def plus_icon(size: int = 16, color: str = "#9aa0a6") -> QIcon:
  def draw(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    mid = s // 2
    pad = int(s * 0.28)
    p.drawLine(mid, pad, mid, s - pad)
    p.drawLine(pad, mid, s - pad, mid)

  return _draw_icon(draw, size, color)


def close_icon(size: int = 16, color: str = "#9aa0a6") -> QIcon:
  def draw(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    pad = int(s * 0.28)
    p.drawLine(pad, pad, s - pad, s - pad)
    p.drawLine(s - pad, pad, pad, s - pad)

  return _draw_icon(draw, size, color)


def back_icon(size: int = 16, color: str = "#e8eaed") -> QIcon:
  def draw(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x1 = int(s * 0.62)
    x2 = int(s * 0.34)
    y1 = int(s * 0.24)
    y2 = s // 2
    y3 = int(s * 0.76)
    p.drawLine(x1, y1, x2, y2)
    p.drawLine(x2, y2, x1, y3)

  return _draw_icon(draw, size, color)


def forward_icon(size: int = 16, color: str = "#e8eaed") -> QIcon:
  def draw(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    x1 = int(s * 0.38)
    x2 = int(s * 0.66)
    y1 = int(s * 0.24)
    y2 = s // 2
    y3 = int(s * 0.76)
    p.drawLine(x1, y1, x2, y2)
    p.drawLine(x2, y2, x1, y3)

  return _draw_icon(draw, size, color)


def reload_icon(size: int = 16, color: str = "#e8eaed") -> QIcon:
  def draw(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    inset = int(s * 0.22)
    rect = QRectF(inset, inset, s - inset * 2, s - inset * 2)
    p.drawArc(rect, 16 * 16, 270 * 16)
    ax = int(s * 0.68)
    ay = int(s * 0.24)
    p.drawLine(ax, ay, int(s * 0.78), int(s * 0.18))
    p.drawLine(ax, ay, int(s * 0.72), int(s * 0.34))

  return _draw_icon(draw, size, color)


def stop_icon(size: int = 16, color: str = "#e8eaed") -> QIcon:
  def draw(p: QPainter, s: int, c: QColor):
    pad = int(s * 0.30)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(c)
    p.drawRect(pad, pad, s - pad * 2, s - pad * 2)

  return _draw_icon(draw, size, color)
