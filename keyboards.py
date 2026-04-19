from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ── Channel post buttons ──────────────────────────────────────────
def channel_post_buttons(group_id: int, rc: int, dc: int, bot_username: str) -> InlineKeyboardMarkup:
    """
    Row 1: ⚡ فعّل البوت أولاً  (full width, no arrow)
    Row 2: ❤️ تفاعل (X)  |  📥 استلام (X)
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "⚡️ فعّل البوت أولاً 🤖",
            url=f"https://t.me/{bot_username}?start=activate"
        )],
        [
            InlineKeyboardButton(f"❤️ تفاعل ({rc})",   callback_data=f"react_{group_id}"),
            InlineKeyboardButton(f"📥 استلام ({dc})",  callback_data=f"getfile_{group_id}"),
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
            InlineKeyboardButton("🔒 اشتراك إجباري",   callback_data="adm_forcesub"),
            InlineKeyboardButton("⚙️ الإعدادات",        callback_data="adm_settings"),
        ],
        [
            InlineKeyboardButton("📊 إحصائيات",         callback_data="adm_stats"),
            InlineKeyboardButton(toggle,                callback_data="adm_toggle"),
        ],
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
def filetypes_menu(fts: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{ft['emoji']} {ft['name']}", callback_data=f"editft_{ft['id']}"
    )] for ft in fts]
    rows.append([InlineKeyboardButton("➕ إضافة نوع", callback_data="adm_addft")])
    rows.append([InlineKeyboardButton("🔙 رجوع",      callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


# ── Settings ──────────────────────────────────────────────────────
def settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ رسالة الترحيب",  callback_data="adm_set_welcome")],
        [InlineKeyboardButton("🖼 شعار افتراضي",   callback_data="adm_set_logo")],
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
