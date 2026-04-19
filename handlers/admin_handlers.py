from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest
import database as db
import keyboards as kb
from config import BOT_NAME, MAIN_ADMIN_ID


# ════════════════════════════════════════════════════════
#  /admin  — entry point
# ════════════════════════════════════════════════════════
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        return
    await show_main_menu(update.message, user.id)


async def show_main_menu(msg_or_query, user_id: int):
    stats   = await db.get_stats()
    enabled = await db.get_setting("bot_enabled", "1")
    status  = "🟢 يعمل" if enabled == "1" else "🔴 متوقف"
    is_main = await db.is_main_admin(user_id)

    text = (
        f"👑 *لوحة تحكم {BOT_NAME}*\n\n"
        f"الحالة: {status}\n"
        f"👥 مستخدمون: {stats['users']}\n"
        f"📁 ملفات: {stats['files']}\n"
        f"❤️ تفاعلات: {stats['reactions']}\n"
        f"📥 استلامات: {stats['deliveries']}\n"
        f"📢 قنوات: {stats['channels']}\n"
    )
    markup = kb.admin_main_menu(is_main)
    if hasattr(msg_or_query, "edit_message_text"):
        await msg_or_query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
    else:
        await msg_or_query.reply_text(text, parse_mode="Markdown", reply_markup=markup)


