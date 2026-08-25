import sqlite3
import pytest
import models.database
import sys

class MockConnection:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:', isolation_level=None)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
    
    def cursor(self):
        return self.conn.cursor()
        
    def execute(self, *args, **kwargs):
        return self.conn.execute(*args, **kwargs)
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        pass

@pytest.fixture
def db_conn(monkeypatch):
    mock = MockConnection()
    
    def mock_get_connection():
        return mock
        
    modules_to_patch = [
        "models.database",
        "models.session_repo",
        "models.student_repo",
        "models.meta_repo",
        "services.attendance_service",
        "services.session_normalizer",
        "services.analytics_service",
        "services.daily_report_service",
        "services.monthly_report_service",
        "services.student_report_service"
    ]
    
    for mod in modules_to_patch:
        if mod not in sys.modules:
            try:
                __import__(mod)
            except ImportError:
                continue
        monkeypatch.setattr(f"{mod}.get_connection", mock_get_connection, raising=False)
        
    models.database.init_db()
    
    yield mock.conn
    
    mock.conn.close()
