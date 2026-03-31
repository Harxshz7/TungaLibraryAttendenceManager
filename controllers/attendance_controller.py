import os
from PySide6.QtCore import QObject, QTimer, Signal
from services.attendance_service import handle_scan
from services.session_normalizer import normalize_stale_sessions
from models.session_repo import get_live_sessions, get_present_count
from utils.id_utils import normalize_id
from utils.resource_utils import data_path
from views.student_popup import StudentPopup
from models.student_repo import get_student_basic_info
from models.database import get_connection
from views.input_capture_window import InputCaptureWindow
from models.input_mode import InputMode
from datetime import datetime

_PHOTO_EXTENSIONS = (".png", ".jpg", ".JPG", ".jpeg", ".JPEG", ".PNG")

class AttendanceController(QObject):
    data_updated = Signal(list, int)  # rows, present_count

    def __init__(self, refresh_interval_ms=30_000):
        super().__init__()
        self.input_mode = InputMode.SCANNER
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(refresh_interval_ms)
        self._active_popup = None
        self.input_capture = InputCaptureWindow(self._on_scan)


        # initial normalization
        normalize_stale_sessions()
        self.refresh()

    def _find_photo(self, student_id: str) -> str | None:
        """Return absolute path to student photo, trying all common extensions."""
        for ext in _PHOTO_EXTENSIONS:
            p = data_path(f"photos/{student_id}{ext}")
            if os.path.exists(p):
                return p
        return None

    def set_input_mode(self, mode: InputMode):
        self.input_mode = mode
        if mode == InputMode.SCANNER:
            self.input_capture.start()
        else:
            self.input_capture.stop()

    def _on_scan(self, raw):
        if self.input_mode != InputMode.SCANNER:
            return

        sid = normalize_id(raw)
        student = get_student_basic_info(sid)
        if not student:
            return

        self.process_scan(sid)

    def enable_manual_temporarily(self, ms=30000):
        self.input_mode = InputMode.MANUAL
        QTimer.singleShot(
            ms,
            lambda: setattr(self, "input_mode", InputMode.SCANNER)
        )

    def _has_open_session(self, student_id: str) -> bool:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
                    SELECT 1
                    FROM sessions
                    WHERE student_id = ?
                      AND end_at IS NULL LIMIT 1
                    """, (student_id,))

        result = cur.fetchone()
        conn.close()

        return result is not None

    # ---------- SCAN ----------
    def process_scan(self, student_id: str):
        if self._active_popup:
            self._active_popup.close()
            self._active_popup = None
        was_inside = self._has_open_session(student_id)

        handle_scan(student_id)

        student = get_student_basic_info(student_id)
        name = student["name"] if student else student_id

        total_visits = self._get_total_visits(student_id)
        last_session = self._get_last_session_info(student_id)

        start_fmt = self._format_time(last_session["start_at"]) if last_session else None
        end_fmt = self._format_time(last_session["end_at"]) if last_session and last_session["end_at"] else None
        last_duration = (
            int(last_session["duration"])
            if last_session and last_session["duration"] is not None
            else None
        )

        class_grade = student.get("class") if student else None

        if not was_inside:
            self._active_popup = StudentPopup(
                student_name=name,
                message="Check-in recorded",
                student_id=student_id,
                class_grade=class_grade,
                image_path=self._find_photo(student_id),
                is_login=True,
                total_visits=total_visits,
                check_in_time=start_fmt,
            )
        else:
            self._active_popup = StudentPopup(
                student_name=name,
                message="Check-out recorded",
                student_id=student_id,
                class_grade=class_grade,
                image_path=self._find_photo(student_id),
                is_login=False,
                session_seconds=last_duration,
                check_in_time=start_fmt,
                check_out_time=end_fmt,
            )

        self._active_popup.show_popup()

        QTimer.singleShot(50, self.refresh)

    # ---------- REFRESH ----------
    def refresh(self):
        normalize_stale_sessions()

        rows = get_live_sessions()
        present = get_present_count()

        self.data_updated.emit(rows, present)

    def _get_total_visits(self, student_id: str) -> int:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sessions WHERE student_id = ?", (student_id,))
        count = cur.fetchone()[0]
        conn.close()
        return count

    def _get_last_session_duration(self, student_id: str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT duration_sec
            FROM sessions
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (student_id,))
        row = cur.fetchone()
        conn.close()
        if row and row[0] is not None:
            return int(row[0])
        return None

    def _get_last_session_info(self, student_id: str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT start_at, end_at, duration_sec
            FROM sessions
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (student_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "start_at": row[0],
            "end_at": row[1],
            "duration": row[2],
        }

    def _format_time(self, ts: str | None) -> str | None:
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts).strftime("%d %b %Y, %I:%M %p")
        except ValueError:
            return ts
