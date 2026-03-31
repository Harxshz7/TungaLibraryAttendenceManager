from PySide6.QtWidgets import (
    QWidget, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem,
    QVBoxLayout, QGridLayout, QSizePolicy
)
from services.analytics_service import (
    get_daily_averages,
    get_top_users
)


class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QGridLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 20, 24, 20)

        # -------- TITLE --------
        title = QLabel("Library Analytics Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        # -------- DAILY AVERAGES --------
        avg_group = QGroupBox("Daily Averages")
        avg_layout = QVBoxLayout(avg_group)
        avg_layout.setContentsMargins(18, 14, 18, 16)
        avg_layout.setSpacing(8)

        avg_visits, avg_hours = get_daily_averages()

        avg_label = QLabel(
            f"Average Visits per Day: <b>{avg_visits}</b><br>"
            f"Average Hours Spent per Day: <b>{avg_hours}</b>"
        )
        avg_label.setStyleSheet("font-size: 14px;")

        avg_layout.addWidget(avg_label)

        # -------- MOST FREQUENT USERS --------
        user_group = QGroupBox("Most Frequent Users")
        user_layout = QVBoxLayout(user_group)
        user_layout.setContentsMargins(18, 14, 18, 16)
        user_layout.setSpacing(10)

        user_table = QTableWidget(0, 3)
        user_table.setHorizontalHeaderLabels(["ID", "Name", "Visits"])
        user_table.horizontalHeader().setStretchLastSection(True)
        user_table.verticalHeader().setVisible(False)
        user_table.setAlternatingRowColors(True)
        user_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for r, (sid, name, visits) in enumerate(get_top_users()):
            user_table.insertRow(r)
            user_table.setItem(r, 0, QTableWidgetItem(sid))
            user_table.setItem(r, 1, QTableWidgetItem(name))
            user_table.setItem(r, 2, QTableWidgetItem(str(visits)))

        user_layout.addWidget(user_table)

        # -------- LAYOUT --------
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(avg_group, 1, 0)
        layout.addWidget(user_group, 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
