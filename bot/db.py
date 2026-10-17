import aiosqlite
from bot import config

_conn: aiosqlite.Connection | None = None

async def connect() -> None:
    global _conn
    _conn = await aiosqlite.connect(config.DB_PATH)
    
    # Users table
    await _conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            role        TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Groups table
    await _conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id     INTEGER PRIMARY KEY,
            title       TEXT,
            added_by    INTEGER NOT NULL,
            created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Stats table
    await _conn.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           INTEGER NOT NULL,
            username          TEXT,
            chat_id           INTEGER NOT NULL,
            timestamp         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            duration_sec      INTEGER NOT NULL,
            file_size_bytes   INTEGER NOT NULL
        )
    """)
    
    # Settings table
    await _conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Safe migrations for existing databases
    try:
        await _conn.execute("ALTER TABLE stats ADD COLUMN chat_id INTEGER NOT NULL DEFAULT 0")
    except aiosqlite.OperationalError:
        pass
    try:
        await _conn.execute("ALTER TABLE stats ADD COLUMN username TEXT")
    except aiosqlite.OperationalError:
        pass
        
    await _conn.commit()

async def close() -> None:
    if _conn:
        await _conn.close()

# --- Settings ---
async def get_setting(key: str, default: str = "") -> str:
    async with _conn.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
        row = await cur.fetchone()
    return row[0] if row else default

async def set_setting(key: str, value: str) -> None:
    await _conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    await _conn.commit()

# --- Users ---
async def get_user(user_id: int) -> dict | None:
    async with _conn.execute("SELECT user_id, username, role FROM users WHERE user_id = ?", (user_id,)) as cur:
        row = await cur.fetchone()
    return {"user_id": row[0], "username": row[1], "role": row[2]} if row else None

async def create_user(user_id: int, username: str | None, role: str) -> None:
    await _conn.execute("INSERT OR IGNORE INTO users (user_id, username, role) VALUES (?, ?, ?)", (user_id, username, role))
    await _conn.commit()

async def set_role(user_id: int, role: str) -> None:
    await _conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
    await _conn.commit()

async def get_all_users() -> list[dict]:
    async with _conn.execute("SELECT user_id, username, role FROM users ORDER BY created_at") as cur:
        rows = await cur.fetchall()
    return [{"user_id": r[0], "username": r[1], "role": r[2]} for r in rows]

async def get_admins() -> list[dict]:
    async with _conn.execute("SELECT user_id, username, role FROM users WHERE role = 'admin'") as cur:
        rows = await cur.fetchall()
    return [{"user_id": r[0], "username": r[1], "role": r[2]} for r in rows]

async def is_first_user() -> bool:
    async with _conn.execute("SELECT COUNT(*) FROM users") as cur:
        (count,) = await cur.fetchone()
    return count == 0

# --- Groups ---
async def add_group(chat_id: int, title: str, added_by: int) -> None:
    await _conn.execute("INSERT OR REPLACE INTO groups (chat_id, title, added_by) VALUES (?, ?, ?)", (chat_id, title, added_by))
    await _conn.commit()

async def get_group(chat_id: int) -> dict | None:
    async with _conn.execute("SELECT chat_id, title, added_by FROM groups WHERE chat_id = ?", (chat_id,)) as cur:
        row = await cur.fetchone()
    return {"chat_id": row[0], "title": row[1], "added_by": row[2]} if row else None

async def remove_group(chat_id: int) -> None:
    await _conn.execute("DELETE FROM groups WHERE chat_id = ?", (chat_id,))
    await _conn.commit()

# --- Stats ---
async def add_stat(user_id: int, username: str | None, chat_id: int, duration_sec: int, file_size_bytes: int) -> None:
    await _conn.execute(
        "INSERT INTO stats (user_id, username, chat_id, duration_sec, file_size_bytes) VALUES (?, ?, ?, ?, ?)", 
        (user_id, username, chat_id, duration_sec, file_size_bytes)
    )
    await _conn.commit()

async def get_global_stats() -> dict:
    async with _conn.execute("SELECT COUNT(*), SUM(duration_sec), SUM(file_size_bytes) FROM stats") as cur:
        count, duration, size = await cur.fetchone()
    return {"count": count or 0, "duration": duration or 0, "size": size or 0}

async def get_user_stats(user_id: int) -> dict:
    async with _conn.execute("SELECT COUNT(*), SUM(duration_sec), SUM(file_size_bytes) FROM stats WHERE user_id = ?", (user_id,)) as cur:
        count, duration, size = await cur.fetchone()
    return {"count": count or 0, "duration": duration or 0, "size": size or 0}

async def get_groups_stats() -> list[dict]:
    async with _conn.execute("""
        SELECT s.chat_id, g.title, COUNT(*), SUM(s.duration_sec), SUM(s.file_size_bytes)
        FROM stats s
        LEFT JOIN groups g ON s.chat_id = g.chat_id
        WHERE s.chat_id != s.user_id
        GROUP BY s.chat_id
        ORDER BY COUNT(*) DESC
    """) as cur:
        rows = await cur.fetchall()
    return [
        {"chat_id": r[0], "title": r[1] or f"Group {r[0]}", "count": r[2], "duration": r[3], "size": r[4]} 
        for r in rows
    ]

async def get_group_details(chat_id: int) -> dict:
    async with _conn.execute("""
        SELECT COUNT(*), SUM(duration_sec), SUM(file_size_bytes) 
        FROM stats WHERE chat_id = ?
    """, (chat_id,)) as cur:
        total_count, total_duration, total_size = await cur.fetchone()
        
    async with _conn.execute("""
        SELECT user_id, username, COUNT(*), SUM(duration_sec)
        FROM stats WHERE chat_id = ?
        GROUP BY user_id
        ORDER BY COUNT(*) DESC
    """, (chat_id,)) as cur:
        users_rows = await cur.fetchall()
        
    users_list = [
        {"user_id": r[0], "username": r[1], "count": r[2], "duration": r[3]} 
        for r in users_rows
    ]
    
    return {
        "total_count": total_count or 0,
        "total_duration": total_duration or 0,
        "total_size": total_size or 0,
        "users": users_list
    }

async def search_user(query: str) -> list[dict]:
    q_str = f"%{query}%"
    async with _conn.execute("""
        SELECT user_id, username, SUM(duration_sec), SUM(file_size_bytes), COUNT(*) 
        FROM stats 
        WHERE CAST(user_id AS TEXT) LIKE ? OR username LIKE ?
        GROUP BY user_id
    """, (q_str, q_str)) as cur:
        rows = await cur.fetchall()
    return [
        {"user_id": r[0], "username": r[1], "duration": r[2], "size": r[3], "count": r[4]} 
        for r in rows
    ]