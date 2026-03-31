import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# -----------------------------
# CONFIGURATION
# -----------------------------
DB_PATH = Path("attendance.db")  # adjust if needed

MIN_SEC = 20 * 60   # 1200 seconds
MAX_SEC = 25 * 60   # 1500 seconds
THRESHOLD = 5 * 60  # 300 seconds


def normalize_short_sessions():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("🔍 Fetching sessions shorter than 5 minutes...")

    cur.execute("""
        SELECT id, start_at
        FROM sessions
        WHERE duration_sec < ?
          AND end_at IS NOT NULL
    """, (THRESHOLD,))

    rows = cur.fetchall()

    if not rows:
        print("✅ No short sessions to normalize.")
        conn.close()
        return

    print(f"⚙ Normalizing {len(rows)} short sessions...")

    for session_id, start_at in rows:
        start_dt = datetime.fromisoformat(start_at)

        new_duration = random.randint(MIN_SEC, MAX_SEC)
        new_end = start_dt + timedelta(seconds=new_duration)

        cur.execute("""
            UPDATE sessions
            SET duration_sec = ?,
                end_at = ?
            WHERE id = ?
        """, (
            new_duration,
            new_end.strftime("%Y-%m-%d %H:%M:%S"),
            session_id
        ))

    conn.commit()
    conn.close()

    print("✅ Short session normalization completed successfully.")


if __name__ == "__main__":
    normalize_short_sessions()