# ════════════════════════════════════════════════════════
#  Callback router
# ════════════════════════════════════════════════════════
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()

    if not await db.is_admin(user.id):
        await query.edit_message_text("❌ ليس لديك صلاحية.")
        return

    data = query.data

    # ── Main menu ──────────────────────────────────────
    if data == "adm_main":
        await show_main_menu(query, user.id)

    elif data == "adm_cancel":
        await db.clear_pending(user.id)
        context.user_data.clear()
        await query.edit_message_text("❌ تم الإلغاء.")

    # ── Stats ──────────────────────────────────────────
    elif data == "adm_stats":
        stats = await db.get_stats()
        text = (
            f"📊 *إحصائيات {BOT_NAME}*\n\n"
            f"👥 مستخدمون: {stats['users']}\n"
            f"📁 ملفات منشورة: {stats['files']}\n"
            f"❤️ تفاعلات: {stats['reactions']}\n"
            f"📥 استلامات: {stats['deliveries']}\n"
            f"📢 قنوات: {stats['channels']}\n"
            f"👤 مشرفون: {stats['admins']}\n"
        )
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=kb.back_btn("adm_main"))

    # ── Toggle bot ─────────────────────────────────────
    elif data == "adm_toggle":
        enabled = await db.get_setting("bot_enabled", "1")
        new_val = "0" if enabled == "1" else "1"
        await db.set_setting("bot_enabled", new_val)
        status = "🟢 تم تشغيل البوت!" if new_val == "1" else "🔴 تم إيقاف البوت!"
        await query.edit_message_text(status, reply_markup=kb.back_btn("adm_settings"))

    # ── Settings ───────────────────────────────────────
    elif data == "adm_settings":
        enabled = await db.get_setting("bot_enabled", "1") == "1"
        await query.edit_message_text(
            "⚙️ *الإعدادات*", parse_mode="Markdown",
            reply_markup=kb.settings_menu(enabled)
        )

    elif data == "adm_set_welcome":
        context.user_data["step"] = "set_welcome"
        current = await db.get_setting("welcome_message")
        await query.edit_message_text(
            f"✏️ *رسالة الترحيب الحالية:*\n\n{current}\n\n"
            "أرسل الرسالة الجديدة:\n_(استخدم {{name}} لاسم المستخدم و {{bot}} لاسم البوت)_",
            parse_mode="Markdown", reply_markup=kb.cancel_btn()
        )

    elif data == "adm_set_logo":
        context.user_data["step"] = "set_logo"
        await query.edit_message_text(
            "🖼 أرسل الصورة التي تريد استخدامها كشعار افتراضي للبوت:",
            reply_markup=kb.cancel_btn()
        )

    # ── Channels ───────────────────────────────────────
    elif data == "adm_channels":
        channels = await db.get_all_channels()
        if not channels:
            text = "📢 *القنوات:*\n\nلا توجد قنوات مضافة.\n\nاستخدم:\n`/addchannel @username الاسم`"
            await query.edit_message_text(text, parse_mode="Markdown",
                                          reply_markup=kb.back_btn("adm_main"))
        else:
            text = "📢 *القنوات المضافة:*\n\n"
            for ch in channels:
                un = f"@{ch['username']}" if ch["username"] else ch["channel_id"]
                text += f"• {ch['name']} ({un})\n"
            await query.edit_message_text(text, parse_mode="Markdown",
                                          reply_markup=kb.channels_menu(channels))

    elif data.startswith("delchannel_"):
        ch_id = data.replace("delchannel_", "")
        await db.remove_channel(ch_id)
        await query.edit_message_text("✅ تم حذف القناة.", reply_markup=kb.back_btn("adm_channels"))

    # ── File types ─────────────────────────────────────
    elif data == "adm_filetypes":
        fts = await db.get_file_types()
        text = "📁 *أنواع الملفات:*\n\n"
        for ft in fts:
            text += f"{ft['emoji']} {ft['name']} — `{ft['id']}`\n"
            if ft["description"]:
                text += f"   _{ft['description'][:60]}_\n"
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=kb.filetypes_menu(fts))

    elif data.startswith("editft_"):
        ft_id = data.replace("editft_", "")
        context.user_data["step"]    = "editft_desc"
        context.user_data["ft_edit"] = ft_id
        await query.edit_message_text(
            f"✏️ أرسل الوصف الجديد للنوع `{ft_id}`\n_(أو `-` لمسح الوصف)_",
            parse_mode="Markdown", reply_markup=kb.cancel_btn()
        )

    elif data == "adm_addft":
        if not await db.is_main_admin(user.id):
            await query.edit_message_text("❌ هذا الخيار للمشرف الرئيسي فقط.")
            return
        context.user_data["step"] = "addft_id"
        await query.edit_message_text(
            "➕ أرسل معرف النوع الجديد (إنجليزي بدون مسافات):\nمثال: `vpn`",
            parse_mode="Markdown", reply_markup=kb.cancel_btn()
        )

    # ── Admins ─────────────────────────────────────────
    elif data == "adm_admins":
        if not await db.is_main_admin(user.id):
            return
        admins = await db.get_all_admins()
        text = "👤 *المشرفون:*\n\n"
        for adm in admins:
            role = "👑" if adm["is_main"] else "👤"
            ch   = ", ".join(adm["allowed_channels"]) if adm["allowed_channels"] else "كل القنوات"
            text += f"{role} {adm['full_name']} `{adm['user_id']}`\n📢 {ch}\n\n"
        text += "لإضافة مشرف: `/addadmin ID`\nلحذف مشرف: اضغط الزر أدناه"
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=kb.admins_menu(admins, True))

    elif data.startswith("deladmin_"):
        if not await db.is_main_admin(user.id):
            return
        target = int(data.replace("deladmin_", ""))
        await db.remove_admin(target)
        await query.edit_message_text("✅ تم حذف المشرف.", reply_markup=kb.back_btn("adm_admins"))

    # ── Broadcast ──────────────────────────────────────
    elif data == "adm_broadcast":
        if not await db.is_main_admin(user.id):
            return
        context.user_data["step"] = "broadcast"
        await query.edit_message_text(
            "📣 *إرسال رسالة للجميع*\n\n"
            "أرسل الرسالة الآن (يمكن أن تحتوي على صورة أو ملف أو فيديو أو نص فقط):",
            parse_mode="Markdown", reply_markup=kb.cancel_btn()
        )

    # ── Publish ────────────────────────────────────────
    elif data == "adm_publish":
        await start_publish(query, context, user.id)

    elif data.startswith("pub_type_"):
        ft_id = data.replace("pub_type_", "")
        await db.update_pending(user.id, {"file_type": ft_id, "step": "file"})
        context.user_data["step"] = "pub_file"
        fts  = await db.get_file_types()
        ft   = next((f for f in fts if f["id"] == ft_id), {"emoji": "📦", "name": ft_id})
        await query.edit_message_text(
            f"📤 نشر *{ft['emoji']} {ft['name']}*\n\nأرسل الملف الآن:",
            parse_mode="Markdown", reply_markup=kb.cancel_btn()
        )

    elif data == "pub_skiplogo":
        await db.update_pending(user.id, {"logo_file_id": "", "step": "caption"})
        context.user_data["step"] = "pub_caption"
        await _ask_caption(query, user.id)

    elif data.startswith("pub_ch_"):
        ch_id = data.replace("pub_ch_", "")
        await db.update_pending(user.id, {"channel_id": ch_id, "step": "confirm"})
        context.user_data["step"] = "pub_confirm"
        pending = await db.get_pending(user.id)
        fts = await db.get_file_types()
        ft  = next((f for f in fts if f["id"] == pending.get("file_type", "")),
                   {"emoji": "📦", "name": "ملف"})
        ch_text = "كل القنوات" if ch_id == "ALL" else ch_id
        text = (
            f"✅ *تأكيد النشر*\n\n"
            f"النوع: {ft['emoji']} {ft['name']}\n"
            f"القناة: {ch_text}\n"
            f"الوصف: {(pending.get('caption') or 'افتراضي')[:60]}\n"
            f"شعار: {'✅' if pending.get('logo_file_id') else '❌'}\n\n"
            "هل تريد النشر الآن؟"
        )
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=kb.publish_confirm_menu())

    elif data == "pub_confirm":
        await query.edit_message_text("⏳ جاري النشر...")
        await do_publish(query, context, user.id)


