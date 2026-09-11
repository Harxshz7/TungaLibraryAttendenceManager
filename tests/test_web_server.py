import hashlib
import sqlite3
import pytest
from fastapi.testclient import TestClient
from web.server import app, ro_get_connection
import models.database

client = TestClient(app)

def test_health_endpoint_no_auth():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_protected_routes_unauthorized_without_credentials():
    routes = ["/", "/history", "/analytics", "/events/live-sessions"]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

def test_protected_routes_authorized_with_credentials(monkeypatch, tmp_path):
    # Setup test credentials
    test_user = "admin_user"
    test_pass = "secret_pass"
    pass_hash = hashlib.sha256(test_pass.encode("utf-8")).hexdigest()

    test_config = tmp_path / "web_config.json"
    test_config.write_text(f'{{"username": "{test_user}", "password_hash": "{pass_hash}"}}')

    test_db = tmp_path / "attendance.db"
    init_conn = sqlite3.connect(test_db)
    init_conn.executescript("""
        CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, scanned_at TEXT);
        CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, start_at TEXT, end_at TEXT, duration_sec INTEGER, is_estimated INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS students(student_id TEXT PRIMARY KEY, name TEXT, class TEXT);
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
    """)
    init_conn.commit()
    init_conn.close()

    monkeypatch.setattr("models.database.DB_PATH", test_db)

    auth = (test_user, test_pass)

    # Test Dashboard Home (/)
    res_home = client.get("/", auth=auth)
    assert res_home.status_code == 200
    assert "Live Sessions" in res_home.text

    # Test History (/history)
    res_history = client.get("/history", auth=auth)
    assert res_history.status_code == 200
    assert "Student History" in res_history.text

    # Test Analytics (/analytics)
    res_analytics = client.get("/analytics", auth=auth)
    assert res_analytics.status_code == 200
    assert "Analytics" in res_analytics.text

def test_read_only_database_connection(monkeypatch, tmp_path):
    # Create an actual test database file
    db_file = tmp_path / "test_ro.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO test VALUES (1, 'readonly')")
    conn.commit()
    conn.close()

    monkeypatch.setattr(models.database, "DB_PATH", db_file)

    # Connect using ro_get_connection()
    ro_conn = ro_get_connection()
    cur = ro_conn.cursor()

    # Reads should succeed
    cur.execute("SELECT name FROM test WHERE id = 1")
    row = cur.fetchone()
    assert row[0] == "readonly"

    # Writes must be rejected with OperationalError (attempt to write a readonly database)
    with pytest.raises(sqlite3.OperationalError, match="readonly|read-only"):
        cur.execute("INSERT INTO test VALUES (2, 'fail')")

    ro_conn.close()
