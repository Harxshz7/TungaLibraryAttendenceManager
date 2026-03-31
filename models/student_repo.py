import csv
from models.database import get_connection

def import_students_from_csv(csv_path: str) -> int:
    conn = get_connection()
    cur = conn.cursor()

    count = 0

    with open(csv_path, newline='', encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        for row in reader:
            if len(row) < 3:
                continue

            sid = row[0].strip()
            name = row[1].strip()
            cls = row[2].strip()

            # skip header
            if sid.lower() in ("studentid", "id"):
                continue

            cur.execute("""
                INSERT OR REPLACE INTO students(student_id, name, class)
                VALUES (?, ?, ?)
            """, (sid, name, cls))

            count += 1

    conn.commit()
    conn.close()
    return count

def get_student_basic_info(student_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, class
        FROM students
        WHERE student_id = ?
    """, (student_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "name": row[0],
        "class": row[1]
    }
