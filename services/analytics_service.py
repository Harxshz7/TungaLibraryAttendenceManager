from models.database import get_connection


def get_peak_hours(limit=6):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            strftime('%H', start_at) AS hour,
            COUNT(*) AS sessions
        FROM sessions
        GROUP BY hour
        ORDER BY sessions DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows

def get_daily_averages():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        WITH daily AS (
            SELECT
                date(start_at) AS day,
                COUNT(*) AS visits,
                SUM(duration_sec) AS total_sec
            FROM sessions
            GROUP BY day
        )
        SELECT
            ROUND(AVG(visits), 2),
            ROUND(AVG(total_sec) / 3600.0, 2)
        FROM daily
    """)

    row = cur.fetchone()
    conn.close()
    return row

def get_top_users(limit=10):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            s.student_id,
            COALESCE(st.name, ''),
            COUNT(*) AS visits
        FROM sessions s
        LEFT JOIN students st ON st.student_id = s.student_id
        GROUP BY s.student_id
        ORDER BY visits DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_weekly_trends():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            strftime('%w', start_at) AS weekday,
            COUNT(*) AS visits
        FROM sessions
        GROUP BY weekday
        ORDER BY weekday
    """)

    rows = cur.fetchall()
    conn.close()
    return rows
