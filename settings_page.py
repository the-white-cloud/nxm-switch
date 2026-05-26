from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from activity_log import journal_note
from config import save_config
from constants import DEFAULT_TIMEOUT
from install import guard_available, guard_is_active, install_guard, uninstall_guard
from widgets import divider, lbl, make_btn


class SettingsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.config: dict = {}
        self._handlers: list = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 16, 0, 16)
        lay.setSpacing(0)

        lay.addWidget(lbl("COUNTDOWN TIMEOUT", "mono"))
        lay.addSpacing(6)
        self.countdown_cb = QCheckBox("Enable countdown timer")
        self.countdown_cb.toggled.connect(self._on_countdown_toggled)
        self.countdown_cb.toggled.connect(self._save)
        lay.addWidget(self.countdown_cb)
        lay.addSpacing(8)
        note = lbl(
            "Seconds to wait before auto-forwarding to the selected handler.",
            "small",
        )
        note.setWordWrap(True)
        lay.addWidget(note)
        lay.addSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(3, 120)
        self.timeout_spin.setSuffix("  s")
        self.timeout_spin.setFixedWidth(90)
        self.timeout_spin.editingFinished.connect(self._save)
        row.addWidget(self.timeout_spin)
        row.addStretch()
        lay.addLayout(row)

        lay.addSpacing(20)
        lay.addWidget(divider())
        lay.addSpacing(16)

        lay.addWidget(lbl("PREFERRED MOD MANAGER", "mono"))
        lay.addSpacing(6)
        pref_note = lbl(
            "This handler is pre-selected and sorted to the top of the picker.",
            "small",
        )
        pref_note.setWordWrap(True)
        lay.addWidget(pref_note)
        lay.addSpacing(10)
        self.preferred_combo = QComboBox()
        self.preferred_combo.currentIndexChanged.connect(self._save)
        lay.addWidget(self.preferred_combo)

        lay.addSpacing(16)

        self.stop_on_interact_cb = QCheckBox(
            "Stop countdown when I interact with the picker"
        )
        self.stop_on_interact_cb.toggled.connect(self._save)
        lay.addWidget(self.stop_on_interact_cb)

        lay.addSpacing(20)
        lay.addWidget(divider())
        lay.addSpacing(16)

        lay.addWidget(lbl("CUSTOM MOD MANAGERS", "mono"))
        lay.addSpacing(6)
        custom_note = lbl(
            "Add apps that support NXM links but aren't detected automatically.",
            "small",
        )
        custom_note.setWordWrap(True)
        lay.addWidget(custom_note)
        lay.addSpacing(10)
        self.custom_list = QListWidget()
        self.custom_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.custom_list.setMaximumHeight(120)
        lay.addWidget(self.custom_list)
        lay.addSpacing(6)
        custom_btn_row = QHBoxLayout()
        custom_btn_row.setSpacing(8)
        self.custom_del_btn = make_btn("Remove", "danger")
        self.custom_del_btn.setEnabled(False)
        self.custom_del_btn.clicked.connect(self._remove_custom)
        custom_btn_row.addWidget(self.custom_del_btn)
        custom_btn_row.addStretch()
        add_custom_btn = make_btn("+ Add", "ghost")
        add_custom_btn.clicked.connect(self._add_custom)
        custom_btn_row.addWidget(add_custom_btn)
        lay.addLayout(custom_btn_row)
        self.custom_list.currentRowChanged.connect(
            lambda row: self.custom_del_btn.setEnabled(row >= 0)
        )

        lay.addSpacing(20)
        lay.addWidget(divider())
        lay.addSpacing(16)

        lay.addWidget(lbl("STARTUP", "mono"))
        lay.addSpacing(6)
        self.warn_default_cb = QCheckBox(
            "Warn me when NXM Switch isn't the default handler"
        )
        self.warn_default_cb.toggled.connect(self._save)
        lay.addWidget(self.warn_default_cb)

        lay.addSpacing(20)
        lay.addWidget(divider())
        lay.addSpacing(16)

        lay.addWidget(lbl("KEEP AS DEFAULT", "mono"))
        lay.addSpacing(6)
        guard_note = lbl(
            "Runs a systemd user service that keeps this application as default "
            "when another application tries to make itself the default for nexus mods.",
            "small",
        )
        guard_note.setWordWrap(True)
        lay.addWidget(guard_note)
        lay.addSpacing(10)
        self.guard_cb = QCheckBox("Aggressive mode (not recommended)")
        self.guard_cb.setToolTip("(unless another app is being equally aggressive)")
        self.guard_cb.toggled.connect(self._toggle_guard)
        lay.addWidget(self.guard_cb)

        lay.addStretch()

    def refresh(self, config: dict, handlers: list) -> None:
        self.config = config
        self._handlers = handlers
        self.timeout_spin.setValue(config.get("timeout", DEFAULT_TIMEOUT))

        self.preferred_combo.blockSignals(True)
        self.preferred_combo.clear()
        self.preferred_combo.addItem("(none)", userData="")
        for h in handlers:
            self.preferred_combo.addItem(h["name"], userData=h["id"])
        idx = self.preferred_combo.findData(config.get("preferred", ""))
        self.preferred_combo.setCurrentIndex(max(0, idx))
        self.preferred_combo.blockSignals(False)

        self.stop_on_interact_cb.blockSignals(True)
        self.stop_on_interact_cb.setChecked(config.get("stop_on_interact", True))
        self.stop_on_interact_cb.blockSignals(False)

        self.custom_list.clear()
        for c in config.get("custom_handlers", []):
            item = QListWidgetItem(f"{c['name']}  —  {c['exec']}")
            item.setData(Qt.ItemDataRole.UserRole, c)
            self.custom_list.addItem(item)
        self.custom_del_btn.setEnabled(False)

        enabled = config.get("countdown_enabled", False)
        self.countdown_cb.blockSignals(True)
        self.countdown_cb.setChecked(enabled)
        self.countdown_cb.blockSignals(False)
        self._on_countdown_toggled(enabled)

        self.warn_default_cb.blockSignals(True)
        self.warn_default_cb.setChecked(config.get("warn_if_not_default", True))
        self.warn_default_cb.blockSignals(False)

        self.guard_cb.blockSignals(True)
        self.guard_cb.setEnabled(guard_available())
        self.guard_cb.setChecked(guard_is_active())
        self.guard_cb.blockSignals(False)

    def _toggle_guard(self, enabled: bool) -> None:
        if enabled:
            if not install_guard():
                QMessageBox.warning(
                    self,
                    "Background Service",
                    "Could not enable the service. A systemd user session is required.",
                )
        else:
            journal_note("service stopped (Aggressive mode disabled)")
            uninstall_guard()
        self.guard_cb.blockSignals(True)
        self.guard_cb.setEnabled(guard_available())
        self.guard_cb.setChecked(guard_is_active())
        self.guard_cb.blockSignals(False)

    def _on_countdown_toggled(self, enabled: bool) -> None:
        self.timeout_spin.setEnabled(enabled)
        self.stop_on_interact_cb.setEnabled(enabled)

    def _add_custom(self) -> None:
        dlg = _AddCustomDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name, exec_path = dlg.result_name, dlg.result_exec
        customs = self.config.setdefault("custom_handlers", [])
        if any(c["name"] == name for c in customs):
            QMessageBox.warning(
                self,
                "Duplicate",
                f"A custom handler named '{name}' already exists.",
            )
            return
        customs.append({"name": name, "exec": exec_path})
        save_config(self.config)
        self.refresh(self.config, self._handlers)

    def _remove_custom(self) -> None:
        item = self.custom_list.currentItem()
        if not item:
            return
        c = item.data(Qt.ItemDataRole.UserRole)
        customs = self.config.get("custom_handlers", [])
        self.config["custom_handlers"] = [x for x in customs if x["name"] != c["name"]]
        save_config(self.config)
        self.refresh(self.config, self._handlers)

    def _save(self) -> None:
        self.config["timeout"] = self.timeout_spin.value()
        self.config["preferred"] = self.preferred_combo.currentData() or ""
        self.config["stop_on_interact"] = self.stop_on_interact_cb.isChecked()
        self.config["countdown_enabled"] = self.countdown_cb.isChecked()
        self.config["warn_if_not_default"] = self.warn_default_cb.isChecked()
        save_config(self.config)


