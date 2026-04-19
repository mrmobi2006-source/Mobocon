import aiosqlite
import json
from config import DATABASE_URL, MAIN_ADMIN_ID, DEFAULT_FILE_TYPES, DEFAULT_WELCOME, BOT_NAME

DB = DATABASE_URL

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id      INTEGER PRIMARY KEY,
            username     TEXT    DEFAULT '',
            full_name    TEXT    DEFAULT '',
            added_by     INTEGER DEFAULT 0,
            is_main      INTEGER DEFAULT 0,
            allowed_channels TEXT DEFAULT '[]',
            added_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS channels (
            channel_id   TEXT PRIMARY KEY,
            channel_name TEXT,
            channel_username TEXT DEFAULT '',
            added_by     INTEGER,
            is_active    INTEGER DEFAULT 1,
            added_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS file_types (
            id          TEXT PRIMARY KEY,
            name        TEXT,
            emoji       TEXT,
            description TEXT DEFAULT '',
            is_active   INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS files (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id      TEXT NOT NULL,
            file_type    TEXT DEFAULT 'general',
            file_name    TEXT DEFAULT '',
            caption      TEXT DEFAULT '',
            logo_file_id TEXT DEFAULT '',
            published_by INTEGER,
            channel_id   TEXT DEFAULT '',
            message_id   INTEGER DEFAULT 0,
            is_active    INTEGER DEFAULT 1,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reactions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            file_id    INTEGER,
            reacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, file_id)
        );

        CREATE TABLE IF NOT EXISTS deliveries (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            file_id      INTEGER,
            delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, file_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY,
            username   TEXT DEFAULT '',
            full_name  TEXT DEFAULT '',
            joined_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS pending (
            admin_id     INTEGER PRIMARY KEY,
            data         TEXT DEFAULT '{}',
            updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Main admin
        await db.execute("""
            INSERT OR IGNORE INTO admins (user_id, full_name, is_main)
            VALUES (?, 'Main Admin', 1)
        """, (MAIN_ADMIN_ID,))

        # Default file types
        for ft in DEFAULT_FILE_TYPES:
            await db.execute("""
                INSERT OR IGNORE INTO file_types (id, name, emoji)
                VALUES (?, ?, ?)
            """, (ft["id"], ft["name"], ft["emoji"]))

        # Default settings
        defaults = {
            "welcome_message": DEFAULT_WELCOME,
            "bot_logo": "",
            "bot_enabled": "1",
            "broadcast_photo": "",
        }
        for k, v in defaults.items():
            await db.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))

        await db.commit()

# ── Settings ──────────────────────────────────────────────────────
async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
        r = await cur.fetchone()
        return r[0] if r else default

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
        await db.commit()

# ── Admins ────────────────────────────────────────────────────────
async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
        return await cur.fetchone() is not None

async def is_main_admin(user_id: int) -> bool:
    return user_id == MAIN_ADMIN_ID

async def get_admin(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id,username,full_name,is_main,allowed_channels FROM admins WHERE user_id=?",
            (user_id,))
        r = await cur.fetchone()
        if r:
            return {"user_id": r[0], "username": r[1], "full_name": r[2],
                    "is_main": r[3], "allowed_channels": json.loads(r[4] or "[]")}
        return None

async def get_all_admins():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id,username,full_name,is_main,allowed_channels FROM admins")
        rows = await cur.fetchall()
        return [{"user_id": r[0], "username": r[1], "full_name": r[2],
                 "is_main": r[3], "allowed_channels": json.loads(r[4] or "[]")} for r in rows]

async def add_admin(user_id: int, username: str, full_name: str, added_by: int, channels=None):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO admins (user_id,username,full_name,added_by,allowed_channels)
            VALUES (?,?,?,?,?)
        """, (user_id, username, full_name, added_by, json.dumps(channels or [])))
        await db.commit()

async def remove_admin(user_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM admins WHERE user_id=? AND is_main=0", (user_id,))
        await db.commit()

# ── Channels ──────────────────────────────────────────────────────
async def get_all_channels():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT channel_id,channel_name,channel_username,is_active FROM channels")
        rows = await cur.fetchall()
        return [{"channel_id": r[0], "name": r[1], "username": r[2], "is_active": r[3]} for r in rows]

async def get_channel(channel_id: str):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT channel_id,channel_name,channel_username FROM channels WHERE channel_id=?",
            (channel_id,))
        r = await cur.fetchone()
        return {"channel_id": r[0], "name": r[1], "username": r[2]} if r else None

async def add_channel(channel_id: str, name: str, username: str, added_by: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO channels (channel_id,channel_name,channel_username,added_by)
            VALUES (?,?,?,?)
        """, (channel_id, name, username, added_by))
        await db.commit()

