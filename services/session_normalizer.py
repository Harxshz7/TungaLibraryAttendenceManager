from datetime import datetime
from models.database import get_connection

THRESHOLD_SEC = 50 * 60  # auto-close sessions open longer than 50 minutes


def normalize_stale_sessions():
    """
    Close open sessions that have run longer than THRESHOLD_SEC.

    The real elapsed time is stored, but is_estimated is set to 1 because
    the student likely forgot to scan out and the true checkout time is unknown.
    """

    conn = get_connection()
    cur = conn.cursor()

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
        dur = int((now - start_dt).total_seconds())

        cur.execute("""
            UPDATE sessions
            SET end_at = ?, duration_sec = ?, is_estimated = 1
            WHERE id = ?
        """, (
            now.strftime("%Y-%m-%d %H:%M:%S"),
            dur,
            sid
        ))

    conn.commit()
    conn.close()
