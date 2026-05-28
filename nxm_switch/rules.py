from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .config import load_config, parse_game, save_config
from .discovery import handler_name
from .widgets import divider, lbl, make_btn


class AddRuleDialog(QDialog):
    """Small dialog to create a game → handler rule."""

    def __init__(
        self,
        handlers: list,
        config: dict | None = None,
        prefill_game: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.handlers = handlers
        self.config = config if config is not None else load_config()
        self.result_game = ""
        self.result_handler = None

        self.setWindowTitle("Add Game Rule")
        self.setModal(True)
        self.setMinimumWidth(380)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(0)

        lay.addWidget(lbl("Add Game Rule", "title"))
        lay.addSpacing(4)
        lay.addWidget(
            lbl("NXM links for this game will always go to the chosen handler.")
        )
        lay.addSpacing(16)
        lay.addWidget(divider())
        lay.addSpacing(14)

        lay.addWidget(lbl("GAME SLUG", "mono"))
        lay.addSpacing(6)

        hint = lbl(
            "Type the game slug, or paste a full nxm:// link here to extract it automatically.",
            "small",
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addSpacing(6)

        self.game_input = QLineEdit()
        self.game_input.setPlaceholderText("e.g. skyrimspecialedition")
        self.game_input.textChanged.connect(self._auto_parse)
        if prefill_game:
            self.game_input.setText(prefill_game)
        lay.addWidget(self.game_input)

        last_game = self.config.get("last_game")
        if last_game:
            lay.addSpacing(6)
            last_row = QHBoxLayout()
            last_row.setSpacing(8)
            last_row.addWidget(lbl(f"Last link clicked:  {last_game}", "small"))
            last_btn = make_btn("Auto-Fill", "ghost")
            last_btn.clicked.connect(lambda: self.game_input.setText(last_game))
            last_row.addWidget(last_btn)
            last_row.addStretch()
            lay.addLayout(last_row)

        lay.addSpacing(14)
        lay.addWidget(lbl("SEND TO", "mono"))
        lay.addSpacing(6)

        self.handler_combo = QComboBox()
        for h in handlers:
            self.handler_combo.addItem(h["name"], userData=h)
        lay.addWidget(self.handler_combo)
        lay.addSpacing(20)

        brow = QHBoxLayout()
        brow.setSpacing(10)
        cancel = make_btn("Cancel", "secondary")
        cancel.clicked.connect(self.reject)
        brow.addWidget(cancel)
        brow.addStretch()
        save = make_btn("Save Rule")
        save.clicked.connect(self._save)
        brow.addWidget(save)
        lay.addLayout(brow)

    def _auto_parse(self, text: str) -> None:
        if text.strip().lower().startswith("nxm://"):
            self.game_input.blockSignals(True)  # noqa: FBT003
            self.game_input.setText(parse_game(text.strip()))
            self.game_input.blockSignals(False)  # noqa: FBT003

    def _save(self) -> None:
        game = self.game_input.text().strip().lower()
        if not game:
            self.game_input.setFocus()
            return
        self.result_game = game
        self.result_handler = self.handler_combo.currentData()
        self.accept()


# ── Rules page ────────────────────────────────────────────────────────────────


class RulesPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.config: dict = {"rules": {}}
        self.handlers: list = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 16, 0, 0)
        lay.setSpacing(0)

        note = lbl("Route specific games to specific mod managers automatically.")
        note.setWordWrap(True)
        lay.addWidget(note)
        lay.addSpacing(12)

        self.list = QListWidget()
        lay.addWidget(self.list)
        lay.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.del_btn = make_btn("Remove Rule", "danger")
        self.del_btn.setEnabled(False)
        self.del_btn.clicked.connect(self._remove)
        btn_row.addWidget(self.del_btn)
        btn_row.addStretch()
        add_btn = make_btn("+ Add Rule", "ghost")
        add_btn.clicked.connect(self._add)
        btn_row.addWidget(add_btn)
        lay.addLayout(btn_row)
        lay.addStretch()

        self.list.currentRowChanged.connect(
            lambda row: self.del_btn.setEnabled(row >= 0)
        )

    def refresh(self, config: dict, handlers: list) -> None:
        self.config = config
        self.handlers = handlers
        self.list.clear()
        for game, did in sorted(config.get("rules", {}).items()):
            name = handler_name(did, handlers)
            item = QListWidgetItem(f"{game}  →  {name}")
            item.setData(Qt.ItemDataRole.UserRole, game)
            self.list.addItem(item)
        self.del_btn.setEnabled(False)

    def _add(self) -> None:
        dlg = AddRuleDialog(self.handlers, config=self.config, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.result_game:
            return
        game = dlg.result_game
        rules = self.config.setdefault("rules", {})
        if game in rules:
            existing = handler_name(rules[game], self.handlers)
            answer = QMessageBox.question(
                self,
                "Rule Already Exists",
                f"'{game}' already routes to {existing}.\nReplace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        rules[game] = dlg.result_handler["id"]
        save_config(self.config)
        self.refresh(self.config, self.handlers)

    def _remove(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        self.config.get("rules", {}).pop(item.data(Qt.ItemDataRole.UserRole), None)
        save_config(self.config)
        self.refresh(self.config, self.handlers)
