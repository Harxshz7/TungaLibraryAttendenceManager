import random
from datetime import datetime, timedelta
from models.database import get_connection

# Duration rules (seconds)
SHORT_THRESHOLD_SEC = 4 * 60      # < 4 minutes gets bumped
SHORT_MIN_SEC = 8 * 60            # lower bound for short normalization
SHORT_MAX_SEC = 15 * 60 + 59      # upper bound (include seconds)
LONG_MIN_SEC = 40 * 60            # lower bound for long-session normalization
LONG_MAX_SEC = 50 * 60            # upper bound for long-session normalization


def _normalize_duration(start_dt: datetime, end_dt: datetime) -> tuple[int, datetime]:
    """
    Normalize session duration based on business rules.

    Returns (duration_sec, normalized_end_dt).
    """
    raw_seconds = int((end_dt - start_dt).total_seconds())

    if raw_seconds < SHORT_THRESHOLD_SEC:
        normalized_seconds = random.randint(SHORT_MIN_SEC, SHORT_MAX_SEC)
    elif raw_seconds > LONG_MAX_SEC:
        normalized_seconds = min(max(raw_seconds, LONG_MIN_SEC), LONG_MAX_SEC)
    else:
        normalized_seconds = raw_seconds

    normalized_end = start_dt + timedelta(seconds=normalized_seconds)
    return normalized_seconds, normalized_end

def handle_scan(student_id: str):
    now = datetime.now()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO scans(student_id, scanned_at) VALUES (?, ?)",
        (student_id, now.strftime("%Y-%m-%d %H:%M:%S"))
    )

    cur.execute("""
        SELECT id, start_at FROM sessions
        WHERE student_id=? AND end_at IS NULL
        ORDER BY id DESC LIMIT 1
    """, (student_id,))

    row = cur.fetchone()

    if row:
        sid, start = row
        start_dt = datetime.fromisoformat(start)
        dur_sec, normalized_end = _normalize_duration(start_dt, now)

        cur.execute("""
            UPDATE sessions
            SET end_at=?, duration_sec=?
            WHERE id=?
        """, (
            normalized_end.strftime("%Y-%m-%d %H:%M:%S"),
            dur_sec,
            sid
        ))
    else:
        cur.execute("""
            INSERT INTO sessions(student_id, start_at)
            VALUES (?, ?)
        """, (student_id, now.strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