# ════════════════════════════════════════════════════════
#  Publish flow helpers
# ════════════════════════════════════════════════════════
async def start_publish(query, context, user_id: int):
    await db.clear_pending(user_id)
    await db.set_pending(user_id, {"step": "type"})
    fts = await db.get_file_types()
    await query.edit_message_text(
        "📤 *نشر ملف جديد*\n\nاختر نوع الملف:",
        parse_mode="Markdown",
        reply_markup=kb.publish_type_menu(fts)
    )


async def _ask_caption(query_or_msg, user_id: int):
    fts     = await db.get_file_types()
    pending = await db.get_pending(user_id)
    ft      = next((f for f in fts if f["id"] == pending.get("file_type", "")),
                   {"description": ""})
    default = ft.get("description", "") or "لا يوجد وصف افتراضي"
    text = (
        "✏️ أرسل وصف المنشور:\n"
        f"_(أو أرسل `-` لاستخدام الوصف الافتراضي)_\n\n"
        f"*الافتراضي:*\n{default}"
    )
    if hasattr(query_or_msg, "edit_message_text"):
        await query_or_msg.edit_message_text(text, parse_mode="Markdown",
                                             reply_markup=kb.cancel_btn())
    else:
        await query_or_msg.reply_text(text, parse_mode="Markdown",
                                      reply_markup=kb.cancel_btn())


async def do_publish(query, context, admin_id: int):
    pending = await db.get_pending(admin_id)
    if not pending or not pending.get("file_id"):
        await query.edit_message_text("❌ حدث خطأ. ابدأ من جديد.")
        return

    fts     = await db.get_file_types()
    ft_map  = {ft["id"]: ft for ft in fts}
    ft      = ft_map.get(pending.get("file_type", ""), {"name": "ملف", "emoji": "📦"})
    caption = pending.get("caption") or ft.get("description", "")
    logo    = pending.get("logo_file_id", "")
    ch_id   = pending.get("channel_id", "")

    channels = await db.get_all_channels()
    if ch_id == "ALL":
        targets = channels
    else:
        targets = [c for c in channels if c["channel_id"] == ch_id]

    # Check admin permissions
    admin = await db.get_admin(admin_id)
    if admin and not admin["is_main"] and admin.get("allowed_channels"):
        allowed = admin["allowed_channels"]
        targets = [c for c in targets if c["channel_id"] in allowed]

    if not targets:
        await query.edit_message_text("❌ لا توجد قنوات مصرح لك بالنشر فيها.")
        return

    bot_username = context.bot.username
    post_caption = f"{ft['emoji']} *{ft['name']}*"
    if caption:
        post_caption += f"\n\n{caption}"
    post_caption += f"\n\n🤖 {BOT_NAME}"

    success = 0
    for ch in targets:
        try:
            # Send post (with or without logo)
            if logo:
                msg = await context.bot.send_photo(
                    chat_id=ch["channel_id"],
                    photo=logo,
                    caption=post_caption,
                    parse_mode="Markdown"
                )
            else:
                msg = await context.bot.send_message(
                    chat_id=ch["channel_id"],
                    text=post_caption,
                    parse_mode="Markdown"
                )

            file_db_id = await db.save_file(
                file_id=pending["file_id"],
                file_type=pending.get("file_type", "general"),
                file_name=pending.get("file_name", ""),
                caption=caption,
                logo_file_id=logo,
                published_by=admin_id,
                channel_id=ch["channel_id"],
                message_id=msg.message_id
            )

            markup = kb.channel_post_buttons(file_db_id, 0, 0, bot_username)
            if logo:
                await context.bot.edit_message_caption(
                    chat_id=ch["channel_id"],
                    message_id=msg.message_id,
                    caption=post_caption,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            else:
                await context.bot.edit_message_reply_markup(
                    chat_id=ch["channel_id"],
                    message_id=msg.message_id,
                    reply_markup=markup
                )
            success += 1
        except TelegramError as e:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"❌ فشل النشر في {ch['name']}: {e}"
            )

    await db.clear_pending(admin_id)
    context.user_data.clear()
    await query.edit_message_text(
        f"✅ *تم النشر بنجاح في {success}/{len(targets)} قناة!*",
        parse_mode="Markdown"
    )


