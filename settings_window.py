from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from activity_log import journal_note
from config import load_config
from constants import MIME_TYPE
from discovery import get_handlers
from install import (
    install_self,
    self_is_default,
    self_is_installed,
    uninstall_self,
)
from logs_page import LogsPage
from rules import RulesPage
from settings_page import SettingsPage
from widgets import divider, lbl, make_btn, repolish


class SettingsWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NXM Switch - Settings")
        self.setMinimumSize(520, 520)
        self.resize(560, 580)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 28, 28, 28)
        outer.setSpacing(0)

        outer.addWidget(lbl("NXM Switch", "title"))
        outer.addWidget(lbl(f"{MIME_TYPE}  ·  settings", "mono"))
        outer.addSpacing(18)
        outer.addWidget(divider())

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)

        status_page = QWidget()
        status_lay = QVBoxLayout(status_page)
        status_lay.setContentsMargins(0, 16, 0, 0)
        status_lay.setSpacing(0)

        status_lay.addWidget(lbl("HANDLER STATUS", "mono"))
        status_lay.addSpacing(6)
        self.status_lbl = QLabel()
        status_lay.addWidget(self.status_lbl)
        status_lay.addSpacing(10)
        ibrow = QHBoxLayout()
        self.install_btn = make_btn("Install as Handler", "ghost")
        self.install_btn.clicked.connect(self._toggle_install)
        ibrow.addWidget(self.install_btn)
        ibrow.addStretch()
        status_lay.addLayout(ibrow)

        status_lay.addSpacing(20)
        status_lay.addWidget(divider())
        status_lay.addSpacing(16)

        status_lay.addWidget(lbl("DETECTED MOD MANAGERS", "mono"))
        status_lay.addSpacing(6)
        self.handlers_list = QListWidget()
        self.handlers_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        status_lay.addWidget(self.handlers_list)

        self.rules_page = RulesPage()
        self.settings_page = SettingsPage()
        self.logs_page = LogsPage()

        self.tabs.addTab(status_page, "Status")
        self.tabs.addTab(self.rules_page, "Rules")
        self.tabs.addTab(self.settings_page, "Settings")
        self.tabs.addTab(self.logs_page, "Logs")

        outer.addSpacing(12)
        brow = QHBoxLayout()
        ref = make_btn("⟳  Refresh", "secondary")
        ref.clicked.connect(self._load)
        brow.addWidget(ref)
        brow.addStretch()
        outer.addLayout(brow)

        self._load()

    def _load(self) -> None:
        self.config = load_config()
        self.handlers = get_handlers(self.config)
        self.installed = self_is_installed()
        self.is_default = self_is_default()

        if self.installed and self.is_default:
            self.status_lbl.setObjectName("ok")
            self.status_lbl.setText("● Default nexus handler")
            self.install_btn.setVisible(False)
        else:
            self.status_lbl.setObjectName("warn")
            self.status_lbl.setText(
                "◐ Not the default nexus handler"
                if self.installed
                else "○ Not installed"
            )
            self.install_btn.setText("Set as Default")
            self.install_btn.setObjectName("ghost")
            self.install_btn.setVisible(True)

        repolish(self.status_lbl)
        repolish(self.install_btn)

        self.handlers_list.clear()
        for h in self.handlers:
            self.handlers_list.addItem(h["name"])
        if not self.handlers:
            self.handlers_list.addItem("No mod managers detected")
        self.rules_page.refresh(self.config, self.handlers)
        self.settings_page.refresh(self.config, self.handlers)
        self.logs_page.refresh(self.config, self.handlers)

    def do_install(self) -> None:
        if install_self():
            QMessageBox.information(
                self, "Default Set", "NXM Switch is now the default NXM handler."
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to set as default handler.")
        self._load()

    def _toggle_install(self) -> None:
        if self.installed and self.is_default:
            if (
                QMessageBox.question(
                    self,
                    "Uninstall",
                    "Remove NXM Switch as the NXM handler?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                == QMessageBox.StandardButton.Yes
            ):
                uninstall_self()
                self._load()
        else:
            self.do_install()
