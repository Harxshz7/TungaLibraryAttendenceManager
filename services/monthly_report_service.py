from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from models.database import get_connection
from datetime import date

REPORT_DIR = Path("reports/monthly")


def export_monthly_report(year: int, month: int) -> str:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    cur = conn.cursor()

    # ---------- DAILY SUMMARY ----------
    cur.execute("""
    WITH fixed AS (
        SELECT
            date(start_at, 'localtime') AS d,
            student_id,
            CASE
                WHEN end_at IS NOT NULL THEN duration_sec
                ELSE strftime('%s','now','localtime') - strftime('%s', start_at)
            END AS dur
        FROM sessions
        WHERE strftime('%Y', start_at) = ?
          AND strftime('%m', start_at) = ?
    )
    SELECT
        d AS Date,
        COUNT(*) AS 'Total Users',
        ROUND(SUM(dur)/3600.0, 2) AS 'Hours Spent',
        COUNT(DISTINCT student_id) AS 'Distinct IDs'
    FROM fixed
    GROUP BY d
    ORDER BY d;
    """, (str(year), f"{month:02}"))

    daily_summary = cur.fetchall()

    # ---------- ALL ATTENDANCE ----------
    cur.execute("""
    WITH fixed AS (
        SELECT
            s.student_id AS id,
            COALESCE(st.name,'') AS name,
            COALESCE(st.class,'') AS class,
            CASE
                WHEN s.end_at IS NOT NULL THEN s.duration_sec
                ELSE strftime('%s','now','localtime') - strftime('%s', s.start_at)
            END AS dur
        FROM sessions s
        LEFT JOIN students st ON st.student_id = s.student_id
        WHERE strftime('%Y', s.start_at) = ?
          AND strftime('%m', s.start_at) = ?
    )
    SELECT
        id, name, class,
        SUM(dur) AS total_sec
    FROM fixed
    GROUP BY id, name, class
    ORDER BY class, id;
    """, (str(year), f"{month:02}"))

    all_rows = cur.fetchall()
    conn.close()

    if not all_rows:
        raise ValueError("No attendance data for selected month")

    # ---------- EXCEL ----------
    wb = Workbook()
    wb.remove(wb.active)

    def add_sheet(title, headers, rows):
        ws = wb.create_sheet(title)
        ws.append(headers)
        ws.row_dimensions[1].font = Font(bold=True)

        for row in rows:
            ws.append(row)

        for col in ("A", "B", "C", "D"):
            ws.column_dimensions[col].width = 22

    # Sheet 1 – Daily Summary
    add_sheet(
        "Daily Summary",
        ["Date", "Total Users", "Hours Spent", "Distinct IDs"],
        daily_summary
    )

    # Helper to format seconds → h m
    def fmt(sec):
        h = sec // 3600
        m = (sec % 3600) // 60
        return f"{h}h {m}m"

    # All students
    all_data = [(i, n, c, fmt(s)) for i, n, c, s in all_rows]

    add_sheet(
        "All Students",
        ["ID", "Name", "Class", "Time Spent"],
        all_data
    )

    # Degree / PUC / Lecturers split
    degree = [r for r in all_data if "PUC" not in r[2].upper() and not r[0].startswith("L-")]
    puc = [r for r in all_data if "PUC" in r[2].upper()]
    lecturers = [r for r in all_data if r[0].startswith("L-")]

    add_sheet("Degree Students", ["ID", "Name", "Class", "Time Spent"], degree)
    add_sheet("PUC Students", ["ID", "Name", "Class", "Time Spent"], puc)
    add_sheet("Lecturers", ["ID", "Name", "Class", "Time Spent"], lecturers)

    file_path = REPORT_DIR / f"Monthly_{year}_{month:02}.xlsx"
    wb.save(file_path)

    return str(file_path)