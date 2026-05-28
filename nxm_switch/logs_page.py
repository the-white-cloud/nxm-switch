from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .activity_log import clear_activity_log, read_activity_log, read_service_log
from .constants import ForwardMethod
from .widgets import divider, lbl, make_btn, truncate

METHOD_LABELS = {
    ForwardMethod.RULE: "Rule",
    ForwardMethod.MANUAL: "Manual",
    ForwardMethod.TIMEOUT: "Timed out",
}


class LogsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 16, 0, 0)
        lay.setSpacing(0)

        head_row = QHBoxLayout()
        head_row.addWidget(lbl("FORWARD ACTIVITY", "mono"))
        head_row.addStretch()
        clear_btn = make_btn("Clear", "danger")
        clear_btn.clicked.connect(self._clear)
        head_row.addWidget(clear_btn)
        lay.addLayout(head_row)
        lay.addSpacing(6)

        note = lbl("Links received and where they were forwarded.", "small")
        note.setWordWrap(True)
        lay.addWidget(note)
        lay.addSpacing(8)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                "Time",
                "Link",
                "Sent To",
                "Via",
            ]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        lay.addWidget(self.table)

        lay.addSpacing(16)
        lay.addWidget(divider())
        lay.addSpacing(16)

        lay.addWidget(lbl("SERVICE LOG", "mono"))
        lay.addSpacing(6)
        svc_note = lbl(
            "Journal output from the 'Aggressive mode' background service.",
            "small",
        )
        svc_note.setWordWrap(True)
        lay.addWidget(svc_note)
        lay.addSpacing(8)

        self.service_log = QPlainTextEdit()
        self.service_log.setReadOnly(True)
        self.service_log.setMaximumHeight(160)
        lay.addWidget(self.service_log)

    def refresh(
        self, _config: dict | None = None, _handlers: list | None = None
    ) -> None:
        entries = read_activity_log()
        self.table.setRowCount(len(entries))
        for i, e in enumerate(entries):
            url = e.get("url", "")
            link_item = QTableWidgetItem(truncate(url, 48))
            link_item.setToolTip(url)
            method = e.get("method", "")
            self.table.setItem(i, 0, QTableWidgetItem(e.get("time", "")))
            self.table.setItem(i, 1, link_item)
            self.table.setItem(i, 2, QTableWidgetItem(e.get("handler", "")))
            self.table.setItem(
                i, 3, QTableWidgetItem(METHOD_LABELS.get(method, method))
            )

        self.service_log.setPlainText(read_service_log())

    def _clear(self) -> None:
        clear_activity_log()
        self.refresh()
