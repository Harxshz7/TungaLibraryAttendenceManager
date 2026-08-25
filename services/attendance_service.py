import random
from datetime import datetime
from models.database import get_connection

# Duration normalization thresholds
SHORT_MIN_SEC = 8 * 60    # sessions shorter than 8 min → bumped to 8-15 min
SHORT_MAX_SEC = 15 * 60
LONG_THRESHOLD_SEC = 40 * 60  # sessions longer than 40 min → capped to 40-50 min
LONG_MAX_SEC = 50 * 60


def _normalize_duration(raw_sec: int) -> int:
    """
    Normalize session duration to avoid unrealistic values.
    Short sessions (<8 min) are bumped to 8-15 min.
    Long sessions (>40 min) are capped to 40-50 min.
    """
    if raw_sec < SHORT_MIN_SEC:
        return random.randint(SHORT_MIN_SEC, SHORT_MAX_SEC)
    if raw_sec > LONG_THRESHOLD_SEC:
        return random.randint(LONG_THRESHOLD_SEC, LONG_MAX_SEC)
    return raw_sec


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
        raw_sec = int((now - start_dt).total_seconds())
        dur_sec = _normalize_duration(raw_sec)

        cur.execute("""
            UPDATE sessions
            SET end_at=?, duration_sec=?
            WHERE id=?
        """, (
                now.strftime("%Y-%m-%d %H:%M:%S"),
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
