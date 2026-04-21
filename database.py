import aiosqlite
import json
from config import DATABASE_URL, MAIN_ADMIN_ID, DEFAULT_FILE_TYPES, WELCOME_TEXT

DB = DATABASE_URL

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id          INTEGER PRIMARY KEY,
            username         TEXT    DEFAULT '',
            full_name        TEXT    DEFAULT '',
            added_by         INTEGER DEFAULT 0,
            is_main          INTEGER DEFAULT 0,
            allowed_channels TEXT    DEFAULT '[]',
            added_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS channels (
            channel_id       TEXT PRIMARY KEY,
            channel_name     TEXT,
            channel_username TEXT DEFAULT '',
            added_by         INTEGER,
            is_active        INTEGER DEFAULT 1,
            added_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS file_types (
            id          TEXT PRIMARY KEY,
            name        TEXT,
            emoji       TEXT,
            description TEXT DEFAULT '',
            is_active   INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS publish_groups (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT DEFAULT '',
            caption      TEXT DEFAULT '',
            logo_file_id TEXT DEFAULT '',
            published_by INTEGER,
            channel_id   TEXT DEFAULT '',
            is_active    INTEGER DEFAULT 1,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS files (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id        INTEGER DEFAULT 0,
            app_id          INTEGER DEFAULT 0,
            file_id         TEXT NOT NULL,
            file_type       TEXT DEFAULT 'general',
            file_name       TEXT DEFAULT '',
            file_caption    TEXT DEFAULT '',
            sort_order      INTEGER DEFAULT 0,
            channel_id      TEXT DEFAULT '',
            message_id      INTEGER DEFAULT 0,
            is_active       INTEGER DEFAULT 1,
            published_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reactions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            group_id   INTEGER,
            reacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, group_id)
        );

        CREATE TABLE IF NOT EXISTS deliveries (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            group_id     INTEGER,
            delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, group_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY,
            username  TEXT DEFAULT '',
            full_name TEXT DEFAULT '',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS pending (
            admin_id   INTEGER PRIMARY KEY,
            data       TEXT DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS force_sub (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id   TEXT NOT NULL,
            target_name TEXT DEFAULT '',
            target_type TEXT DEFAULT 'channel',
            target_link TEXT DEFAULT '',
            is_active   INTEGER DEFAULT 1,
            added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS apps (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            emoji      TEXT DEFAULT '📱',
            is_active  INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS banned_users (
            user_id   INTEGER PRIMARY KEY,
            username  TEXT DEFAULT '',
            full_name TEXT DEFAULT '',
            reason    TEXT DEFAULT '',
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vip_users (
            user_id    INTEGER PRIMARY KEY,
            username   TEXT DEFAULT '',
            full_name  TEXT DEFAULT '',
            expires_at TEXT DEFAULT '',
            added_by   INTEGER DEFAULT 0,
            added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id,full_name,is_main) VALUES (?,?,1)",
            (MAIN_ADMIN_ID, "Main Admin")
        )

        # Migration: add app_id column if missing
        try:
            await db.execute("ALTER TABLE files ADD COLUMN app_id INTEGER DEFAULT 0")
        except Exception:
            pass
        for ft in DEFAULT_FILE_TYPES:
            await db.execute(
                "INSERT OR IGNORE INTO file_types (id,name,emoji) VALUES (?,?,?)",
                (ft["id"], ft["name"], ft["emoji"])
            )
        defaults = {
            "welcome_message": WELCOME_TEXT,
            "bot_logo":        "",
            "bot_enabled":     "1",
            "vip_enabled":     "0",
            "vip_contact":     "@xtt1x",
            "button_color":    "default",
            "vip_message":     "💎 للحصول على VIP تواصل مع @xtt1x",
        }
        for k, v in defaults.items():
            await db.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))
        await db.commit()


# ── Settings ──────────────────────────────────────────────────────
async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
        r   = await cur.fetchone()
        return r[0] if r else default

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
        await db.commit()


# ── Admins ────────────────────────────────────────────────────────
async def is_admin(uid: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,))
        return await cur.fetchone() is not None

async def is_main_admin(uid: int) -> bool:
    return uid == MAIN_ADMIN_ID

async def get_admin(uid: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id,username,full_name,is_main,allowed_channels FROM admins WHERE user_id=?", (uid,))
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

async def add_admin(uid: int, username: str, full_name: str, added_by: int, channels=None):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admins (user_id,username,full_name,added_by,allowed_channels) VALUES (?,?,?,?,?)",
            (uid, username, full_name, added_by, json.dumps(channels or [])))
        await db.commit()

async def remove_admin(uid: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM admins WHERE user_id=? AND is_main=0", (uid,))
        await db.commit()


# ── Channels ──────────────────────────────────────────────────────
async def get_all_channels():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT channel_id,channel_name,channel_username,is_active FROM channels")
        rows = await cur.fetchall()
        return [{"channel_id": r[0], "name": r[1], "username": r[2], "is_active": r[3]} for r in rows]

async def get_channel(cid: str):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT channel_id,channel_name,channel_username FROM channels WHERE channel_id=?", (cid,))
        r = await cur.fetchone()
        return {"channel_id": r[0], "name": r[1], "username": r[2]} if r else None

async def add_channel(cid: str, name: str, username: str, added_by: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO channels (channel_id,channel_name,channel_username,added_by) VALUES (?,?,?,?)",
            (cid, name, username, added_by))
        await db.commit()

async def remove_channel(cid: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM channels WHERE channel_id=?", (cid,))
        await db.commit()


# ── File types ────────────────────────────────────────────────────
async def get_file_types():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT id,name,emoji,description FROM file_types WHERE is_active=1")
        rows = await cur.fetchall()
        return [{"id": r[0], "name": r[1], "emoji": r[2], "description": r[3]} for r in rows]

async def add_file_type(tid: str, name: str, emoji: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO file_types (id,name,emoji) VALUES (?,?,?)", (tid, name, emoji))
        await db.commit()

async def set_filetype_desc(tid: str, desc: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE file_types SET description=? WHERE id=?", (desc, tid))
        await db.commit()


# ── Publish groups (one group = one publish action, many files) ───
async def create_group(title: str, caption: str, logo: str, published_by: int, channel_id: str) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "INSERT INTO publish_groups (title,caption,logo_file_id,published_by,channel_id) VALUES (?,?,?,?,?)",
            (title, caption, logo, published_by, channel_id))
        await db.commit()
        return cur.lastrowid

async def get_group(gid: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT id,title,caption,logo_file_id,channel_id FROM publish_groups WHERE id=? AND is_active=1", (gid,))
        r = await cur.fetchone()
        if r:
            return {"id": r[0], "title": r[1], "caption": r[2], "logo_file_id": r[3], "channel_id": r[4]}
        return None

async def get_latest_group():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT id,title,caption,logo_file_id,channel_id FROM publish_groups WHERE is_active=1 ORDER BY published_at DESC LIMIT 1")
        r = await cur.fetchone()
        if r:
            return {"id": r[0], "title": r[1], "caption": r[2], "logo_file_id": r[3], "channel_id": r[4]}
        return None

async def update_group_message(gid: int, message_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE publish_groups SET channel_id=channel_id WHERE id=?", (gid,))
        await db.commit()


# ── Files in a group ──────────────────────────────────────────────
async def add_file_to_group(group_id: int, file_id: str, file_type: str,
                             file_name: str, file_caption: str, sort_order: int,
                             channel_id: str = "", message_id: int = 0,
                             app_id: int = 0) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """INSERT INTO files
               (group_id,app_id,file_id,file_type,file_name,file_caption,sort_order,channel_id,message_id)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (group_id, app_id, file_id, file_type, file_name, file_caption, sort_order, channel_id, message_id))
        await db.commit()
        return cur.lastrowid

async def get_files_in_group(group_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """SELECT id,file_id,file_type,file_name,file_caption,sort_order
               FROM files WHERE group_id=? AND is_active=1 ORDER BY sort_order""",
            (group_id,))
        rows = await cur.fetchall()
        return [{"id": r[0], "file_id": r[1], "file_type": r[2],
                 "file_name": r[3], "file_caption": r[4], "sort_order": r[5]} for r in rows]

async def get_latest_files_by_type(file_type: str):
    """Get files from the most recent group that has this file_type"""
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """SELECT f.id,f.file_id,f.file_type,f.file_name,f.file_caption,f.sort_order,
                      pg.id as gid, pg.logo_file_id, pg.caption as group_caption, pg.title
               FROM files f
               JOIN publish_groups pg ON f.group_id = pg.id
               WHERE f.file_type=? AND f.is_active=1 AND pg.is_active=1
               ORDER BY f.published_at DESC LIMIT 10""",
            (file_type,))
        rows = await cur.fetchall()
        return [{"id": r[0], "file_id": r[1], "file_type": r[2], "file_name": r[3],
                 "file_caption": r[4], "sort_order": r[5], "group_id": r[6],
                 "logo_file_id": r[7], "group_caption": r[8], "title": r[9]} for r in rows]


# ── Reactions ─────────────────────────────────────────────────────
async def add_reaction(uid: int, group_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        try:
            await db.execute(
                "INSERT INTO reactions (user_id,group_id) VALUES (?,?)", (uid, group_id))
            await db.commit()
            return True
        except Exception:
            return False

async def has_reacted(uid: int, group_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT 1 FROM reactions WHERE user_id=? AND group_id=?", (uid, group_id))
        return await cur.fetchone() is not None

async def reaction_count(group_id: int) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM reactions WHERE group_id=?", (group_id,))
        r = await cur.fetchone()
        return r[0] if r else 0


# ── Deliveries ────────────────────────────────────────────────────
async def add_delivery(uid: int, group_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        try:
            await db.execute(
                "INSERT INTO deliveries (user_id,group_id) VALUES (?,?)", (uid, group_id))
            await db.commit()
            return True
        except Exception:
            return False

async def delivery_count(group_id: int) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM deliveries WHERE group_id=?", (group_id,))
        r = await cur.fetchone()
        return r[0] if r else 0


# ── Users ─────────────────────────────────────────────────────────
async def register_user(uid: int, username: str, full_name: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id,username,full_name,last_seen) VALUES (?,?,?,CURRENT_TIMESTAMP)",
            (uid, username, full_name))
        await db.commit()

async def get_all_user_ids():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT user_id FROM users")
        return [r[0] for r in await cur.fetchall()]

async def user_count() -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        r = await cur.fetchone()
        return r[0] if r else 0


# ── Force subscribe ───────────────────────────────────────────────
async def get_force_subs():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT id,target_id,target_name,target_type,target_link FROM force_sub WHERE is_active=1")
        rows = await cur.fetchall()
        return [{"id": r[0], "target_id": r[1], "target_name": r[2],
                 "target_type": r[3], "target_link": r[4]} for r in rows]

async def add_force_sub(target_id: str, target_name: str, target_type: str, target_link: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO force_sub (target_id,target_name,target_type,target_link) VALUES (?,?,?,?)",
            (target_id, target_name, target_type, target_link))
        await db.commit()

async def remove_force_sub(sub_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM force_sub WHERE id=?", (sub_id,))
        await db.commit()


# ── Pending (wizard state) ────────────────────────────────────────
async def set_pending(admin_id: int, data: dict):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO pending (admin_id,data,updated_at) VALUES (?,?,CURRENT_TIMESTAMP)",
            (admin_id, json.dumps(data)))
        await db.commit()

async def get_pending(admin_id: int) -> dict:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT data FROM pending WHERE admin_id=?", (admin_id,))
        r   = await cur.fetchone()
        return json.loads(r[0]) if r else {}

async def update_pending(admin_id: int, updates: dict):
    d = await get_pending(admin_id)
    d.update(updates)
    await set_pending(admin_id, d)

async def clear_pending(admin_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM pending WHERE admin_id=?", (admin_id,))
        await db.commit()


# ── Stats ─────────────────────────────────────────────────────────
async def get_stats() -> dict:
    async with aiosqlite.connect(DB) as db:
        u  = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        f  = (await (await db.execute("SELECT COUNT(*) FROM files WHERE is_active=1")).fetchone())[0]
        g  = (await (await db.execute("SELECT COUNT(*) FROM publish_groups WHERE is_active=1")).fetchone())[0]
        rc = (await (await db.execute("SELECT COUNT(*) FROM reactions")).fetchone())[0]
        dc = (await (await db.execute("SELECT COUNT(*) FROM deliveries")).fetchone())[0]
        ch = (await (await db.execute("SELECT COUNT(*) FROM channels WHERE is_active=1")).fetchone())[0]
        ad = (await (await db.execute("SELECT COUNT(*) FROM admins")).fetchone())[0]
        fs = (await (await db.execute("SELECT COUNT(*) FROM force_sub WHERE is_active=1")).fetchone())[0]
        ap = (await (await db.execute("SELECT COUNT(*) FROM apps WHERE is_active=1")).fetchone())[0]
        bn = (await (await db.execute("SELECT COUNT(*) FROM banned_users")).fetchone())[0]
        vp = (await (await db.execute("SELECT COUNT(*) FROM vip_users")).fetchone())[0]
        return {"users": u, "files": f, "groups": g, "reactions": rc,
                "deliveries": dc, "channels": ch, "admins": ad, "force_subs": fs,
                "apps": ap, "banned": bn, "vip": vp}


# ── Apps ──────────────────────────────────────────────────────────
async def get_all_apps():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT id,name,emoji FROM apps WHERE is_active=1 ORDER BY sort_order,id")
        rows = await cur.fetchall()
        return [{"id": r[0], "name": r[1], "emoji": r[2]} for r in rows]

async def add_app(name: str, emoji: str) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "INSERT INTO apps (name,emoji) VALUES (?,?)", (name, emoji))
        await db.commit()
        return cur.lastrowid

async def remove_app(app_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE apps SET is_active=0 WHERE id=?", (app_id,))
        await db.commit()

async def get_app(app_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT id,name,emoji FROM apps WHERE id=?", (app_id,))
        r = await cur.fetchone()
        return {"id": r[0], "name": r[1], "emoji": r[2]} if r else None

async def get_apps_in_group(group_id: int):
    """Return distinct app names/emojis used in a publish group"""
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """SELECT DISTINCT f.app_id, a.name, a.emoji
               FROM files f JOIN apps a ON f.app_id=a.id
               WHERE f.group_id=? AND f.is_active=1""",
            (group_id,))
        rows = await cur.fetchall()
        return [{"id": r[0], "name": r[1], "emoji": r[2]} for r in rows]

async def get_files_by_app_and_type(group_id: int, app_id: int, file_type: str):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """SELECT id,file_id,file_type,file_name,file_caption,sort_order
               FROM files WHERE group_id=? AND app_id=? AND file_type=? AND is_active=1
               ORDER BY sort_order""",
            (group_id, app_id, file_type))
        rows = await cur.fetchall()
        return [{"id": r[0], "file_id": r[1], "file_type": r[2],
                 "file_name": r[3], "file_caption": r[4], "sort_order": r[5]} for r in rows]

async def get_filetypes_in_app(group_id: int, app_id: int):
    """Return distinct file types inside an app within a group"""
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            """SELECT DISTINCT f.file_type, ft.name, ft.emoji
               FROM files f
               JOIN file_types ft ON f.file_type=ft.id
               WHERE f.group_id=? AND f.app_id=? AND f.is_active=1""",
            (group_id, app_id))
        rows = await cur.fetchall()
        return [{"id": r[0], "name": r[1], "emoji": r[2]} for r in rows]

async def deactivate_old_groups():
    """Mark all previous groups as inactive (clear old files) on new publish"""
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE publish_groups SET is_active=0")
        await db.execute("UPDATE files SET is_active=0")
        await db.commit()


# ── Banned users ──────────────────────────────────────────────────
async def ban_user(user_id: int, username: str, full_name: str, reason: str = ""):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO banned_users (user_id,username,full_name,reason) VALUES (?,?,?,?)",
            (user_id, username, full_name, reason))
        await db.commit()

async def unban_user(user_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM banned_users WHERE user_id=?", (user_id,))
        await db.commit()

async def unban_all():
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM banned_users")
        await db.commit()

async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT 1 FROM banned_users WHERE user_id=?", (user_id,))
        return await cur.fetchone() is not None

async def get_all_banned():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id,username,full_name,reason FROM banned_users ORDER BY banned_at DESC")
        rows = await cur.fetchall()
        return [{"user_id": r[0], "username": r[1], "full_name": r[2], "reason": r[3]} for r in rows]


# ── VIP users ─────────────────────────────────────────────────────
async def add_vip(user_id: int, username: str, full_name: str, expires_at: str, added_by: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO vip_users (user_id,username,full_name,expires_at,added_by) VALUES (?,?,?,?,?)",
            (user_id, username, full_name, expires_at, added_by))
        await db.commit()

async def remove_vip(user_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM vip_users WHERE user_id=?", (user_id,))
        await db.commit()

async def remove_all_vip():
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM vip_users")
        await db.commit()

async def is_vip(user_id: int) -> bool:
    from datetime import datetime
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT expires_at FROM vip_users WHERE user_id=?", (user_id,))
        r = await cur.fetchone()
        if not r:
            return False
        if r[0] == "permanent":
            return True
        try:
            exp = datetime.fromisoformat(r[0])
            return datetime.now() < exp
        except Exception:
            return True

async def get_all_vip():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id,username,full_name,expires_at FROM vip_users ORDER BY added_at DESC")
        rows = await cur.fetchall()
        return [{"user_id": r[0], "username": r[1], "full_name": r[2], "expires_at": r[3]} for r in rows]

async def get_all_users_list():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id,username,full_name FROM users ORDER BY joined_at DESC LIMIT 200")
        rows = await cur.fetchall()
        return [{"user_id": r[0], "username": r[1], "full_name": r[2]} for r in rows]
