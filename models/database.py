import sqlite3
import sys
from pathlib import Path

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[1]

DB_PATH = get_base_path() / "data" / "attendance.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        isolation_level=None  # autocommit
    )

    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS scans(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        scanned_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        start_at TEXT NOT NULL,
        end_at TEXT,
        duration_sec INTEGER
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_open
    ON sessions(student_id, end_at);

    CREATE TABLE IF NOT EXISTS students(
        student_id TEXT PRIMARY KEY,
        name TEXT,
        class TEXT
    );
                      
    CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
    );

    """)

    conn.commit()
    conn.close()
