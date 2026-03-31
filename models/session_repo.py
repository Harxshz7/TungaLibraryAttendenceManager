from models.database import get_connection
from datetime import datetime

def get_live_sessions():
    conn = get_connection()
    cur = conn.cursor()

    sql = """
    SELECT
        s.student_id,
        COALESCE(st.name, ''),
        COALESCE(st.class, ''),
        s.start_at,
        s.end_at,
        CASE
            WHEN s.end_at IS NULL THEN
                strftime('%s','now','localtime') - strftime('%s', s.start_at)
            ELSE
                s.duration_sec
        END AS duration_sec
    FROM sessions s
    LEFT JOIN students st ON st.student_id = s.student_id
    WHERE date(s.start_at) = date('now','localtime')
       OR s.end_at IS NULL
    ORDER BY (s.end_at IS NULL) DESC, s.start_at DESC;
    """

    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()

    return rows


def get_present_count():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(DISTINCT student_id)
        FROM sessions
        WHERE end_at IS NULL
    """)

    count = cur.fetchone()[0]
    conn.close()
    return count

def get_student_history(student_id: str):
    """
    Returns all sessions for a student till date.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            date(start_at),
            time(start_at),
            time(end_at),
            duration_sec
        FROM sessions
        WHERE student_id = ?
        ORDER BY start_at DESC
    """, (student_id,))

    rows = cur.fetchall()
    conn.close()
    return rows

def get_student_history_range(student_id: str, start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            date(start_at),
            time(start_at),
            time(end_at),
            duration_sec
        FROM sessions
        WHERE student_id = ?
          AND date(start_at) BETWEEN date(?) AND date(?)
        ORDER BY start_at DESC
    """, (student_id, start_date, end_date))

    rows = cur.fetchall()
    conn.close()
    return rows