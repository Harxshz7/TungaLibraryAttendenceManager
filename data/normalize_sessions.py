import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# -----------------------------
# CONFIGURATION
# -----------------------------
DB_PATH = Path("attendance.db")   # 🔁 change if needed
MIN_SEC = 40 * 60   # 2400 seconds
MAX_SEC = 45 * 60   # 2700 seconds
THRESHOLD = 50 * 60 # 3000 seconds


def normalize_sessions():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("🔍 Fetching sessions exceeding 50 minutes...")

    cur.execute("""
        SELECT id, start_at
        FROM sessions
        WHERE duration_sec > ?
          AND end_at IS NOT NULL
    """, (THRESHOLD,))

    rows = cur.fetchall()

    if not rows:
        print("✅ No sessions need normalization.")
        conn.close()
        return

    print(f"⚙ Normalizing {len(rows)} sessions...")

    for session_id, start_at in rows:
        start_dt = datetime.fromisoformat(start_at)

        # Random duration between 40–45 min
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

    print("✅ Normalization completed successfully.")


if __name__ == "__main__":
    normalize_sessions()
