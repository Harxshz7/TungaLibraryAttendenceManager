import sqlite3
from pathlib import Path

DB_PATH = Path("attendance.db")


def add_is_estimated_column():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if column already exists
    cur.execute("PRAGMA table_info(sessions)")
    columns = [row[1] for row in cur.fetchall()]

    if "is_estimated" in columns:
        print("Column 'is_estimated' already exists. Nothing to do.")
        conn.close()
        return

    print("Adding 'is_estimated' column to sessions table...")
    cur.execute("ALTER TABLE sessions ADD COLUMN is_estimated INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    add_is_estimated_column()
