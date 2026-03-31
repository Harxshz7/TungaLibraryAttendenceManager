import random
from datetime import datetime, timedelta
from models.database import get_connection

# Thresholds and normalization window (seconds)
THRESHOLD_SEC = 50 * 60          # normalize when open > 50 minutes
NORMAL_MIN_SEC = 40 * 60         # lower bound for stored duration
NORMAL_MAX_SEC = 50 * 60         # upper bound for stored duration


def normalize_stale_sessions():
    """
    Close open sessions that have run longer than THRESHOLD_SEC.

    We store a duration inside the [40, 50] minute window to prevent
    runaway long sessions from persisting indefinitely.
    """

    conn = get_connection()
    cur = conn.cursor()

    # Fetch open sessions older than the threshold (50 minutes)
    cur.execute("""
        SELECT id, start_at
        FROM sessions
        WHERE end_at IS NULL
          AND (strftime('%s','now','localtime') - strftime('%s', start_at)) >= ?
    """, (THRESHOLD_SEC,))

    rows = cur.fetchall()
    now = datetime.now()

    for sid, start_at in rows:
        start_dt = datetime.fromisoformat(start_at)

        # Random duration between 40–50 minutes
        dur = random.randint(NORMAL_MIN_SEC, NORMAL_MAX_SEC)
        end_dt = start_dt + timedelta(seconds=dur)

        # Safety: never end in the future; clamp duration into [40, 50] min
        if end_dt > now:
            end_dt = now
            dur = int((end_dt - start_dt).total_seconds())
            dur = min(max(dur, NORMAL_MIN_SEC), NORMAL_MAX_SEC)

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
