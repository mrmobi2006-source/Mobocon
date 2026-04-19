import aiosqlite
import json
from config import DATABASE_URL, MAIN_ADMIN_ID, DEFAULT_DESCRIPTION, DEFAULT_FILE_TYPES, DEFAULT_REACTIONS_REQUIRED

DB = DATABASE_URL

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_main INTEGER DEFAULT 0,
            allowed_channels TEXT DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            channel_username TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            file_type TEXT DEFAULT 'general',
            file_name TEXT,
            caption TEXT,
            published_by INTEGER,
            channel_id TEXT,
            message_id INTEGER,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_id INTEGER,
            reacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, file_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS file_types (
            id TEXT PRIMARY KEY,
            name TEXT,
            emoji TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS pending_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            file_id TEXT,
            file_name TEXT,
            file_type TEXT DEFAULT 'general',
            caption TEXT,
            logo_file_id TEXT,
            step TEXT DEFAULT 'type',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Insert main admin
        await db.execute("""
            INSERT OR IGNORE INTO admins (user_id, username, full_name, is_main)
            VALUES (?, 'main_admin', 'Main Admin', 1)
        """, (MAIN_ADMIN_ID,))

        # Insert default file types
        for ft in DEFAULT_FILE_TYPES:
            await db.execute("""
                INSERT OR IGNORE INTO file_types (id, name, emoji, description)
                VALUES (?, ?, ?, ?)
            """, (ft["id"], ft["name"], ft["emoji"], DEFAULT_DESCRIPTION.get(ft["id"], "")))

        # Insert default settings
        defaults = {
            "bot_logo": "",
            "reactions_required": str(DEFAULT_REACTIONS_REQUIRED),
            "bot_description": "مرحباً بك في MOBO TUNNEL 🚀\n\nاحصل على أحدث ملفات الإنترنت ويوتيوب مجاناً!",
            "welcome_message": "👋 أهلاً {name}!\n\nمرحباً بك في بوت MOBO TUNNEL\n\n🎬 ملفات يوتيوب\n🌐 ملفات إنترنت مجاني\n\nتابع قناتنا للحصول على أحدث الملفات!",
        }
        for key, val in defaults.items():
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

        await db.commit()

# ─── Admin Management ───────────────────────────────────────────
async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return await cur.fetchone() is not None

async def is_main_admin(user_id: int) -> bool:
    return user_id == MAIN_ADMIN_ID

async def add_admin(user_id: int, username: str, full_name: str, added_by: int, channels: list = None):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO admins (user_id, username, full_name, added_by, allowed_channels)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, full_name, added_by, json.dumps(channels or [])))
        await db.commit()

