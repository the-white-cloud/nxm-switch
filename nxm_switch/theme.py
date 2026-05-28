from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class Theme:
    @staticmethod
    def get() -> dict[str, str]:
        pal = QApplication.palette()

        bg = pal.color(QPalette.ColorRole.Window)
        card = pal.color(QPalette.ColorRole.Base)
        text = pal.color(QPalette.ColorRole.WindowText)
        accent = pal.color(QPalette.ColorRole.Highlight)

        muted = pal.color(QPalette.ColorRole.PlaceholderText)
        border = pal.color(QPalette.ColorRole.Mid)
        acc_dim = QColor(accent)
        acc_dim.setAlpha(76)

        is_dark_mode = QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        success = QColor("#4caf7d")
        warn = QColor("#d4622b")
        if not is_dark_mode:
            for color in (success, warn):
                hue = color.hslHueF()
                sat = color.hslSaturationF()
                lue = color.lightnessF()
                new_s = min(1.0, sat + 0.05)
                new_l = max(0.10, min(0.95, 1.0 - lue))
                color.setHslF(hue, new_s, new_l, color.alphaF())

        return {
            "bg": bg.name(),
            "card": card.name(),
            "text": text.name(),
            "accent": accent.name(),
            "muted": muted.name(),
            "acc_dim": acc_dim.name(QColor.NameFormat.HexArgb),
            "border": border.name(),
            "success": success.name(),
            "warn": warn.name(),
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
