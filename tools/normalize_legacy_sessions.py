import random
from datetime import datetime, timedelta
from models.database import get_connection
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MIN_SEC = 45 * 60   
MAX_SEC = 50 * 60   
MAX_ALLOWED = 60 * 60  


def normalize_legacy_sessions():
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now()

    print("🔧 Normalizing legacy sessions...")

    # -------------------------------------------------
    # 1. FIX OPEN SESSIONS (end_at IS NULL)
    # -------------------------------------------------
    cur.execute("""
        SELECT id, start_at
        FROM sessions
        WHERE end_at IS NULL
    """)

    open_rows = cur.fetchall()
    print(f"• Found {len(open_rows)} open sessions")

    for sid, start_at in open_rows:
        start_dt = datetime.fromisoformat(start_at)

        dur = random.randint(MIN_SEC, MAX_SEC)
        end_dt = start_dt + timedelta(seconds=dur)

        if end_dt > now:
            end_dt = now
            dur = int((end_dt - start_dt).total_seconds())

        cur.execute("""
            UPDATE sessions
            SET end_at = ?, duration_sec = ?
            WHERE id = ?
        """, (
            end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            dur,
            sid
        ))

    # -------------------------------------------------
    # 2. FIX ABSURD DURATIONS (> 2 HOURS)
    # -------------------------------------------------
    cur.execute("""
        SELECT id, start_at, end_at, duration_sec
        FROM sessions
        WHERE duration_sec > ?
    """, (MAX_ALLOWED,))

    bad_rows = cur.fetchall()
    print(f"• Found {len(bad_rows)} sessions with absurd duration")

    for sid, start_at, end_at, old_dur in bad_rows:
        start_dt = datetime.fromisoformat(start_at)

        dur = random.randint(MIN_SEC, MAX_SEC)
        end_dt = start_dt + timedelta(seconds=dur)

        cur.execute("""
            UPDATE sessions
            SET end_at = ?, duration_sec = ?
            WHERE id = ?
        """, (
            end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            dur,
            sid
        ))

    conn.commit()
    conn.close()

    print("✅ Legacy session normalization complete.")


if __name__ == "__main__":
    normalize_legacy_sessions()
