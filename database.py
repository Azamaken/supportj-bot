import sqlite3

conn = sqlite3.connect("data/support.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    is_banned INTEGER DEFAULT 0,
    thread_id INTEGER,
    last_activity INTEGER
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS topics (
    user_id INTEGER PRIMARY KEY,
    thread_id INTEGER,
    username TEXT,
    full_name TEXT,
    is_open INTEGER DEFAULT 1,
    last_activity INTEGER
)
''')
conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def upsert_user(user_id, username, full_name, thread_id, last_activity):
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, full_name, thread_id, last_activity)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            full_name=excluded.full_name,
            thread_id=excluded.thread_id,
            last_activity=excluded.last_activity
    ''', (user_id, username, full_name, thread_id, last_activity))
    conn.commit()

def ban_user(user_id: int):
    cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()

def unban_user(user_id: int):
    cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()

def is_banned(user_id: int) -> bool:
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return bool(row[0]) if row else False

def update_last_activity(user_id: int, timestamp: int):
    cursor.execute("UPDATE users SET last_activity = ? WHERE user_id = ?", (timestamp, user_id))
    conn.commit()

def get_all_active_threads() -> list[tuple[int, int, int]]:
    """
    Возвращает список (user_id, thread_id, last_activity)
    Только если thread_id указан
    """
    cursor.execute("SELECT user_id, thread_id, last_activity FROM users WHERE thread_id IS NOT NULL")
    return cursor.fetchall()

def clear_thread(user_id: int):
    cursor.execute("UPDATE users SET thread_id = NULL WHERE user_id = ?", (user_id,))
    conn.commit()

def get_topic_by_user(user_id: int):
    cursor.execute("SELECT * FROM topics WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def upsert_topic(user_id, thread_id, username, full_name, is_open, last_activity):
    cursor.execute('''
        INSERT OR REPLACE INTO topics (user_id, thread_id, username, full_name, is_open, last_activity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, thread_id, username, full_name, is_open, last_activity))
    conn.commit()

def mark_topic_closed(user_id: int):
    cursor.execute("UPDATE topics SET is_open = 0 WHERE user_id = ?", (user_id,))
    conn.commit()

def reopen_topic(user_id: int, thread_id: int, username: str, full_name: str):
    cursor.execute('''
        UPDATE topics
        SET is_open = 1, thread_id = ?, username = ?, full_name = ?
        WHERE user_id = ?
    ''', (thread_id, username, full_name, user_id))
    conn.commit()
