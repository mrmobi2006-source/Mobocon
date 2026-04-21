from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ── Channel post buttons ──────────────────────────────────────────
def channel_post_buttons(group_id: int, rc: int, dc: int, bot_username: str) -> InlineKeyboardMarkup:
    """
    Row 1: ⚡ فعّل البوت أولاً  — URL يفتح البوت
    Row 2: ❤️ تفاعل (callback)  |  📥 استلام (URL مباشر للبوت)
    زر استلام URL = ينقل المستخدم مباشرة للبوت ويعرض قائمة الملفات
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "⚡️ فعّل البوت أولاً 🤖",
            url=f"https://t.me/{bot_username}?start=activate"
        )],
        [
            InlineKeyboardButton(
                f"❤️ تفاعل ({rc})",
                callback_data=f"react_{group_id}"
            ),
            InlineKeyboardButton(
                f"📥 استلام ({dc}) ↗️",
                url=f"https://t.me/{bot_username}?start=getfile_{group_id}"
            ),
        ],
    ])


# ── Admin main menu ───────────────────────────────────────────────
def admin_main_menu(is_main: bool, enabled: bool) -> InlineKeyboardMarkup:
    toggle = "🔴 إيقاف البوت" if enabled else "🟢 تشغيل البوت"
    rows = [
        [InlineKeyboardButton("📤 نشر ملفات جديدة",   callback_data="adm_publish")],
        [
            InlineKeyboardButton("📢 القنوات",          callback_data="adm_channels"),
            InlineKeyboardButton("📁 أنواع الملفات",    callback_data="adm_filetypes"),
        ],
        [
            InlineKeyboardButton("📱 التطبيقات",        callback_data="adm_apps"),
            InlineKeyboardButton("🔒 اشتراك إجباري",   callback_data="adm_forcesub"),
        ],
        [
            InlineKeyboardButton("🚫 الحظر",            callback_data="adm_bans"),
            InlineKeyboardButton("💎 VIP",              callback_data="adm_vip"),
        ],
        [
            InlineKeyboardButton("⚙️ الإعدادات",        callback_data="adm_settings"),
            InlineKeyboardButton("📊 إحصائيات",         callback_data="adm_stats"),
        ],
        [InlineKeyboardButton(toggle,                   callback_data="adm_toggle")],
    ]
    if is_main:
        rows.append([InlineKeyboardButton("👤 المشرفون",     callback_data="adm_admins")])
        rows.append([InlineKeyboardButton("📣 بث رسالة",    callback_data="adm_broadcast")])
    return InlineKeyboardMarkup(rows)


def back_btn(target: str = "adm_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=target)]])


def cancel_btn() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="adm_cancel")]])


def back_cancel(back: str = "adm_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 رجوع", callback_data=back),
        InlineKeyboardButton("❌ إلغاء", callback_data="adm_cancel"),
    ]])


# ── Publish wizard ────────────────────────────────────────────────
def publish_type_menu(file_types: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{ft['emoji']} {ft['name']}", callback_data=f"pub_addfile_{ft['id']}"
    )] for ft in file_types]
    rows.append([InlineKeyboardButton("✅ انتهيت من الملفات", callback_data="pub_done_files")])
    rows.append([InlineKeyboardButton("❌ إلغاء",             callback_data="adm_cancel")])
    return InlineKeyboardMarkup(rows)


def publish_app_filetype_menu(file_types: list, app_id: int) -> InlineKeyboardMarkup:
    """After picking app, pick file type"""
    rows = [[InlineKeyboardButton(
        f"{ft['emoji']} {ft['name']}", callback_data=f"pub_appft_{app_id}_{ft['id']}"
    )] for ft in file_types]
    rows.append([InlineKeyboardButton("✅ انتهيت من الملفات", callback_data="pub_done_files")])
    rows.append([InlineKeyboardButton("❌ إلغاء",             callback_data="adm_cancel")])
    return InlineKeyboardMarkup(rows)


def publish_logo_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ بدون شعار",  callback_data="pub_skiplogo")],
        [InlineKeyboardButton("❌ إلغاء",      callback_data="adm_cancel")],
    ])


def publish_channel_menu(channels: list, is_main: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"📢 {ch['name']}", callback_data=f"pub_ch_{ch['channel_id']}"
    )] for ch in channels]
    if is_main:
        rows.append([InlineKeyboardButton("📢 كل القنوات", callback_data="pub_ch_ALL")])
    rows.append([InlineKeyboardButton("❌ إلغاء", callback_data="adm_cancel")])
    return InlineKeyboardMarkup(rows)


def publish_confirm_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ نشر الآن",  callback_data="pub_confirm")],
        [InlineKeyboardButton("❌ إلغاء",     callback_data="adm_cancel")],
    ])


# ── Channel management ────────────────────────────────────────────
def channels_menu(channels: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"🗑 {ch['name']}", callback_data=f"delch_{ch['channel_id']}"
    )] for ch in channels]
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


# ── File types management ─────────────────────────────────────────
# ── File types management (kept for backward compat — calls new one) ─
def filetypes_menu(fts: list) -> InlineKeyboardMarkup:
    return filetypes_manage_menu(fts)


# ── Settings ──────────────────────────────────────────────────────
def settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ رسالة الترحيب",  callback_data="adm_set_welcome")],
        [InlineKeyboardButton("🖼 شعار افتراضي",   callback_data="adm_set_logo")],
        [InlineKeyboardButton("🎨 ألوان الأزرار",  callback_data="adm_colors")],
        [InlineKeyboardButton("🔙 رجوع",           callback_data="adm_main")],
    ])


# ── Admins ────────────────────────────────────────────────────────
def admins_menu(admins: list) -> InlineKeyboardMarkup:
    rows = []
    for adm in admins:
        if not adm["is_main"]:
            rows.append([InlineKeyboardButton(
                f"🗑 {adm['full_name']}", callback_data=f"deladmin_{adm['user_id']}"
            )])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


# ── Force sub ─────────────────────────────────────────────────────
def forcesub_menu(subs: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"🗑 {s['target_name']}", callback_data=f"delsub_{s['id']}"
    )] for s in subs]
    rows.append([InlineKeyboardButton("➕ إضافة اشتراك إجباري", callback_data="adm_addsub")])
    rows.append([InlineKeyboardButton("🔙 رجوع",                callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


def force_sub_user_buttons(subs: list) -> InlineKeyboardMarkup:
    """Buttons shown to user when force-sub check fails"""
    rows = []
    for s in subs:
        label = f"{'📢' if s['target_type']=='channel' else '🤖'} اشترك في {s['target_name']}"
        rows.append([InlineKeyboardButton(label, url=s["target_link"])])
    rows.append([InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub")])
    return InlineKeyboardMarkup(rows)


# ── User file selection (inside bot after clicking receive) ───────
def user_filetype_menu(file_types: list, group_id: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{ft['emoji']} {ft['name']}", callback_data=f"userget_{group_id}_{ft['id']}"
    )] for ft in file_types]
    return InlineKeyboardMarkup(rows)


# ── New: App selector for user ────────────────────────────────────
def user_app_menu(apps: list, group_id: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{a['emoji']} {a['name']}", callback_data=f"uapp_{group_id}_{a['id']}"
    )] for a in apps]
    return InlineKeyboardMarkup(rows)


def user_app_filetype_menu(fts: list, group_id: int, app_id: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{ft['emoji']} {ft['name']}", callback_data=f"uappft_{group_id}_{app_id}_{ft['id']}"
    )] for ft in fts]
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"userget_{group_id}_back")])
    return InlineKeyboardMarkup(rows)


# ── Apps management ───────────────────────────────────────────────
def apps_manage_menu(apps: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"🗑 {a['emoji']} {a['name']}", callback_data=f"delapp_{a['id']}"
    )] for a in apps]
    rows.append([InlineKeyboardButton("➕ إضافة تطبيق", callback_data="adm_addapp")])
    rows.append([InlineKeyboardButton("🔙 رجوع",         callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


def publish_app_menu(apps: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{a['emoji']} {a['name']}", callback_data=f"pub_app_{a['id']}"
    )] for a in apps]
    rows.append([InlineKeyboardButton("❌ إلغاء", callback_data="adm_cancel")])
    return InlineKeyboardMarkup(rows)


# ── File types management (with delete) ───────────────────────────
def filetypes_manage_menu(fts: list) -> InlineKeyboardMarkup:
    rows = []
    for ft in fts:
        rows.append([
            InlineKeyboardButton(f"{ft['emoji']} {ft['name']}", callback_data=f"editft_{ft['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"delft_{ft['id']}"),
        ])
    rows.append([InlineKeyboardButton("➕ إضافة نوع", callback_data="adm_addft")])
    rows.append([InlineKeyboardButton("🔙 رجوع",      callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


# ── Ban management ────────────────────────────────────────────────
def ban_menu(banned: list) -> InlineKeyboardMarkup:
    rows = []
    for u in banned[:20]:  # max 20 shown
        name = u["full_name"] or u["username"] or str(u["user_id"])
        rows.append([InlineKeyboardButton(
            f"✅ رفع حظر {name[:20]}", callback_data=f"unban_{u['user_id']}"
        )])
    rows.append([InlineKeyboardButton("✅ رفع الحظر عن الجميع", callback_data="unban_all")])
    rows.append([InlineKeyboardButton("➕ حظر مستخدم",          callback_data="adm_ban_pick")])
    rows.append([InlineKeyboardButton("🔙 رجوع",                callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


def users_pick_menu(users: list, action: str, page: int = 0) -> InlineKeyboardMarkup:
    """Generic paginated user picker. action = 'ban' or 'vip'"""
    per_page = 10
    start    = page * per_page
    chunk    = users[start:start + per_page]
    rows     = []
    for u in chunk:
        name = u.get("full_name") or u.get("username") or str(u["user_id"])
        rows.append([InlineKeyboardButton(
            f"👤 {name[:25]} ({u['user_id']})",
            callback_data=f"pick_{action}_{u['user_id']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"page_{action}_{page-1}"))
    if start + per_page < len(users):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"page_{action}_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


# ── VIP management ────────────────────────────────────────────────
def vip_menu(vip_users: list, vip_enabled: bool) -> InlineKeyboardMarkup:
    toggle = "🔴 إيقاف نظام VIP" if vip_enabled else "🟢 تفعيل نظام VIP"
    rows   = []
    for u in vip_users[:15]:
        name = u["full_name"] or u["username"] or str(u["user_id"])
        exp  = u["expires_at"] or "دائم"
        rows.append([InlineKeyboardButton(
            f"💎 {name[:18]} — {exp[:10]}", callback_data=f"rmvip_{u['user_id']}"
        )])
    rows.append([InlineKeyboardButton("➕ إضافة VIP",           callback_data="adm_addvip")])
    rows.append([InlineKeyboardButton("🗑 إزالة كل VIP",        callback_data="rmvip_all")])
    rows.append([InlineKeyboardButton(toggle,                   callback_data="adm_toggle_vip")])
    rows.append([InlineKeyboardButton("✏️ رسالة VIP",           callback_data="adm_set_vipmsg")])
    rows.append([InlineKeyboardButton("🔙 رجوع",                callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


# ── Button color picker ───────────────────────────────────────────
def color_menu() -> InlineKeyboardMarkup:
    """
    Telegram doesn't support custom button colors via API directly.
    We store a 'theme' that changes button text emoji/style.
    """
    themes = [
        ("🔵 أزرق",   "blue"),
        ("🔴 أحمر",   "red"),
        ("🟢 أخضر",   "green"),
        ("🟡 ذهبي",   "gold"),
        ("⚪ أبيض",   "white"),
        ("🟣 بنفسجي", "purple"),
    ]
    rows = [[InlineKeyboardButton(label, callback_data=f"setcolor_{val}")]
            for label, val in themes]
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="adm_settings")])
    return InlineKeyboardMarkup(rows)
