import hashlib
import os
from models.database import get_connection

def get_setting(key: str) -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key: str, value: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

def set_pin(new_pin: str):
    salt = os.urandom(16).hex()
    pin_hash = hashlib.sha256((new_pin + salt).encode('utf-8')).hexdigest()
    set_setting('admin_pin_salt', salt)
    set_setting('admin_pin', pin_hash)

def verify_pin(candidate: str) -> bool:
    salt = get_setting('admin_pin_salt')
    stored_hash = get_setting('admin_pin')
    
    if not salt or not stored_hash:
        return False
        
    candidate_hash = hashlib.sha256((candidate + salt).encode('utf-8')).hexdigest()
    return candidate_hash == stored_hash
