# Tunga Library Attendance Manager

A PySide6 desktop kiosk application for tracking library attendance via barcode/ID scanner input.

## Features

- **Scanner + Manual Input** — Barcode/ID scanner capture via hidden always-on-top window (`InputCaptureWindow`), with manual `InputMode.MANUAL` fallback triggered on tab switches and form focus
- **Live Session Tracking** — Check-in/check-out cycle managed by `AttendanceController.process_scan()`, with animated popup confirmation (`StudentPopup`) showing student photo, name, class, and session duration
- **System Tray / Kiosk Mode** — Starts minimized to system tray (`QSystemTrayIcon`); window close is blocked in kiosk mode (`MainWindow.closeEvent`), F12 exits kiosk
- **Reports** — Daily, monthly, and per-student attendance reports exported to Excel (`.xlsx`) via openpyxl, plus PDF export for student history (via ReportLab in `StudentHistoryWindow`)
- **Analytics** — Dashboard tab showing peak hours, daily averages, top users, and weekly trends (`analytics_service.py`)
- **Themes** — Light, dark, and college-blue QSS stylesheets (`themes/`), loaded at startup in `main.py`
- **Auto-Export** — `AppController.auto_export_yesterday()` runs on startup to export the previous day's report if not already done
- **Stale Session Cleanup** — `normalize_stale_sessions()` auto-closes open sessions older than 50 minutes, storing the true elapsed time but flagging them as `is_estimated = 1` (student likely forgot to scan out). Flagged sessions can be reviewed via the "Review Flagged Sessions" button.

## Tech Stack

- Python 3.10+
- PySide6 (Qt6)
- SQLite (WAL mode, autocommit via `isolation_level=None`)
- openpyxl (Excel export)
- pynput (optional keyboard listener, currently unused in favor of Qt input capture)

## Project Structure

```
.
├── main.py                  # Entry point (tray, theme, kiosk mode)
├── requirements.txt
├── assets/                  # Logo, default avatar, fonts, GIF
├── controllers/
│   ├── app_controller.py    # Auto-export logic, meta repo usage
│   └── attendance_controller.py  # Core scan handling, popup display, refresh loop
├── models/
│   ├── database.py          # SQLite connection, schema init (WAL mode)
│   ├── input_mode.py        # InputMode enum: SCANNER / MANUAL
│   ├── meta_repo.py         # Key-value metadata store (last export date)
│   ├── session_repo.py      # Queries: live sessions, present count, student history
│   └── student_repo.py      # CSV import, student info lookup
├── services/
│   ├── attendance_service.py       # handle_scan(): open/close sessions with duration normalization
│   ├── session_normalizer.py       # Auto-close stale sessions (>50 min)
│   ├── daily_report_service.py     # Daily Excel export
│   ├── monthly_report_service.py   # Monthly Excel export (Degree/PUC/Lecturers split)
│   ├── student_report_service.py   # Per-student Excel export
│   ├── analytics_service.py        # Peak hours, averages, top users, weekly trends
│   └── scanner_service.py          # Buffer-based scanner signal (unused, kept for reference)
├── views/
│   ├── main_window.py              # Dashboard: live table, clock, CSV import, report buttons
│   ├── student_popup.py            # Animated check-in/check-out popup with photo
│   ├── student_history_window.py   # Dialog with date filter, Excel/PDF export
│   ├── analytics_tab.py            # Analytics dashboard UI
│   ├── input_capture_window.py     # Hidden Qt window for scanner capture
│   ├── input_capture.py            # pynput keyboard listener (unused)
│   └── review_sessions_window.py   # Dialog for reviewing estimated/flagged sessions
├── utils/
│   ├── id_utils.py          # normalize_id(): adds S- prefix, strips invalid chars
│   ├── time_utils.py        # format_duration(): HH:MM:SS formatter
│   └── resource_utils.py    # PyInstaller-compatible resource path resolution
├── themes/
│   ├── light.qss
│   ├── dark.qss
│   └── college_blue.qss
├── data/
│   ├── migrate_attendance.py       # One-shot migration from old_attendance.db
│   ├── add_is_estimated_column.py  # Adds is_estimated column to existing DBs
│   ├── normalize_sessions.py       # Batch normalize long sessions
│   └── normalize_short_sessions.py # Batch normalize short sessions
├── tools/
│   └── normalize_legacy_sessions.py  # Normalize open + absurd-duration sessions
├── photos/                  # Student photos (gitignored)
├── reports/                 # Generated reports (gitignored)
│   ├── daily/
│   ├── monthly/
│   └── student/
└── assets/
    └── default_avatar.png   # Fallback when student photo is missing
```

## Setup

```bash
git clone <repo-url>
cd TungaLibraryAttendenceManager
pip install -r requirements.txt
python main.py
```

`python main.py`

## How It Works

1. On launch, `main.py` loads the Inter font, sets the QSS theme, creates `MainWindow`, and initializes the system tray. The `AttendanceController` starts a 30-second refresh timer.
2. When a barcode scanner scans an ID, `InputCaptureWindow` (a hidden 1x1px Qt window) receives the keystrokes and fires `on_scan_callback`.
3. The callback normalizes the ID via `normalize_id()` (e.g., `1623` → `S-1623`), looks up the student in `get_student_basic_info()`, and calls `AttendanceController.process_scan()`.
4. `process_scan()` calls `handle_scan()` in `attendance_service.py`:
   - If the student has an open session, it closes it (normalizing duration: short sessions bumped to 8-15 min, long sessions capped at 40-50 min).
   - If no open session, it creates one.
5. A `StudentPopup` is shown for 3.2 seconds with the student's photo, name, class, check-in/out time, and visit count or session duration.
6. The live dashboard table (`QTableWidget`) refreshes every 30 seconds via `get_live_sessions()`, showing today's sessions with real-time duration for open ones.

## Reports

All reports are saved under `reports/` (gitignored):

| Report | Location | Contents |
|--------|----------|----------|
| Daily | `reports/daily/Daily_YYYY_MM_DD.xlsx` | Summary sheet (total users, hours, distinct IDs) + Attendance sheet (per-student time) |
| Monthly | `reports/monthly/Monthly_YYYY_MM.xlsx` | Daily summary + All Students + Degree/PUC/Lecturers split sheets |
| Student | `reports/student/Student_{id}.xlsx` | Full attendance history with date range filter |

Student history is also exportable as PDF via `StudentHistoryWindow.export_pdf()`.

## Seeding Data

- **Students**: Import a CSV with columns `student_id,name,class` via the "Import Students CSV" button in the UI, or programmatically through `student_repo.import_students_from_csv()`.
- **Photos**: Place student photos at `photos/{student_id}.png` (e.g., `photos/S-1623.png`). The popup falls back to `assets/default_avatar.png` if no photo is found.

Both `photos/` and `data/*.db` are gitignored — they live locally and are not version-controlled.

## Screenshots

<!-- Replace with actual screenshots -->
![Dashboard](screenshots/dashboard.png)
![Check-in Popup](screenshots/popup.png)
![Analytics](screenshots/analytics.png)
![Reports](screenshots/reports.png)

## License

<!-- Choose a license and uncomment -->
<!-- This project is licensed under the MIT License. See LICENSE for details. -->
