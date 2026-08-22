from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
)
from PySide6.QtCore import Qt

from models.session_repo import get_estimated_sessions
from utils.time_utils import format_duration


class ReviewSessionsWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Review Flagged Sessions")
        self.resize(860, 480)

        layout = QVBoxLayout(self)

        # ---------- TITLE ----------
        title = QLabel("Sessions flagged as estimated (student likely forgot to scan out)")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # ---------- TABLE ----------
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Class", "Date", "Start", "Est. End", "Duration"]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # ---------- BUTTON BAR ----------
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_bar.addWidget(btn_close)

        layout.addLayout(btn_bar)

        # Load data
        self.load_rows()

    def load_rows(self):
        rows = get_estimated_sessions()
        self.table.setRowCount(len(rows))

        for r, (sid, name, cls, date_, start, end, dur) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(sid))
            self.table.setItem(r, 1, QTableWidgetItem(name))
            self.table.setItem(r, 2, QTableWidgetItem(cls))
            self.table.setItem(r, 3, QTableWidgetItem(date_ or "-"))
            self.table.setItem(r, 4, QTableWidgetItem(start or "-"))
            self.table.setItem(r, 5, QTableWidgetItem(end or "-"))
            self.table.setItem(
                r, 6,
                QTableWidgetItem(format_duration(dur) if dur else "-")
            )