async def remove_channel(channel_id: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
        await db.commit()

# ── File Types ────────────────────────────────────────────────────
async def get_file_types():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT id,name,emoji,description FROM file_types WHERE is_active=1")
        rows = await cur.fetchall()
        return [{"id": r[0], "name": r[1], "emoji": r[2], "description": r[3]} for r in rows]

async def add_file_type(type_id: str, name: str, emoji: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO file_types (id,name,emoji)
            VALUES (?,?,?)
        """, (type_id, name, emoji))
        await db.commit()

async def set_filetype_desc(type_id: str, desc: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE file_types SET description=? WHERE id=?", (desc, type_id))
        await db.commit()

# ── Files ─────────────────────────────────────────────────────────
async def save_file(file_id, file_type, file_name, caption, logo_file_id,
                    published_by, channel_id, message_id) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("""
            INSERT INTO files
              (file_id,file_type,file_name,caption,logo_file_id,published_by,channel_id,message_id)
            VALUES (?,?,?,?,?,?,?,?)
        """, (file_id, file_type, file_name, caption, logo_file_id,
              published_by, channel_id, message_id))
        await db.commit()
        return cur.lastrowid

async def get_latest_file(file_type: str = None):
    async with aiosqlite.connect(DB) as db:
        if file_type:
            cur = await db.execute("""
                SELECT id,file_id,file_type,file_name,caption,logo_file_id,channel_id,message_id
                FROM files WHERE file_type=? AND is_active=1
                ORDER BY published_at DESC LIMIT 1
            """, (file_type,))
        else:
            cur = await db.execute("""
                SELECT id,file_id,file_type,file_name,caption,logo_file_id,channel_id,message_id
                FROM files WHERE is_active=1
                ORDER BY published_at DESC LIMIT 1
            """)
        r = await cur.fetchone()
        if r:
            return {"id": r[0], "file_id": r[1], "file_type": r[2], "file_name": r[3],
                    "caption": r[4], "logo_file_id": r[5], "channel_id": r[6], "message_id": r[7]}
        return None

async def get_file_by_id(fid: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("""
            SELECT id,file_id,file_type,file_name,caption,logo_file_id,channel_id,message_id
            FROM files WHERE id=? AND is_active=1
        """, (fid,))
        r = await cur.fetchone()
        if r:
            return {"id": r[0], "file_id": r[1], "file_type": r[2], "file_name": r[3],
                    "caption": r[4], "logo_file_id": r[5], "channel_id": r[6], "message_id": r[7]}
        return None

# ── Reactions ─────────────────────────────────────────────────────
async def add_reaction(user_id: int, file_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        try:
            await db.execute(
                "INSERT INTO reactions (user_id,file_id) VALUES (?,?)", (user_id, file_id))
            await db.commit()
            return True
        except:
            return False

async def has_reacted(user_id: int, file_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT 1 FROM reactions WHERE user_id=? AND file_id=?", (user_id, file_id))
        return await cur.fetchone() is not None

async def reaction_count(file_id: int) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM reactions WHERE file_id=?", (file_id,))
        r = await cur.fetchone()
        return r[0] if r else 0

# ── Deliveries ────────────────────────────────────────────────────
async def add_delivery(user_id: int, file_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        try:
            await db.execute(
                "INSERT INTO deliveries (user_id,file_id) VALUES (?,?)", (user_id, file_id))
            await db.commit()
            return True
        except:
            return False

async def delivery_count(file_id: int) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM deliveries WHERE file_id=?", (file_id,))
        r = await cur.fetchone()
        return r[0] if r else 0

# ── Users ─────────────────────────────────────────────────────────
async def register_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id,username,full_name,last_seen)
            VALUES (?,?,?,CURRENT_TIMESTAMP)
        """, (user_id, username, full_name))
        await db.commit()

async def get_all_user_ids():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT user_id FROM users")
        return [r[0] for r in await cur.fetchall()]

# ── Pending ───────────────────────────────────────────────────────
async def set_pending(admin_id: int, data: dict):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO pending (admin_id, data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (admin_id, json.dumps(data)))
        await db.commit()

async def get_pending(admin_id: int) -> dict:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT data FROM pending WHERE admin_id=?", (admin_id,))
        r = await cur.fetchone()
        return json.loads(r[0]) if r else {}

async def clear_pending(admin_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM pending WHERE admin_id=?", (admin_id,))
        await db.commit()

async def update_pending(admin_id: int, updates: dict):
    d = await get_pending(admin_id)
    d.update(updates)
    await set_pending(admin_id, d)

# ── Stats ─────────────────────────────────────────────────────────
async def get_stats() -> dict:
    async with aiosqlite.connect(DB) as db:
        u  = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        f  = (await (await db.execute("SELECT COUNT(*) FROM files WHERE is_active=1")).fetchone())[0]
        rc = (await (await db.execute("SELECT COUNT(*) FROM reactions")).fetchone())[0]
        dc = (await (await db.execute("SELECT COUNT(*) FROM deliveries")).fetchone())[0]
        ch = (await (await db.execute("SELECT COUNT(*) FROM channels WHERE is_active=1")).fetchone())[0]
        ad = (await (await db.execute("SELECT COUNT(*) FROM admins")).fetchone())[0]
        return {"users": u, "files": f, "reactions": rc, "deliveries": dc,
                "channels": ch, "admins": ad}
