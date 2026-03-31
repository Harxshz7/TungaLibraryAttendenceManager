from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QFrame,
    QGridLayout
)
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer
from PySide6.QtGui import QPixmap, QFont, QColor, QPalette
import os
from utils.resource_utils import resource_path


class StudentPopup(QWidget):
    def __init__(
        self,
        student_name: str,
        message: str,
        student_id: str = "",
        class_grade: str = None,
        section: str = None,
        image_path: str = None,
        is_login: bool = True,
        total_visits: int = None,
        session_seconds: int = None,
        check_in_time: str = None,
        check_out_time: str = None,
        duration_ms: int = 3200
    ):
        super().__init__()

        self.duration_ms = duration_ms

        # ---------------- Window Setup ----------------
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowOpacity(0.0)

        # ---------------- Theme ----------------
        if is_login:
            accent = "#0fa968"
            accent_soft = "#d7f4e6"
            status_text = "Check-In"
        else:
            accent = "#2563eb"
            accent_soft = "#dbe6ff"
            status_text = "Check-Out"

        title_color = "#0f172a"
        muted = "#4b5563"

        # ---------------- Container ----------------
        container = QWidget(self)
        container.setFixedSize(640, 320)
        container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 18px;
                border: 1px solid #e5e7eb;
            }
        """)

        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(32, 26, 32, 26)
        main_layout.setSpacing(22)

        accent_bar = QFrame()
        accent_bar.setFixedWidth(8)
        accent_bar.setStyleSheet(f"background-color: {accent}; border-radius: 10px;")
        main_layout.addWidget(accent_bar)

        content = QVBoxLayout()
        content.setSpacing(18)
        content.setContentsMargins(0, 0, 0, 0)

        main_layout.addLayout(content)

        # ---------------- Header ----------------
        header = QHBoxLayout()
        header.setSpacing(8)

        status_pill = QLabel(status_text)
        status_pill.setAlignment(Qt.AlignCenter)
        status_pill.setFixedHeight(30)
        status_pill.setMinimumWidth(110)
        status_pill.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        status_pill.setStyleSheet(f"""
            background-color: {accent_soft};
            color: {accent};
            border: 1px solid {accent};
            border-radius: 15px;
            padding: 5px 14px;
        """)
        header.addStretch()
        header.addWidget(status_pill)

        content.addLayout(header)
        content.addSpacing(4)

        # ---------------- Body ----------------
        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)

        # Profile area
        photo_wrap = QFrame()
        photo_wrap.setFixedSize(170, 190)
        photo_wrap.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
            }
        """)
        photo_wrap_layout = QVBoxLayout(photo_wrap)
        photo_wrap_layout.setContentsMargins(14, 14, 14, 14)

        photo = QLabel()
        photo.setFixedSize(146, 166)
        photo.setAlignment(Qt.AlignCenter)

        # image_path is already an absolute path from data_path(); use directly.
        # Fall back to the bundled default avatar (resource_path) if missing.
        if image_path and os.path.exists(image_path):
            pix = QPixmap(image_path)
        else:
            pix = QPixmap(resource_path("assets/default_avatar.png"))

        photo.setPixmap(
            pix.scaled(
                146, 166,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
        )
        photo.setStyleSheet("border-radius: 10px;")
        photo_wrap_layout.addWidget(photo)
        body_layout.addWidget(photo_wrap)

        # Info area
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)

        name_lbl = QLabel(student_name)
        name_lbl.setFont(QFont("Segoe UI", 22, QFont.Bold))
        name_lbl.setContentsMargins(0, 2, 0, 2)
        name_lbl.setStyleSheet(f"color: {title_color};")

        subtitle_lbl = QLabel(message)
        subtitle_lbl.setFont(QFont("Segoe UI", 12))
        subtitle_lbl.setContentsMargins(0, 0, 0, 6)
        subtitle_lbl.setStyleSheet(f"color: {muted};")

        info_layout.addWidget(name_lbl)
        info_layout.addWidget(subtitle_lbl)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        row = 0
        grid.addWidget(self._field_label("Full Name", muted), row, 0, Qt.AlignLeft)
        grid.addWidget(self._field_value(student_name, title_color), row + 1, 0, Qt.AlignLeft)
        grid.addWidget(self._field_label("Student ID", muted), row, 1, Qt.AlignLeft)
        grid.addWidget(self._field_value(student_id or "N/A", title_color), row + 1, 1, Qt.AlignLeft)

        row += 2
        grid.addWidget(self._field_label("Class / Grade", muted), row, 0, Qt.AlignLeft)
        grid.addWidget(self._field_value(class_grade or "N/A", title_color), row + 1, 0, Qt.AlignLeft)
        grid.addWidget(self._field_label("Check-In Time", muted), row, 1, Qt.AlignLeft)
        grid.addWidget(self._field_value(check_in_time or "--", title_color), row + 1, 1, Qt.AlignLeft)

        row += 2
        grid.addWidget(self._field_label("Section", muted), row, 0, Qt.AlignLeft)
        grid.addWidget(self._field_value(section or "N/A", title_color), row + 1, 0, Qt.AlignLeft)
        grid.addWidget(self._field_label("Check-Out Time", muted), row, 1, Qt.AlignLeft)
        grid.addWidget(self._field_value(check_out_time or "--", title_color), row + 1, 1, Qt.AlignLeft)

        info_layout.addLayout(grid)

        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {accent_soft};
                border: 1px solid {accent};
                border-radius: 10px;
            }}
            QLabel {{
                color: {accent};
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(16, 12, 16, 12)
        stats_layout.setSpacing(8)

        if is_login:
            visits_text = f"Total visits: {total_visits}" if total_visits is not None else "Total visits: --"
            stats_layout.addWidget(self._info_label(visits_text))
        else:
            dur_text = self._format_duration(session_seconds) if session_seconds is not None else "--"
            stats_layout.addWidget(self._info_label(f"Session duration: {dur_text}"))

        stats_layout.addStretch()
        info_layout.addWidget(stats_frame)
        info_layout.addStretch()

        body_layout.addLayout(info_layout)
        content.addLayout(body_layout)

        root = QVBoxLayout(self)
        root.addWidget(container)

        self.adjustSize()

        # ---------------- Animations ----------------
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(400)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)

        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(400)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.finished.connect(self.close)

    # ------------------------------------------------
    def show_popup(self):
        self._center_on_screen()
        self.show()
        self.fade_in.start()
        QTimer.singleShot(self.duration_ms, self._start_fade_out)

    def _start_fade_out(self):
        self.fade_out.start()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )

    def _field_label(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setFont(QFont("Segoe UI", 9, QFont.Medium))
        lbl.setStyleSheet(f"color: {color}; letter-spacing: 0.6px;")
        return lbl

    def _field_value(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 13, QFont.DemiBold))
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 8px 12px;
            }}
        """)
        return lbl

    def _info_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        return lbl

    def _format_duration(self, seconds: int) -> str:
        if seconds is None:
            return "--"
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if mins:
            parts.append(f"{mins}m")
        if secs or not parts:
            parts.append(f"{secs}s")
        return " ".join(parts)
