from datetime import datetime
from models.database import get_connection


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
        dur_sec = int((now - start_dt).total_seconds())

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
