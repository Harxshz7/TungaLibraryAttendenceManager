from datetime import date
import openpyxl
import pytest
from services.daily_report_service import export_daily_report
from services.monthly_report_service import export_monthly_report
from services.student_report_service import export_student_report

def test_daily_report_export(db_conn, monkeypatch, tmp_path):
    report_dir = tmp_path / "daily"
    monkeypatch.setattr("services.daily_report_service.REPORT_DIR", report_dir)

    # Seed students
    db_conn.execute("INSERT INTO students (student_id, name, class) VALUES ('S1', 'Alice', 'BCA 1')")
    db_conn.execute("INSERT INTO students (student_id, name, class) VALUES ('S2', 'Bob', 'BSc 2')")

    # Seed sessions on 2023-10-15
    db_conn.execute("""
        INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated)
        VALUES ('S1', '2023-10-15 10:00:00', '2023-10-15 11:00:00', 3600, 0)
    """)
    db_conn.execute("""
        INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated)
        VALUES ('S2', '2023-10-15 12:00:00', '2023-10-15 13:00:00', 3600, 1)
    """)

    file_path = export_daily_report(date(2023, 10, 15))
    assert file_path is not None

    wb = openpyxl.load_workbook(file_path)
    assert "Summary" in wb.sheetnames
    assert "Attendance" in wb.sheetnames

    att_ws = wb["Attendance"]
    # Header is at row 2 (ID, Name, Class, Time Spent, Estimated)
    # Data starts at row 3
    rows = list(att_ws.iter_rows(values_only=True))
    header = rows[1]
    assert header == ("ID", "Name", "Class", "Time Spent", "Estimated")

    data_rows = rows[2:]
    assert len(data_rows) == 2
    
    # Alice (S1) unflagged, Bob (S2) flagged
    s1_row = next(r for r in data_rows if r[0] == "S1")
    s2_row = next(r for r in data_rows if r[0] == "S2")
    assert s1_row[4] in ("", None)
    assert s2_row[4] == "Yes"


def test_daily_report_no_data_raises_value_error(db_conn, monkeypatch, tmp_path):
    report_dir = tmp_path / "daily"
    monkeypatch.setattr("services.daily_report_service.REPORT_DIR", report_dir)

    with pytest.raises(ValueError, match="No attendance data found"):
        export_daily_report(date(2023, 1, 1))

def test_monthly_report_export(db_conn, monkeypatch, tmp_path):
    report_dir = tmp_path / "monthly"
    monkeypatch.setattr("services.monthly_report_service.REPORT_DIR", report_dir)

    # Seed students from different sections
    db_conn.execute("INSERT INTO students (student_id, name, class) VALUES ('S1', 'Alice', 'BCA 1')")
    db_conn.execute("INSERT INTO students (student_id, name, class) VALUES ('S2', 'Bob', '1st PUC Science')")
    db_conn.execute("INSERT INTO students (student_id, name, class) VALUES ('L-01', 'Prof. Smith', 'Staff')")

    # Seed sessions in October 2023
    db_conn.execute("""
        INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated)
        VALUES ('S1', '2023-10-10 10:00:00', '2023-10-10 11:00:00', 3600, 0)
    """)
    db_conn.execute("""
        INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated)
        VALUES ('S2', '2023-10-11 10:00:00', '2023-10-11 11:00:00', 3600, 1)
    """)
    db_conn.execute("""
        INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated)
        VALUES ('L-01', '2023-10-12 10:00:00', '2023-10-12 11:00:00', 3600, 0)
    """)

    file_path = export_monthly_report(2023, 10)
    assert file_path is not None

    wb = openpyxl.load_workbook(file_path)
    expected_sheets = ["Daily Summary", "All Students", "Degree Students", "PUC Students", "Lecturers"]
    for sheet in expected_sheets:
        assert sheet in wb.sheetnames

    # Check Degree vs PUC vs Lecturer sheet separation
    deg_rows = list(wb["Degree Students"].iter_rows(values_only=True))[1:]
    assert len(deg_rows) == 1
    assert deg_rows[0][0] == "S1"

    puc_rows = list(wb["PUC Students"].iter_rows(values_only=True))[1:]
    assert len(puc_rows) == 1
    assert puc_rows[0][0] == "S2"
    assert puc_rows[0][4] == "Yes"  # Estimated flag

    lec_rows = list(wb["Lecturers"].iter_rows(values_only=True))[1:]
    assert len(lec_rows) == 1
    assert lec_rows[0][0] == "L-01"

def test_student_report_export(db_conn, monkeypatch, tmp_path):
    report_dir = tmp_path / "student"
    monkeypatch.setattr("services.student_report_service.REPORT_DIR", report_dir)

    # Seed student and sessions
    db_conn.execute("INSERT INTO students (student_id, name, class) VALUES ('S100', 'John Doe', 'BCom 3')")
    db_conn.execute("""
        INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated)
        VALUES ('S100', '2023-10-01 09:00:00', '2023-10-01 10:00:00', 3600, 0)
    """)
    db_conn.execute("""
        INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated)
        VALUES ('S100', '2023-10-05 14:00:00', '2023-10-05 15:30:00', 5400, 1)
    """)

    file_path = export_student_report("S100")
    assert file_path is not None

    wb = openpyxl.load_workbook(file_path)
    assert "Attendance History" in wb.sheetnames
    ws = wb["Attendance History"]

    # Verify Summary Block values
    assert ws["A1"].value == "Student ID"
    assert ws["B1"].value == "S100"
    assert ws["A2"].value == "Total Visits"
    assert ws["B2"].value == 2

    # Verify Data Rows
    rows = list(ws.iter_rows(values_only=True))
    # Row index 7 is table header: ['Date', 'Entry Time', 'Exit Time', 'Duration', 'Estimated']
    table_rows = rows[7:]
    assert len(table_rows) == 2
    assert table_rows[0][0] == "2023-10-01"
    assert table_rows[0][4] in ("", None)
    assert table_rows[1][0] == "2023-10-05"
    assert table_rows[1][4] == "Yes"