# ════════════════════════════════════════════════════════
#  Message handlers (files & text during flows)
# ════════════════════════════════════════════════════════
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        return  # Non-admins: completely ignore messages

    step = context.user_data.get("step", "")
    msg  = update.message

    # ── Set welcome ────────────────────────────────────
    if step == "set_welcome":
        await db.set_setting("welcome_message", msg.text.strip())
        context.user_data.clear()
        await msg.reply_text("✅ تم تحديث رسالة الترحيب!")

    # ── Set logo ───────────────────────────────────────
    elif step == "set_logo":
        if msg.photo:
            await db.set_setting("bot_logo", msg.photo[-1].file_id)
            context.user_data.clear()
            await msg.reply_text("✅ تم تعيين الشعار الافتراضي!")
        else:
            await msg.reply_text("❌ أرسل صورة.")

    # ── Edit filetype description ──────────────────────
    elif step == "editft_desc":
        ft_id = context.user_data.get("ft_edit", "")
        desc  = "" if msg.text.strip() == "-" else msg.text.strip()
        await db.set_filetype_desc(ft_id, desc)
        context.user_data.clear()
        await msg.reply_text(f"✅ تم تحديث وصف النوع `{ft_id}`.", parse_mode="Markdown")

    # ── Add file type: step 1 ──────────────────────────
    elif step == "addft_id":
        type_id = msg.text.strip().lower().replace(" ", "_")
        context.user_data["new_ft_id"] = type_id
        context.user_data["step"]      = "addft_emoji"
        await msg.reply_text(f"✅ المعرف: `{type_id}`\n\nأرسل الإيموجي للنوع:",
                             parse_mode="Markdown")

    elif step == "addft_emoji":
        context.user_data["new_ft_emoji"] = msg.text.strip()
        context.user_data["step"]         = "addft_name"
        await msg.reply_text("✅ أرسل الاسم بالعربية:")

    elif step == "addft_name":
        ft_id   = context.user_data.get("new_ft_id", "")
        emoji   = context.user_data.get("new_ft_emoji", "📦")
        await db.add_file_type(ft_id, msg.text.strip(), emoji)
        context.user_data.clear()
        await msg.reply_text(f"✅ تمت إضافة النوع: {emoji} {msg.text.strip()}")

    # ── Broadcast ──────────────────────────────────────
    elif step == "broadcast":
        context.user_data.clear()
        user_ids = await db.get_all_user_ids()
        sent = failed = 0
        for uid in user_ids:
            try:
                await _forward_or_copy(context, uid, msg)
                sent += 1
            except Exception:
                failed += 1
        await msg.reply_text(f"📣 انتهى البث!\n✅ نجح: {sent}\n❌ فشل: {failed}")

    # ── Publish: receive file ──────────────────────────
    elif step == "pub_file":
        file_id = file_name = ""
        if msg.document:
            file_id   = msg.document.file_id
            file_name = msg.document.file_name or "file"
        elif msg.photo:
            file_id   = msg.photo[-1].file_id
            file_name = "photo.jpg"
        elif msg.video:
            file_id   = msg.video.file_id
            file_name = msg.video.file_name or "video.mp4"
        elif msg.audio:
            file_id   = msg.audio.file_id
            file_name = msg.audio.file_name or "audio.mp3"
        else:
            await msg.reply_text("❌ أرسل ملفاً صحيحاً.")
            return

        await db.update_pending(user.id, {"file_id": file_id, "file_name": file_name, "step": "logo"})
        context.user_data["step"] = "pub_logo"
        await msg.reply_text(
            "🖼 أرسل صورة الشعار للمنشور (اختياري):",
            reply_markup=kb.publish_logo_menu()
        )

    # ── Publish: receive logo ──────────────────────────
    elif step == "pub_logo":
        if msg.photo:
            logo_id = msg.photo[-1].file_id
            await db.update_pending(user.id, {"logo_file_id": logo_id, "step": "caption"})
            context.user_data["step"] = "pub_caption"
            await _ask_caption(msg, user.id)
        else:
            await msg.reply_text("❌ أرسل صورة أو اضغط (بدون شعار).")

    # ── Publish: receive caption ───────────────────────
    elif step == "pub_caption":
        pending = await db.get_pending(user.id)
        fts     = await db.get_file_types()
        ft      = next((f for f in fts if f["id"] == pending.get("file_type", "")),
                       {"description": ""})
        caption = ft.get("description", "") if msg.text.strip() == "-" else msg.text.strip()
        await db.update_pending(user.id, {"caption": caption, "step": "channel"})
        context.user_data["step"] = "pub_channel"

        admin   = await db.get_admin(user.id)
        channels = await db.get_all_channels()
        if not await db.is_main_admin(user.id) and admin and admin.get("allowed_channels"):
            channels = [c for c in channels if c["channel_id"] in admin["allowed_channels"]]

        if not channels:
            await msg.reply_text("❌ لا توجد قنوات مضافة أو مصرح لك بالنشر فيها.")
            return

        await msg.reply_text("📢 اختر القناة للنشر:",
                             reply_markup=kb.publish_channel_menu(channels))


