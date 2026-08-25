from services.analytics_service import get_peak_hours, get_daily_averages

def test_get_peak_hours(db_conn):
    db_conn.execute("INSERT INTO sessions (student_id, start_at, duration_sec) VALUES ('S1', '2023-10-01 10:15:00', 3600)")
    db_conn.execute("INSERT INTO sessions (student_id, start_at, duration_sec) VALUES ('S2', '2023-10-01 10:30:00', 3600)")
    db_conn.execute("INSERT INTO sessions (student_id, start_at, duration_sec) VALUES ('S3', '2023-10-01 14:00:00', 3600)")
    
    peak_hours = get_peak_hours()
    
    assert len(peak_hours) == 2
    assert peak_hours[0][0] == '10'
    assert peak_hours[0][1] == 2
    assert peak_hours[1][0] == '14'
    assert peak_hours[1][1] == 1

def test_get_daily_averages(db_conn):
    db_conn.execute("INSERT INTO sessions (student_id, start_at, duration_sec) VALUES ('S1', '2023-10-01 10:00:00', 3600)")
    db_conn.execute("INSERT INTO sessions (student_id, start_at, duration_sec) VALUES ('S2', '2023-10-01 11:00:00', 7200)")
    db_conn.execute("INSERT INTO sessions (student_id, start_at, duration_sec) VALUES ('S3', '2023-10-02 10:00:00', 3600)")
    
    daily_avg = get_daily_averages()
    
    assert daily_avg[0] == 1.5
    assert daily_avg[1] == 2.0
