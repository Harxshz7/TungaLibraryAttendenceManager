import sqlite3
from pathlib import Path

# -----------------------------
# CONFIGURATION
# -----------------------------
NEW_DB = Path("attendance.db")       # new system DB
OLD_DB = Path("old_attendance.db")   # old system DB (READ ONLY)


def migrate():
    if not NEW_DB.exists():
        raise FileNotFoundError(f"NEW DB not found: {NEW_DB}")

    if not OLD_DB.exists():
        raise FileNotFoundError(f"OLD DB not found: {OLD_DB}")

    print("🔌 Connecting to NEW database...")
    conn = sqlite3.connect(NEW_DB)
    cur = conn.cursor()

    try:
        print("🧹 Clearing existing scans & sessions...")
        cur.executescript("""
        BEGIN TRANSACTION;

        DELETE FROM scans;
        DELETE FROM sessions;

        DELETE FROM sqlite_sequence
        WHERE name IN ('scans', 'sessions');

        COMMIT;
        """)

        print("🔗 Attaching OLD database (read-only)...")
        cur.execute(f"ATTACH DATABASE '{OLD_DB}' AS old")

        print("📥 Importing scans...")
        cur.execute("""
            INSERT INTO scans (student_id, scanned_at)
            SELECT student_id, scanned_at
            FROM old.scans
        """)

        print("📥 Importing sessions...")
        cur.execute("""
            INSERT INTO sessions (
                student_id,
                start_at,
                end_at,
                duration_sec
            )
            SELECT
                student_id,
                start_at,
                end_at,
                duration_sec
            FROM old.sessions
        """)

        print("🔍 Verifying counts...")

        cur.execute("SELECT COUNT(*) FROM scans")
        new_scans = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM sessions")
        new_sessions = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM old.scans")
        old_scans = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM old.sessions")
        old_sessions = cur.fetchone()[0]

        print(f"   OLD scans     : {old_scans}")
        print(f"   NEW scans     : {new_scans}")
        print(f"   OLD sessions  : {old_sessions}")
        print(f"   NEW sessions  : {new_sessions}")

        if old_scans != new_scans or old_sessions != new_sessions:
            raise RuntimeError("❌ Row count mismatch! Migration aborted.")

        conn.commit()
        print("✅ Migration completed successfully.")

    except Exception as e:
        conn.rollback()
        print("❌ Migration failed. Rolling back.")
        raise e

    finally:
        cur.execute("DETACH DATABASE old")
        conn.close()


if __name__ == "__main__":
    migrate()
