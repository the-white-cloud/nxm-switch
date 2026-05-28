from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .activity_log import log_forward
from .config import load_config, save_config
from .constants import DEFAULT_TIMEOUT, ForwardMethod
from .discovery import get_handlers
from .launch import launch_handler
from .widgets import divider, lbl, make_btn, truncate


class InterceptDialog(QDialog):
    def __init__(
        self,
        url: str,
        game: str = "",
        config: dict | None = None,
        handlers: list | None = None,
    ) -> None:
        super().__init__()
        self.url = url
        self.game = game
        self.config = config if config is not None else load_config()
        self.handlers = handlers if handlers is not None else get_handlers(self.config)

        self.setWindowTitle("NXM Switch")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.setMinimumWidth(460)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(0)

        row = QHBoxLayout()
        row.addWidget(lbl("Forward NXM Link", "title"))
        row.addStretch()
        x = make_btn("✕", "secondary")
        x.setFixedSize(28, 28)
        x.clicked.connect(self.reject)
        row.addWidget(x)
        lay.addLayout(row)
        lay.addSpacing(6)

        if game:
            tag_row = QHBoxLayout()
            tag_row.setSpacing(8)
            tag = lbl(game, "game_tag")
            tag.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            tag_row.addWidget(tag)
            tag_row.addWidget(lbl(truncate(url, 52), "small"))
            tag_row.addStretch()
            lay.addLayout(tag_row)
        else:
            lay.addWidget(lbl(truncate(url, 68), "small"))

        lay.addSpacing(16)
        lay.addWidget(divider())
        lay.addSpacing(14)

        preferred_id = self.config.get("preferred", "")
        if preferred_id:
            self.handlers = sorted(
                self.handlers,
                key=lambda h: (0 if h["id"] == preferred_id else 1, h["name"].lower()),
            )

        if not self.handlers:
            msg = lbl(
                "No NXM-capable apps found.\n"
                "Install a mod manager (Vortex, MO2, etc.) first.",
                "body",
            )
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(msg)
            lay.addSpacing(16)
            close_btn = make_btn("Close", "secondary")
            close_btn.clicked.connect(self.reject)
            lay.addWidget(close_btn)
            return

        lay.addWidget(lbl("AVAILABLE HANDLERS", "mono"))
        lay.addSpacing(6)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Application", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(150)

        self.table.setRowCount(len(self.handlers))
        for i, h in enumerate(self.handlers):
            self.table.setItem(i, 0, QTableWidgetItem(h["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(h["exec"]))

        self.table.selectRow(0)
        if self.config.get("stop_on_interact", True):
            self.table.itemSelectionChanged.connect(self._on_interact)
            self.table.clicked.connect(self._on_interact)
        lay.addWidget(self.table)
        lay.addSpacing(10)

        if game:
            self.save_rule = QCheckBox(f"Always use this for  {game}  (game rule)")
            lay.addWidget(self.save_rule)
        else:
            self.save_rule = None
        lay.addSpacing(12)

        self.countdown_lbl = lbl("", "small")
        lay.addWidget(self.countdown_lbl)
        lay.addSpacing(6)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        if self.config.get("countdown_enabled", False):
            self._countdown = self.config.get("timeout", DEFAULT_TIMEOUT)
            self._update_cd()
            self._timer.start()
        else:
            self.countdown_lbl.setVisible(False)

        brow = QHBoxLayout()
        brow.setSpacing(10)
        cancel = make_btn("Cancel", "secondary")
        cancel.clicked.connect(self.reject)
        brow.addWidget(cancel)
        brow.addStretch()
        self.go_btn = make_btn("Forward  →")
        self.go_btn.clicked.connect(lambda: self._launch(ForwardMethod.MANUAL))
        brow.addWidget(self.go_btn)
        lay.addLayout(brow)

    def _on_interact(self, *_) -> None:
        if self._timer.isActive():
            self._timer.stop()
            self.countdown_lbl.setText("Countdown stopped")

    def _update_cd(self) -> None:
        self.countdown_lbl.setText(
            f"Auto-forwarding in {self._countdown}s - pick a different app or cancel"
        )

    def _tick(self) -> None:
        self._countdown -= 1
        if self._countdown <= 0:
            self._timer.stop()
            self._launch(ForwardMethod.TIMEOUT)
        else:
            self._update_cd()

    def _launch(self, method: ForwardMethod = ForwardMethod.MANUAL) -> None:
        self._timer.stop()
        row = self.table.currentRow()
        if row < 0:
            return
        h = self.handlers[row]
        if self.save_rule and self.save_rule.isChecked():
            self.config.setdefault("rules", {})[self.game] = h["id"]
            save_config(self.config)
        launch_handler(h, self.url)
        log_forward(self.url, h["name"], method)
        self.accept()