async def remove_admin(user_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ? AND is_main = 0", (user_id,))
        await db.commit()

async def get_all_admins():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT user_id, username, full_name, is_main, allowed_channels FROM admins")
        rows = await cur.fetchall()
        return [{"user_id": r[0], "username": r[1], "full_name": r[2], "is_main": r[3], "allowed_channels": json.loads(r[4] or "[]")} for r in rows]

async def get_admin(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT user_id, username, full_name, is_main, allowed_channels FROM admins WHERE user_id = ?", (user_id,))
        r = await cur.fetchone()
        if r:
            return {"user_id": r[0], "username": r[1], "full_name": r[2], "is_main": r[3], "allowed_channels": json.loads(r[4] or "[]")}
        return None

async def update_admin_channels(user_id: int, channels: list):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE admins SET allowed_channels = ? WHERE user_id = ?", (json.dumps(channels), user_id))
        await db.commit()

# ─── Channel Management ─────────────────────────────────────────
async def add_channel(channel_id: str, name: str, username: str, added_by: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO channels (channel_id, channel_name, channel_username, added_by)
            VALUES (?, ?, ?, ?)
        """, (channel_id, name, username, added_by))
        await db.commit()

async def remove_channel(channel_id: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        await db.commit()

async def get_all_channels():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT channel_id, channel_name, channel_username, is_active FROM channels")
        rows = await cur.fetchall()
        return [{"channel_id": r[0], "name": r[1], "username": r[2], "is_active": r[3]} for r in rows]

async def get_channel(channel_id: str):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT channel_id, channel_name, channel_username FROM channels WHERE channel_id = ?", (channel_id,))
        r = await cur.fetchone()
        if r:
            return {"channel_id": r[0], "name": r[1], "username": r[2]}
        return None

# ─── File Management ────────────────────────────────────────────
async def save_file(file_id: str, file_type: str, file_name: str, caption: str, published_by: int, channel_id: str, message_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("""
            INSERT INTO files (file_id, file_type, file_name, caption, published_by, channel_id, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file_id, file_type, file_name, caption, published_by, channel_id, message_id))
        await db.commit()
        return cur.lastrowid

async def get_latest_file(file_type: str = None):
    async with aiosqlite.connect(DB) as db:
        if file_type:
            cur = await db.execute("""
                SELECT id, file_id, file_type, file_name, caption, channel_id, message_id
                FROM files WHERE file_type = ? AND is_active = 1
                ORDER BY published_at DESC LIMIT 1
            """, (file_type,))
        else:
            cur = await db.execute("""
                SELECT id, file_id, file_type, file_name, caption, channel_id, message_id
                FROM files WHERE is_active = 1
                ORDER BY published_at DESC LIMIT 1
            """)
        r = await cur.fetchone()
        if r:
            return {"id": r[0], "file_id": r[1], "file_type": r[2], "file_name": r[3], "caption": r[4], "channel_id": r[5], "message_id": r[6]}
        return None

async def get_file_by_id(file_db_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("""
            SELECT id, file_id, file_type, file_name, caption, channel_id, message_id
            FROM files WHERE id = ? AND is_active = 1
        """, (file_db_id,))
        r = await cur.fetchone()
        if r:
            return {"id": r[0], "file_id": r[1], "file_type": r[2], "file_name": r[3], "caption": r[4], "channel_id": r[5], "message_id": r[6]}
        return None

# ─── Reaction Management ────────────────────────────────────────
async def add_reaction(user_id: int, file_db_id: int) -> bool:
    """Returns True if new reaction, False if already reacted"""
    async with aiosqlite.connect(DB) as db:
        try:
            await db.execute("INSERT INTO reactions (user_id, file_id) VALUES (?, ?)", (user_id, file_db_id))
            await db.commit()
            return True
        except:
            return False

async def has_reacted(user_id: int, file_db_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT 1 FROM reactions WHERE user_id = ? AND file_id = ?", (user_id, file_db_id))
        return await cur.fetchone() is not None

async def get_reaction_count(file_db_id: int) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT COUNT(*) FROM reactions WHERE file_id = ?", (file_db_id,))
        r = await cur.fetchone()
        return r[0] if r else 0

# ─── User Management ────────────────────────────────────────────
async def register_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, username, full_name, last_seen)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, username, full_name))
        await db.commit()

async def get_user_count() -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        r = await cur.fetchone()
        return r[0] if r else 0

async def get_all_user_ids():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT user_id FROM users")
        rows = await cur.fetchall()
        return [r[0] for r in rows]

# ─── Settings ───────────────────────────────────────────────────
async def get_setting(key: str) -> str:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        r = await cur.fetchone()
        return r[0] if r else ""

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()

# ─── File Types ─────────────────────────────────────────────────
async def get_file_types():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT id, name, emoji, description FROM file_types WHERE is_active = 1")
        rows = await cur.fetchall()
        return [{"id": r[0], "name": r[1], "emoji": r[2], "description": r[3]} for r in rows]

async def add_file_type(type_id: str, name: str, emoji: str, description: str = ""):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO file_types (id, name, emoji, description)
            VALUES (?, ?, ?, ?)
        """, (type_id, name, emoji, description))
        await db.commit()

async def update_file_type_description(type_id: str, description: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE file_types SET description = ? WHERE id = ?", (description, type_id))
        await db.commit()

# ─── Pending Files ──────────────────────────────────────────────
async def set_pending_file(admin_id: int, data: dict):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM pending_files WHERE admin_id = ?", (admin_id,))
        await db.execute("""
            INSERT INTO pending_files (admin_id, file_id, file_name, file_type, caption, logo_file_id, step)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (admin_id, data.get("file_id",""), data.get("file_name",""), data.get("file_type","general"),
              data.get("caption",""), data.get("logo_file_id",""), data.get("step","type")))
        await db.commit()

async def get_pending_file(admin_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("""
            SELECT file_id, file_name, file_type, caption, logo_file_id, step
            FROM pending_files WHERE admin_id = ?
        """, (admin_id,))
        r = await cur.fetchone()
        if r:
            return {"file_id": r[0], "file_name": r[1], "file_type": r[2], "caption": r[3], "logo_file_id": r[4], "step": r[5]}
        return None

async def update_pending_file(admin_id: int, updates: dict):
    pending = await get_pending_file(admin_id)
    if pending:
        pending.update(updates)
        await set_pending_file(admin_id, pending)

async def clear_pending_file(admin_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM pending_files WHERE admin_id = ?", (admin_id,))
        await db.commit()

# ─── Stats ──────────────────────────────────────────────────────
async def get_stats():
    async with aiosqlite.connect(DB) as db:
        users = await db.execute("SELECT COUNT(*) FROM users")
        u = (await users.fetchone())[0]
        files = await db.execute("SELECT COUNT(*) FROM files WHERE is_active = 1")
        f = (await files.fetchone())[0]
        reactions = await db.execute("SELECT COUNT(*) FROM reactions")
        r = (await reactions.fetchone())[0]
        channels = await db.execute("SELECT COUNT(*) FROM channels WHERE is_active = 1")
        c = (await channels.fetchone())[0]
        admins = await db.execute("SELECT COUNT(*) FROM admins")
        a = (await admins.fetchone())[0]
        return {"users": u, "files": f, "reactions": r, "channels": c, "admins": a}