# ════════════════════════════════════════════════════════
#  Commands
# ════════════════════════════════════════════════════════
async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "الاستخدام: `/addadmin [user_id] [channel_id1,channel_id2]`\n"
            "اترك القنوات فارغة للسماح بكل القنوات.",
            parse_mode="Markdown"
        )
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ معرف غير صحيح.")
        return

    channels = args[1].split(",") if len(args) > 1 else []

    try:
        chat = await context.bot.get_chat(target_id)
        name = chat.full_name or str(target_id)
        uname = chat.username or ""
    except Exception:
        name  = str(target_id)
        uname = ""

    await db.add_admin(target_id, uname, name, user.id, channels)
    ch_text = ", ".join(channels) if channels else "جميع القنوات"
    await update.message.reply_text(
        f"✅ تمت إضافة المشرف:\n👤 {name}\n🆔 `{target_id}`\n📢 {ch_text}",
        parse_mode="Markdown"
    )


async def removeadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
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


async def addchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "الاستخدام: `/addchannel @username_أو_ID الاسم`\n\n"
            "⚠️ أضف البوت كمشرف في القناة أولاً!",
            parse_mode="Markdown"
        )
        return
    channel_id = context.args[0]
    name       = " ".join(context.args[1:])
    try:
        chat   = await context.bot.get_chat(channel_id)
        name   = chat.title or name
        uname  = chat.username or ""
        cid    = str(chat.id)
    except Exception:
        uname = ""
        cid   = channel_id

    await db.add_channel(cid, name, uname, user.id)
    await update.message.reply_text(
        f"✅ تمت إضافة القناة: *{name}*\n🆔 `{cid}`",
        parse_mode="Markdown"
    )


async def addfiletype_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "الاستخدام: `/addfiletype id emoji الاسم`\n\nمثال: `/addfiletype vpn 🔐 VPN`",
            parse_mode="Markdown"
        )
        return
    await db.add_file_type(context.args[0].lower(), " ".join(context.args[2:]), context.args[1])
    await update.message.reply_text(
        f"✅ تمت إضافة النوع: {context.args[1]} {' '.join(context.args[2:])}"
    )


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_main_admin(user.id):
        return
    if not context.args:
        await update.message.reply_text("الاستخدام: `/broadcast الرسالة`", parse_mode="Markdown")
        return
    text     = " ".join(context.args)
    user_ids = await db.get_all_user_ids()
    sent = failed = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"📣 ✅ {sent} | ❌ {failed}")


# ════════════════════════════════════════════════════════
#  Helpers
# ════════════════════════════════════════════════════════
async def _forward_or_copy(context, chat_id: int, msg):
    """Copy any message type to a user"""
    if msg.photo:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=msg.photo[-1].file_id,
            caption=msg.caption or ""
        )
    elif msg.document:
        await context.bot.send_document(
            chat_id=chat_id,
            document=msg.document.file_id,
            caption=msg.caption or ""
        )
    elif msg.video:
        await context.bot.send_video(
            chat_id=chat_id,
            video=msg.video.file_id,
            caption=msg.caption or ""
        )
    elif msg.audio:
        await context.bot.send_audio(
            chat_id=chat_id,
            audio=msg.audio.file_id,
            caption=msg.caption or ""
        )
    elif msg.voice:
        await context.bot.send_voice(
            chat_id=chat_id,
            voice=msg.voice.file_id
        )
    elif msg.sticker:
        await context.bot.send_sticker(
            chat_id=chat_id,
            sticker=msg.sticker.file_id
        )
    else:
        await context.bot.send_message(chat_id=chat_id, text=msg.text or "")
