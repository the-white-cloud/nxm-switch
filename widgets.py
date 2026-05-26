from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton


def divider() -> QFrame:
    f = QFrame()
    f.setObjectName("div")
    f.setFrameShape(QFrame.Shape.HLine)
    return f


def make_btn(label: QLabel, kind: str = "primary") -> QPushButton:
    b = QPushButton(label)
    b.setObjectName(kind)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def repolish(w) -> None:
    w.style().unpolish(w)
    w.style().polish(w)


def lbl(text: str, obj: str = "body") -> QLabel:
    label = QLabel(text)
    label.setObjectName(obj)
    return label


def truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[: max_len - 3] + "…"