class _AddCustomDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.result_name = ""
        self.result_exec = ""
        self.setWindowTitle("Add Custom Mod Manager")
        self.setModal(True)
        self.setMinimumWidth(400)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(0)

        lay.addWidget(lbl("Add Custom Mod Manager", "title"))
        lay.addSpacing(4)
        lay.addWidget(lbl("Manually register an app to receive NXM links."))
        lay.addSpacing(16)
        lay.addWidget(divider())
        lay.addSpacing(14)

        lay.addWidget(lbl("NAME", "mono"))
        lay.addSpacing(6)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Mod Organizer 2")
        lay.addWidget(self.name_input)
        lay.addSpacing(14)

        lay.addWidget(lbl("EXECUTABLE PATH", "mono"))
        lay.addSpacing(6)
        path_row = QHBoxLayout()
        path_row.setSpacing(6)
        self.exec_input = QLineEdit()
        self.exec_input.setPlaceholderText("/path/to/app %u")
        path_row.addWidget(self.exec_input)
        browse_btn = make_btn("Browse…", "ghost")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        lay.addLayout(path_row)
        lay.addSpacing(6)
        hint = lbl("Use %u where the nxm:// link should be inserted.", "small")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addSpacing(20)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = make_btn("Cancel", "secondary")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        btn_row.addStretch()
        save = make_btn("Add Handler")
        save.clicked.connect(self._accept)
        btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Executable")
        if path:
            self.exec_input.setText(f"{path} %u")

    def _accept(self) -> None:
        name = self.name_input.text().strip()
        exec_path = self.exec_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        if not exec_path:
            self.exec_input.setFocus()
            return
        self.result_name = name
        self.result_exec = exec_path
        self.accept()
