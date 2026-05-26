from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


class Theme:
    @staticmethod
    def get() -> dict[str, str]:
        pal = QApplication.palette()
        bg = pal.color(QPalette.ColorRole.Window).name()
        card = pal.color(QPalette.ColorRole.Base).name()
        text = pal.color(QPalette.ColorRole.WindowText).name()
        accent = pal.color(QPalette.ColorRole.Highlight).name()
        return {
            "bg": bg,
            "card": card,
            "text": text,
            "accent": accent,
            "muted": "#5a5e7a",
            "acc_dim": f"{accent}30",
            "border": "#22253a",
            "success": "#4caf7d",
            "warn": "#d4622b",
        }


def get_stylesheet() -> str:
    t = Theme.get()
    return f"""
        QWidget#root, QDialog {{ background: {t["bg"]}; }}
        QLabel {{ color: {t["text"]}; }}
        QListWidget, QTableWidget {{
            background: {t["card"]};
            border: 1px solid {t["border"]};
            color: {t["text"]};
        }}
        QPushButton#primary {{
            background: {t["accent"]};
            color: #ffffff;
            border-radius: 6px;
            padding: 8px;
        }}
    """
