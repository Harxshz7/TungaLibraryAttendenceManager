from models.session_repo import get_live_sessions, get_estimated_sessions

def test_insert_and_retrieve_live_session(db_conn):
    db_conn.execute("INSERT INTO students (student_id, name, class) VALUES ('S1', 'Alice', '10A')")
    db_conn.execute("INSERT INTO sessions (student_id, start_at) VALUES ('S1', '2023-10-01 10:00:00')")
    
    sessions = get_live_sessions()
    
    assert len(sessions) == 1
    assert sessions[0][0] == 'S1'
    assert sessions[0][1] == 'Alice'
    assert sessions[0][4] is None
    assert sessions[0][6] == 0

def test_closing_session(db_conn):
    db_conn.execute("INSERT INTO students (student_id, name) VALUES ('S2', 'Bob')")
    db_conn.execute("INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated) VALUES ('S2', '2023-10-01 10:00:00', '2023-10-01 11:00:00', 3600, 0)")
    
    cur = db_conn.cursor()
    cur.execute("SELECT student_id, end_at, duration_sec FROM sessions WHERE student_id = 'S2'")
    row = cur.fetchone()
    
    assert row[1] == '2023-10-01 11:00:00'
    assert row[2] == 3600

def test_get_estimated_sessions(db_conn):
    db_conn.execute("INSERT INTO students (student_id, name) VALUES ('S3', 'Charlie')")
    db_conn.execute("INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated) VALUES ('S3', '2023-10-01 10:00:00', '2023-10-01 11:00:00', 3600, 1)")
    db_conn.execute("INSERT INTO sessions (student_id, start_at, end_at, duration_sec, is_estimated) VALUES ('S3', '2023-10-01 12:00:00', '2023-10-01 13:00:00', 3600, 0)")
    
    estimated = get_estimated_sessions()
    
    assert len(estimated) == 1
    assert estimated[0][0] == 'S3'
    assert estimated[0][6] == 3600
