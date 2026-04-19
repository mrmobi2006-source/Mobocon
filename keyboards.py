from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def channel_post_buttons(file_db_id: int, reaction_count: int,
                         delivery_count: int, bot_username: str) -> InlineKeyboardMarkup:
    """
    3-button layout for channel posts — NO arrows, clean look.
    Row 1: big activate button (full width)
    Row 2: react  |  get file
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "⚡️ فعّل البوت أولاً",
            url=f"https://t.me/{bot_username}?start=activate"
        )],
        [
            InlineKeyboardButton(
                f"❤️ تفاعل  {reaction_count}",
                callback_data=f"react_{file_db_id}"
            ),
            InlineKeyboardButton(
                f"📥 استلام  {delivery_count}",
                callback_data=f"getfile_{file_db_id}"
            ),
        ],
    ])


def admin_main_menu(is_main: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📤 نشر ملف", callback_data="adm_publish")],
        [
            InlineKeyboardButton("📢 القنوات",    callback_data="adm_channels"),
            InlineKeyboardButton("📁 أنواع الملفات", callback_data="adm_filetypes"),
        ],
        [
            InlineKeyboardButton("⚙️ الإعدادات", callback_data="adm_settings"),
            InlineKeyboardButton("📊 إحصائيات",  callback_data="adm_stats"),
        ],
    ]
    if is_main:
        rows.append([InlineKeyboardButton("👤 المشرفون", callback_data="adm_admins")])
        rows.append([InlineKeyboardButton("📣 بث رسالة", callback_data="adm_broadcast")])
    return InlineKeyboardMarkup(rows)


def back_btn(target: str = "adm_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=target)]])


def cancel_btn() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="adm_cancel")]])


def channels_menu(channels: list) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        rows.append([InlineKeyboardButton(
            f"🗑 حذف  {ch['name']}",
            callback_data=f"delchannel_{ch['channel_id']}"
        )])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


def filetypes_menu(file_types: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{ft['emoji']} {ft['name']}",
        callback_data=f"editft_{ft['id']}"
    )] for ft in file_types]
    rows.append([InlineKeyboardButton("➕ إضافة نوع", callback_data="adm_addft")])
    rows.append([InlineKeyboardButton("🔙 رجوع",      callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)


def settings_menu(enabled: bool) -> InlineKeyboardMarkup:
    toggle_label = "🔴 إيقاف البوت" if enabled else "🟢 تشغيل البوت"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ رسالة الترحيب",   callback_data="adm_set_welcome")],
        [InlineKeyboardButton("🖼 شعار البوت",       callback_data="adm_set_logo")],
        [InlineKeyboardButton(toggle_label,          callback_data="adm_toggle")],
        [InlineKeyboardButton("🔙 رجوع",             callback_data="adm_main")],
    ])


def publish_type_menu(file_types: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{ft['emoji']} {ft['name']}",
        callback_data=f"pub_type_{ft['id']}"
    )] for ft in file_types]
    rows.append([InlineKeyboardButton("❌ إلغاء", callback_data="adm_cancel")])
    return InlineKeyboardMarkup(rows)


def publish_channel_menu(channels: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"📢 {ch['name']}",
        callback_data=f"pub_ch_{ch['channel_id']}"
    )] for ch in channels]
    rows.append([InlineKeyboardButton("📢 كل القنوات", callback_data="pub_ch_ALL")])
    rows.append([InlineKeyboardButton("❌ إلغاء",      callback_data="adm_cancel")])
    return InlineKeyboardMarkup(rows)


def publish_logo_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ بدون شعار", callback_data="pub_skiplogo")],
        [InlineKeyboardButton("❌ إلغاء",     callback_data="adm_cancel")],
    ])


def publish_confirm_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ نشر الآن",  callback_data="pub_confirm")],
        [InlineKeyboardButton("❌ إلغاء",     callback_data="adm_cancel")],
    ])


def admins_menu(admins: list, is_main: bool) -> InlineKeyboardMarkup:
    rows = []
    if is_main:
        for adm in admins:
            if not adm["is_main"]:
                rows.append([InlineKeyboardButton(
                    f"🗑 حذف  {adm['full_name']}",
                    callback_data=f"deladmin_{adm['user_id']}"
                )])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="adm_main")])
    return InlineKeyboardMarkup(rows)
