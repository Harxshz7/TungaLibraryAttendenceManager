from services.attendance_service import handle_scan
import pytest
from datetime import datetime

def test_handle_scan_check_in(db_conn, monkeypatch):
    class MockDatetime:
        @classmethod
        def now(cls):
            return datetime(2023, 10, 1, 10, 0, 0)
        @classmethod
        def fromisoformat(cls, date_string):
            return datetime.fromisoformat(date_string)
    monkeypatch.setattr("services.attendance_service.datetime", MockDatetime)

    handle_scan('S1')
    
    cur = db_conn.cursor()
    cur.execute("SELECT student_id, start_at, end_at FROM sessions WHERE student_id = 'S1'")
    row = cur.fetchone()
    
    assert row is not None
    assert row[1] == '2023-10-01 10:00:00'
    assert row[2] is None

def test_handle_scan_check_out(db_conn, monkeypatch):
    db_conn.execute("INSERT INTO sessions (student_id, start_at) VALUES ('S2', '2023-10-01 10:00:00')")
    
    class MockDatetime:
        @classmethod
        def now(cls):
            return datetime(2023, 10, 1, 10, 30, 0)
        @classmethod
        def fromisoformat(cls, date_string):
            return datetime.fromisoformat(date_string)
            
    monkeypatch.setattr("services.attendance_service.datetime", MockDatetime)
    
    handle_scan('S2')
    
    cur = db_conn.cursor()
    cur.execute("SELECT end_at, duration_sec, is_estimated FROM sessions WHERE student_id = 'S2'")
    row = cur.fetchone()
    
    assert row[0] == '2023-10-01 10:30:00'
    assert row[1] == 1800
    assert row[2] == 0

def test_handle_scan_short_session(db_conn, monkeypatch):
    db_conn.execute("INSERT INTO sessions (student_id, start_at) VALUES ('S3', '2023-10-01 10:00:00')")
    
    class MockDatetime:
        @classmethod
        def now(cls):
            return datetime(2023, 10, 1, 10, 3, 0)
        @classmethod
        def fromisoformat(cls, date_string):
            return datetime.fromisoformat(date_string)
            
    monkeypatch.setattr("services.attendance_service.datetime", MockDatetime)
    monkeypatch.setattr("services.attendance_service.random.randint", lambda a, b: 180)
    
    handle_scan('S3')
    
    cur = db_conn.cursor()
    cur.execute("SELECT end_at, duration_sec, is_estimated FROM sessions WHERE student_id = 'S3'")
    row = cur.fetchone()
    
    assert row[0] == '2023-10-01 10:03:00'
    assert row[1] == 180
    assert row[2] == 0
