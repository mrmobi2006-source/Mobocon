from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import database as db
from config import BOT_NAME, MAIN_ADMIN_ID
from handlers.user_handlers import build_channel_buttons

# ─── Admin Panel ────────────────────────────────────────────────
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية الوصول.")
        return

    is_main = await db.is_main_admin(user.id)
    stats = await db.get_stats()

    text = f"👑 *لوحة تحكم {BOT_NAME}*\n\n"
    text += f"👥 المستخدمون: {stats['users']}\n"
    text += f"📁 الملفات المنشورة: {stats['files']}\n"
    text += f"❤️ إجمالي التفاعلات: {stats['reactions']}\n"
    text += f"📢 القنوات: {stats['channels']}\n"
    text += f"👤 المشرفون: {stats['admins']}\n\n"

    buttons = [
        [InlineKeyboardButton("📤 نشر ملف جديد", callback_data="admin_publish")],
        [InlineKeyboardButton("📢 القنوات", callback_data="admin_channels"),
         InlineKeyboardButton("📁 أنواع الملفات", callback_data="admin_filetypes")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
    ]

    if is_main:
        buttons.append([InlineKeyboardButton("👤 إدارة المشرفين", callback_data="admin_admins")])
        buttons.append([InlineKeyboardButton("📣 إرسال لجميع المستخدمين", callback_data="admin_broadcast")])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if not await db.is_admin(user.id):
        await query.edit_message_text("❌ ليس لديك صلاحية.")
        return

    data = query.data

    if data == "admin_publish":
        await start_publish_flow(query, context)

    elif data == "admin_channels":
        channels = await db.get_all_channels()
        if not channels:
            text = "📢 *القنوات المضافة:*\n\nلا توجد قنوات مضافة بعد.\n\nاستخدم:\n`/addchannel [channel_id] [الاسم]`"
        else:
            text = "📢 *القنوات المضافة:*\n\n"
            for ch in channels:
                status = "✅" if ch["is_active"] else "❌"
                text += f"{status} {ch['name']} (`{ch['channel_id']}`)\n"
        buttons = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_filetypes":
        file_types = await db.get_file_types()
        text = "📁 *أنواع الملفات:*\n\n"
        for ft in file_types:
            text += f"{ft['emoji']} {ft['name']} (`{ft['id']}`)\n"
        buttons = [[InlineKeyboardButton("➕ إضافة نوع جديد", callback_data="admin_addfiletype")],
                   [InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_addfiletype":
        context.user_data["awaiting"] = "addfiletype_id"
        await query.edit_message_text(
            "➕ *إضافة نوع ملف جديد*\n\nأرسل معرف النوع (بالإنجليزية، بدون مسافات):\nمثال: `vpn` أو `movies`",
            parse_mode="Markdown"
        )

    elif data == "admin_settings":
        await show_settings_menu(query, context)

    elif data == "admin_stats":
        stats = await db.get_stats()
        text = f"📊 *إحصائيات {BOT_NAME}*\n\n"
        text += f"👥 المستخدمون: {stats['users']}\n"
        text += f"📁 الملفات: {stats['files']}\n"
        text += f"❤️ التفاعلات: {stats['reactions']}\n"
        text += f"📢 القنوات: {stats['channels']}\n"
        text += f"👤 المشرفون: {stats['admins']}\n"
        buttons = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_admins" and await db.is_main_admin(user.id):
        admins = await db.get_all_admins()
        text = "👤 *قائمة المشرفين:*\n\n"
        for adm in admins:
            role = "👑 رئيسي" if adm["is_main"] else "👤 مشرف"
            text += f"{role}: {adm['full_name']} (`{adm['user_id']}`)\n"
        text += "\nللإضافة: `/addadmin [ID]`\nللحذف: `/removeadmin [ID]`"
        buttons = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_broadcast" and await db.is_main_admin(user.id):
        context.user_data["awaiting"] = "broadcast_message"
        await query.edit_message_text("📣 أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:")

    elif data == "admin_settings_reactions":
        context.user_data["awaiting"] = "set_reactions"
        req = await db.get_setting("reactions_required")
        await query.edit_message_text(
            f"⚙️ *إعداد عدد التفاعلات المطلوبة*\n\nالحالي: {req}\n\nأرسل العدد الجديد:",
            parse_mode="Markdown"
        )

    elif data == "admin_settings_welcome":
        context.user_data["awaiting"] = "set_welcome"
        current = await db.get_setting("welcome_message")
        await query.edit_message_text(
            f"✏️ *تعديل رسالة الترحيب*\n\nالحالية:\n{current}\n\nأرسل الرسالة الجديدة (استخدم {{name}} لاسم المستخدم):",
            parse_mode="Markdown"
        )

    elif data == "admin_settings_logo":
        context.user_data["awaiting"] = "set_logo"
        await query.edit_message_text("🖼️ أرسل الصورة التي تريد استخدامها كشعار للبوت:")

    elif data == "admin_back":
        stats = await db.get_stats()
        text = f"👑 *لوحة تحكم {BOT_NAME}*\n\n"
        text += f"👥 المستخدمون: {stats['users']}\n"
        text += f"📁 الملفات المنشورة: {stats['files']}\n"
        text += f"❤️ إجمالي التفاعلات: {stats['reactions']}\n"
        is_main = await db.is_main_admin(user.id)
        buttons = [
            [InlineKeyboardButton("📤 نشر ملف جديد", callback_data="admin_publish")],
            [InlineKeyboardButton("📢 القنوات", callback_data="admin_channels"),
             InlineKeyboardButton("📁 أنواع الملفات", callback_data="admin_filetypes")],
            [InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        ]
        if is_main:
            buttons.append([InlineKeyboardButton("👤 إدارة المشرفين", callback_data="admin_admins")])
            buttons.append([InlineKeyboardButton("📣 إرسال لجميع المستخدمين", callback_data="admin_broadcast")])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

async def show_settings_menu(query, context):
    req = await db.get_setting("reactions_required")
    text = f"⚙️ *الإعدادات*\n\nعدد التفاعلات المطلوبة: {req}"
    buttons = [
        [InlineKeyboardButton(f"❤️ تعديل عدد التفاعلات ({req})", callback_data="admin_settings_reactions")],
        [InlineKeyboardButton("✏️ رسالة الترحيب", callback_data="admin_settings_welcome")],
        [InlineKeyboardButton("🖼️ تغيير الشعار", callback_data="admin_settings_logo")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")],
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# ─── Publish Flow ────────────────────────────────────────────────
async def start_publish_flow(query, context):
    user = query.from_user
    await db.clear_pending_file(user.id)
    await db.set_pending_file(user.id, {"step": "file"})

    file_types = await db.get_file_types()
    buttons = [[InlineKeyboardButton(f"{ft['emoji']} {ft['name']}", callback_data=f"publish_type_{ft['id']}")] for ft in file_types]
    buttons.append([InlineKeyboardButton("🔙 إلغاء", callback_data="publish_cancel")])

    await query.edit_message_text(
        "📤 *نشر ملف جديد*\n\nاختر نوع الملف:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_publish_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if not await db.is_admin(user.id):
        return

    data = query.data

    if data == "publish_cancel":
        await db.clear_pending_file(user.id)
        context.user_data.pop("awaiting", None)
        await query.edit_message_text("❌ تم إلغاء النشر.")
        return

    if data.startswith("publish_type_"):
        file_type = data.replace("publish_type_", "")
        await db.update_pending_file(user.id, {"file_type": file_type, "step": "file"})

        # Get default description for this type
        ft_list = await db.get_file_types()
        ft_map = {ft["id"]: ft for ft in ft_list}
        ft = ft_map.get(file_type, {})

        context.user_data["awaiting"] = "publish_file"
        await query.edit_message_text(
            f"📤 *نشر ملف {ft.get('emoji','')} {ft.get('name','')}*\n\nأرسل الملف الآن:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="publish_cancel")]])
        )

    elif data.startswith("publish_channel_"):
        channel_id = data.replace("publish_channel_", "")
        pending = await db.get_pending_file(user.id)
        if not pending:
            await query.edit_message_text("❌ انتهت الجلسة. ابدأ مجدداً.")
            return

        await query.edit_message_text("⏳ جاري النشر...")
        await do_publish(query, context, user.id, channel_id, pending)

    elif data == "publish_skip_logo":
        context.user_data["awaiting"] = "publish_caption"
        pending = await db.get_pending_file(user.id)
        ft_list = await db.get_file_types()
        ft_map = {ft["id"]: ft for ft in ft_list}
        ft = ft_map.get(pending.get("file_type", "general"), {})
        default_desc = ft.get("description", "")

        await query.edit_message_text(
            f"✏️ أرسل وصف المنشور (أو أرسل `-` لاستخدام الوصف الافتراضي):\n\n*الوصف الافتراضي:*\n{default_desc}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="publish_cancel")]])
        )

async def do_publish(query, context, admin_id: int, channel_id: str, pending: dict):
    """Actually publish the file to the channel"""
    try:
        admin = await db.get_admin(admin_id)
        if admin and not admin["is_main"]:
            allowed = admin.get("allowed_channels", [])
            if allowed and channel_id not in allowed:
                await query.edit_message_text("❌ ليس لديك إذن للنشر في هذه القناة.")
                return

        file_types = await db.get_file_types()
        ft_map = {ft["id"]: ft for ft in file_types}
        ft = ft_map.get(pending.get("file_type", "general"), {"name": "ملف", "emoji": "📦"})

        caption = pending.get("caption") or ft.get("description", "")
        logo_file_id = pending.get("logo_file_id", "")
        bot_username = context.bot.username

        # Temporary file_db_id placeholder (we'll get real one after saving)
        # First send without buttons to get message_id, then save and edit
        post_caption = f"{ft['emoji']} *{ft['name']}*\n\n{caption}\n\n🤖 {BOT_NAME}"

        # Send logo + caption if logo exists
        if logo_file_id:
            msg = await context.bot.send_photo(
                chat_id=channel_id,
                photo=logo_file_id,
                caption=post_caption,
                parse_mode="Markdown"
            )
        else:
            msg = await context.bot.send_message(
                chat_id=channel_id,
                text=post_caption,
                parse_mode="Markdown"
            )

        message_id = msg.message_id

        # Save to DB to get file_db_id
        file_db_id = await db.save_file(
            file_id=pending["file_id"],
            file_type=pending.get("file_type", "general"),
            file_name=pending.get("file_name", ""),
            caption=caption,
            published_by=admin_id,
            channel_id=channel_id,
            message_id=message_id
        )

        # Build the 3-button layout
        markup = build_channel_buttons(file_db_id, 0, bot_username, pending.get("file_type", "general"))

        # Edit message to add buttons
        if logo_file_id:
            await context.bot.edit_message_caption(
                chat_id=channel_id,
                message_id=message_id,
                caption=post_caption,
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            await context.bot.edit_message_reply_markup(
                chat_id=channel_id,
                message_id=message_id,
                reply_markup=markup
            )

        await db.clear_pending_file(admin_id)
        context.user_data.pop("awaiting", None)

        # Get channel info
        channel = await db.get_channel(channel_id)
        ch_name = channel["name"] if channel else channel_id

        await query.edit_message_text(
            f"✅ *تم النشر بنجاح!*\n\n"
            f"📢 القناة: {ch_name}\n"
            f"📁 النوع: {ft['emoji']} {ft['name']}\n"
            f"🆔 رقم الملف: `{file_db_id}`",
            parse_mode="Markdown"
        )

    except TelegramError as e:
        await query.edit_message_text(f"❌ فشل النشر!\n\nالخطأ: {str(e)}\n\nتأكد من أن البوت مشرف في القناة.")

# ─── File Upload Handler ─────────────────────────────────────────
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        return

    awaiting = context.user_data.get("awaiting")
    if awaiting != "publish_file" and awaiting != "set_logo":
        return

    if awaiting == "set_logo":
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            await db.set_setting("bot_logo", file_id)
            context.user_data.pop("awaiting", None)
            await update.message.reply_text("✅ تم تعيين الشعار بنجاح!")
        return

    # Handle file for publishing
    pending = await db.get_pending_file(user.id)
    if not pending:
        await db.set_pending_file(user.id, {"step": "logo"})
        pending = await db.get_pending_file(user.id)

    if update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name or "file"
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_name = "photo.jpg"
    elif update.message.video:
        file_id = update.message.video.file_id
        file_name = update.message.video.file_name or "video.mp4"
    else:
        return

    await db.update_pending_file(user.id, {"file_id": file_id, "file_name": file_name, "step": "logo"})
    context.user_data["awaiting"] = "publish_logo"

    await update.message.reply_text(
        "🖼️ أرسل صورة الشعار للمنشور، أو اضغط لتخطي:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭️ تخطي الشعار", callback_data="publish_skip_logo")],
            [InlineKeyboardButton("🔙 إلغاء", callback_data="publish_cancel")]
        ])
    )

# ─── Text Input Handler ──────────────────────────────────────────
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        return

    awaiting = context.user_data.get("awaiting")
    text = update.message.text.strip()

    if awaiting == "publish_logo":
        # User sent text during logo step, treat as skip
        pass

    elif awaiting == "publish_caption":
        pending = await db.get_pending_file(user.id)
        if not pending:
            return

        ft_list = await db.get_file_types()
        ft_map = {ft["id"]: ft for ft in ft_list}
        ft = ft_map.get(pending.get("file_type", "general"), {})

        if text == "-":
            caption = ft.get("description", "")
        else:
            caption = text

        await db.update_pending_file(user.id, {"caption": caption, "step": "channel"})
        context.user_data.pop("awaiting", None)

        # Ask which channel to publish to
        admin = await db.get_admin(user.id)
        channels = await db.get_all_channels()

        if not channels:
            await update.message.reply_text("❌ لا توجد قنوات مضافة! أضف قناة أولاً بـ /addchannel")
            return

        is_main = await db.is_main_admin(user.id)
        if not is_main and admin:
            allowed = admin.get("allowed_channels", [])
            if allowed:
                channels = [ch for ch in channels if ch["channel_id"] in allowed]

        if not channels:
            await update.message.reply_text("❌ ليس لديك إذن للنشر في أي قناة.")
            return

        buttons = [[InlineKeyboardButton(f"📢 {ch['name']}", callback_data=f"publish_channel_{ch['channel_id']}")] for ch in channels]
        buttons.append([InlineKeyboardButton("🔙 إلغاء", callback_data="publish_cancel")])

        await update.message.reply_text(
            "📢 اختر القناة للنشر فيها:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif awaiting == "broadcast_message" and await db.is_main_admin(user.id):
        context.user_data.pop("awaiting", None)
        user_ids = await db.get_all_user_ids()
        sent = 0
        failed = 0
        for uid in user_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=text)
                sent += 1
            except:
                failed += 1
        await update.message.reply_text(f"📣 تم الإرسال!\n✅ نجح: {sent}\n❌ فشل: {failed}")

    elif awaiting == "set_reactions" and await db.is_admin(user.id):
        try:
            n = int(text)
            if n < 1:
                n = 1
            await db.set_setting("reactions_required", str(n))
            context.user_data.pop("awaiting", None)
            await update.message.reply_text(f"✅ تم تعيين عدد التفاعلات المطلوبة: {n}")
        except ValueError:
            await update.message.reply_text("❌ أرسل رقماً صحيحاً.")

    elif awaiting == "set_welcome" and await db.is_admin(user.id):
        await db.set_setting("welcome_message", text)
        context.user_data.pop("awaiting", None)
        await update.message.reply_text("✅ تم تعيين رسالة الترحيب بنجاح!")

    elif awaiting == "addfiletype_id" and await db.is_main_admin(user.id):
        type_id = text.lower().replace(" ", "_")
        context.user_data["new_filetype_id"] = type_id
        context.user_data["awaiting"] = "addfiletype_emoji"
        await update.message.reply_text(f"✅ المعرف: `{type_id}`\n\nأرسل الإيموجي للنوع:", parse_mode="Markdown")

    elif awaiting == "addfiletype_emoji" and await db.is_main_admin(user.id):
        context.user_data["new_filetype_emoji"] = text
        context.user_data["awaiting"] = "addfiletype_name"
        await update.message.reply_text("✅ أرسل اسم النوع بالعربية:")

    elif awaiting == "addfiletype_name" and await db.is_main_admin(user.id):
        type_id = context.user_data.get("new_filetype_id")
        emoji = context.user_data.get("new_filetype_emoji", "📦")
        await db.add_file_type(type_id, text, emoji, "")
        context.user_data.pop("awaiting", None)
        context.user_data.pop("new_filetype_id", None)
        context.user_data.pop("new_filetype_emoji", None)
        await update.message.reply_text(f"✅ تمت إضافة نوع الملف: {emoji} {text}")

    elif awaiting == "set_logo":
        await update.message.reply_text("❌ يرجى إرسال صورة وليس نصاً.")

async def handle_filetype_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Handled via text input flow

async def handle_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Handled via publish flow

# ─── Admin Commands ──────────────────────────────────────────────
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الرئيسي فقط.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("الاستخدام: `/addadmin [user_id] [channel_id1,channel_id2]`\n\nإذا تركت القنوات فارغة سيتمكن من النشر في جميع القنوات.", parse_mode="Markdown")
        return

    try:
        target_id = int(args[0])
        channels = args[1].split(",") if len(args) > 1 else []
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم غير صحيح.")
        return

    try:
        target = await context.bot.get_chat(target_id)
        full_name = target.full_name or str(target_id)
        username = target.username or ""
    except:
        full_name = str(target_id)
        username = ""

    await db.add_admin(target_id, username, full_name, user.id, channels)
    ch_text = ", ".join(channels) if channels else "جميع القنوات"
    await update.message.reply_text(f"✅ تمت إضافة المشرف:\n👤 {full_name}\n🆔 `{target_id}`\n📢 القنوات المسموحة: {ch_text}", parse_mode="Markdown")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الرئيسي فقط.")
        return

    if not context.args:
        await update.message.reply_text("الاستخدام: `/removeadmin [user_id]`", parse_mode="Markdown")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ معرف غير صحيح.")
        return

    if target_id == MAIN_ADMIN_ID:
        await update.message.reply_text("❌ لا يمكن حذف المشرف الرئيسي.")
        return

    await db.remove_admin(target_id)
    await update.message.reply_text(f"✅ تم حذف المشرف `{target_id}`.", parse_mode="Markdown")

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    admins = await db.get_all_admins()
    text = "👤 *قائمة المشرفين:*\n\n"
    for adm in admins:
        role = "👑 رئيسي" if adm["is_main"] else "👤 مشرف"
        ch = ", ".join(adm["allowed_channels"]) if adm["allowed_channels"] else "جميع القنوات"
        text += f"{role}: {adm['full_name']}\n🆔 `{adm['user_id']}`\n📢 {ch}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    s = await db.get_stats()
    text = f"📊 *إحصائيات {BOT_NAME}*\n\n"
    text += f"👥 المستخدمون: {s['users']}\n"
    text += f"📁 الملفات: {s['files']}\n"
    text += f"❤️ التفاعلات: {s['reactions']}\n"
    text += f"📢 القنوات: {s['channels']}\n"
    text += f"👤 المشرفون: {s['admins']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الرئيسي فقط.")
        return

    if not context.args:
        await update.message.reply_text("الاستخدام: `/broadcast [الرسالة]`", parse_mode="Markdown")
        return

    message = " ".join(context.args)
    user_ids = await db.get_all_user_ids()
    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
        except:
            failed += 1
    await update.message.reply_text(f"📣 انتهى الإرسال!\n✅ نجح: {sent}\n❌ فشل: {failed}")

async def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    if len(context.args) < 2:
        ft_list = await db.get_file_types()
        types_str = ", ".join([ft["id"] for ft in ft_list])
        await update.message.reply_text(
            f"الاستخدام: `/setdesc [type] [الوصف]`\n\nالأنواع المتاحة: {types_str}",
            parse_mode="Markdown"
        )
        return

    type_id = context.args[0]
    description = " ".join(context.args[1:])
    await db.update_file_type_description(type_id, description)
    await update.message.reply_text(f"✅ تم تعديل وصف النوع `{type_id}`.", parse_mode="Markdown")

async def set_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return
    context.user_data["awaiting"] = "set_logo"
    await update.message.reply_text("🖼️ أرسل الصورة التي تريد استخدامها كشعار للبوت:")

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "الاستخدام: `/addchannel [channel_id] [الاسم]`\n\nمثال:\n`/addchannel -1001234567890 قناتي`\n\n⚠️ يجب إضافة البوت كمشرف في القناة أولاً.",
            parse_mode="Markdown"
        )
        return

    channel_id = context.args[0]
    name = " ".join(context.args[1:])

    try:
        chat = await context.bot.get_chat(channel_id)
        username = chat.username or ""
        actual_name = chat.title or name
    except:
        username = ""
        actual_name = name

    await db.add_channel(channel_id, actual_name, username, user.id)
    await update.message.reply_text(f"✅ تمت إضافة القناة: {actual_name}\n🆔 `{channel_id}`", parse_mode="Markdown")

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الرئيسي فقط.")
        return

    if not context.args:
        await update.message.reply_text("الاستخدام: `/removechannel [channel_id]`", parse_mode="Markdown")
        return

    await db.remove_channel(context.args[0])
    await update.message.reply_text("✅ تم حذف القناة.")

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    channels = await db.get_all_channels()
    if not channels:
        await update.message.reply_text("لا توجد قنوات مضافة.")
        return

    text = "📢 *القنوات المضافة:*\n\n"
    for ch in channels:
        status = "✅" if ch["is_active"] else "❌"
        un = f"@{ch['username']}" if ch["username"] else "خاصة"
        text += f"{status} {ch['name']} ({un})\n🆔 `{ch['channel_id']}`\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def publish_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    await db.clear_pending_file(user.id)
    await db.set_pending_file(user.id, {"step": "type"})

    file_types = await db.get_file_types()
    buttons = [[InlineKeyboardButton(f"{ft['emoji']} {ft['name']}", callback_data=f"publish_type_{ft['id']}")] for ft in file_types]
    buttons.append([InlineKeyboardButton("🔙 إلغاء", callback_data="publish_cancel")])

    await update.message.reply_text(
        "📤 *نشر ملف جديد*\n\nاختر نوع الملف:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def add_file_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الرئيسي فقط.")
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "الاستخدام: `/addfiletype [id] [emoji] [الاسم]`\n\nمثال:\n`/addfiletype vpn 🔐 VPN`",
            parse_mode="Markdown"
        )
        return

    type_id = context.args[0].lower()
    emoji = context.args[1]
    name = " ".join(context.args[2:])
    await db.add_file_type(type_id, name, emoji, "")
    await update.message.reply_text(f"✅ تمت إضافة النوع: {emoji} {name}\n🆔 `{type_id}`", parse_mode="Markdown")

async def list_file_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    file_types = await db.get_file_types()
    text = "📁 *أنواع الملفات:*\n\n"
    for ft in file_types:
        text += f"{ft['emoji']} {ft['name']} (`{ft['id']}`)\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def set_reactions_required(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    if not context.args:
        current = await db.get_setting("reactions_required")
        await update.message.reply_text(f"الاستخدام: `/setreactions [عدد]`\n\nالحالي: {current}", parse_mode="Markdown")
        return

    try:
        n = max(1, int(context.args[0]))
        await db.set_setting("reactions_required", str(n))
        await update.message.reply_text(f"✅ عدد التفاعلات المطلوبة: {n}")
    except ValueError:
        await update.message.reply_text("❌ أرسل رقماً صحيحاً.")
