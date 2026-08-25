import time
from services.session_normalizer import normalize_stale_sessions
from datetime import datetime, timedelta

def test_normalize_stale_sessions(db_conn, monkeypatch):
    real_now = datetime.now()
    start_time = real_now - timedelta(minutes=60)
    
    db_conn.execute(
        "INSERT INTO sessions (student_id, start_at) VALUES ('S1', ?)",
        (start_time.strftime("%Y-%m-%d %H:%M:%S"),)
    )
    
    normalize_stale_sessions()
    
    cur = db_conn.cursor()
    cur.execute("SELECT end_at, duration_sec, is_estimated FROM sessions WHERE student_id = 'S1'")
    row = cur.fetchone()
    
    assert row is not None
    assert row[0] is not None
    assert row[1] >= 3600
    assert row[2] == 1
