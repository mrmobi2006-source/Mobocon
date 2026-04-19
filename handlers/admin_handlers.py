from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest
import database as db
import keyboards as kb
from utils import build_post_text, ft_map_from_list
from config import BOT_NAME, MAIN_ADMIN_ID


# ════════════════════════════════════════════════════════
#  /admin
# ════════════════════════════════════════════════════════
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await db.is_admin(update.effective_user.id):
        return
    await _show_main(update.message, update.effective_user.id)


async def _show_main(target, user_id: int):
    stats   = await db.get_stats()
    enabled = await db.get_setting("bot_enabled", "1") == "1"
    status  = "🟢 يعمل" if enabled else "🔴 متوقف"
    is_main = await db.is_main_admin(user_id)

    text = (
        "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"  👑 لوحة تحكم {BOT_NAME}\n"
        "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"الحالة: {status}\n"
        f"👥 مستخدمون:   {stats['users']}\n"
        f"📁 ملفات:      {stats['files']}\n"
        f"📦 مجموعات:    {stats['groups']}\n"
        f"❤️ تفاعلات:    {stats['reactions']}\n"
        f"📥 استلامات:   {stats['deliveries']}\n"
        f"📢 قنوات:      {stats['channels']}\n"
        f"🔒 إجباري:     {stats['force_subs']}\n"
    )
    markup = kb.admin_main_menu(is_main, enabled)
    if hasattr(target, "edit_message_text"):
        await target.edit_message_text(text, reply_markup=markup)
    else:
        await target.reply_text(text, reply_markup=markup)


# ════════════════════════════════════════════════════════
#  Master callback router
# ════════════════════════════════════════════════════════
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    data  = query.data
    await query.answer()

    if not await db.is_admin(user.id):
        await query.edit_message_text("❌ ليس لديك صلاحية.")
        return

    # ── Main / cancel ──────────────────────────────────
    if data == "adm_main":
        await _show_main(query, user.id)

    elif data == "adm_cancel":
        await db.clear_pending(user.id)
        context.user_data.clear()
        await query.edit_message_text("❌ تم الإلغاء.")

    # ── Toggle ─────────────────────────────────────────
    elif data == "adm_toggle":
        cur = await db.get_setting("bot_enabled", "1")
        nv  = "0" if cur == "1" else "1"
        await db.set_setting("bot_enabled", nv)
        msg = "🟢 تم تشغيل البوت!" if nv == "1" else "🔴 تم إيقاف البوت!"
        await query.edit_message_text(msg, reply_markup=kb.back_btn("adm_main"))

    # ── Stats ──────────────────────────────────────────
    elif data == "adm_stats":
        stats = await db.get_stats()
        text  = (
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"  📊 إحصائيات {BOT_NAME}\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"👥 مستخدمون:   {stats['users']}\n"
            f"📁 ملفات:      {stats['files']}\n"
            f"📦 مجموعات:    {stats['groups']}\n"
            f"❤️ تفاعلات:    {stats['reactions']}\n"
            f"📥 استلامات:   {stats['deliveries']}\n"
            f"📢 قنوات:      {stats['channels']}\n"
            f"👤 مشرفون:     {stats['admins']}\n"
            f"🔒 إجباري:     {stats['force_subs']}\n"
        )
        await query.edit_message_text(text, reply_markup=kb.back_btn("adm_main"))

    # ── Settings ───────────────────────────────────────
    elif data == "adm_settings":
        await query.edit_message_text(
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            "        ⚙️ الإعدادات\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛",
            reply_markup=kb.settings_menu()
        )

    elif data == "adm_set_welcome":
        context.user_data["step"] = "set_welcome"
        cur = await db.get_setting("welcome_message")
        await query.edit_message_text(
            f"✏️ *رسالة الترحيب الحالية:*\n\n{cur}\n\n"
            "أرسل الرسالة الجديدة:\n"
            "_(استخدم {name} لاسم المستخدم)_",
            parse_mode="Markdown",
            reply_markup=kb.cancel_btn()
        )

    elif data == "adm_set_logo":
        context.user_data["step"] = "set_logo"
        await query.edit_message_text(
            "🖼 أرسل الصورة التي تريدها شعاراً افتراضياً للبوت:",
            reply_markup=kb.cancel_btn()
        )

    # ── Channels ───────────────────────────────────────
    elif data == "adm_channels":
        channels = await db.get_all_channels()
        if not channels:
            text = (
                "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                "       📢 القنوات\n"
                "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                "⚠️ لا توجد قنوات مضافة.\n\n"
                "استخدم:\n`/addchannel @username الاسم`"
            )
            await query.edit_message_text(text, parse_mode="Markdown",
                                          reply_markup=kb.back_btn("adm_main"))
        else:
            text = (
                "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                "       📢 القنوات\n"
                "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            )
            for ch in channels:
                un = f"@{ch['username']}" if ch["username"] else ch["channel_id"]
                text += f"• {ch['name']} ({un})\n"
            await query.edit_message_text(text, reply_markup=kb.channels_menu(channels))

    elif data.startswith("delch_"):
        cid = data[6:]
        await db.remove_channel(cid)
        await query.edit_message_text("✅ تم حذف القناة.", reply_markup=kb.back_btn("adm_channels"))

    # ── File types ─────────────────────────────────────
    elif data == "adm_filetypes":
        fts  = await db.get_file_types()
        text = (
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            "     📁 أنواع الملفات\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        )
        for ft in fts:
            text += f"{ft['emoji']} {ft['name']} — `{ft['id']}`\n"
            if ft["description"]:
                text += f"   _{ft['description'][:50]}_\n"
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=kb.filetypes_menu(fts))

    elif data.startswith("editft_"):
        ft_id = data[7:]
        context.user_data["step"]    = "editft_desc"
        context.user_data["ft_edit"] = ft_id
        await query.edit_message_text(
            f"✏️ أرسل الوصف الجديد للنوع `{ft_id}`\n_(أو `-` لمسحه)_",
            parse_mode="Markdown",
            reply_markup=kb.cancel_btn()
        )

    elif data == "adm_addft":
        if not await db.is_main_admin(user.id):
            await query.edit_message_text("❌ هذا الخيار للمشرف الرئيسي فقط.")
            return
        context.user_data["step"] = "addft_id"
        await query.edit_message_text(
            "➕ أرسل معرّف النوع (إنجليزي بدون مسافات):\nمثال: `vpn`",
            parse_mode="Markdown",
            reply_markup=kb.cancel_btn()
        )

    # ── Force sub ──────────────────────────────────────
    elif data == "adm_forcesub":
        await _show_forcesub(query)

    elif data == "adm_addsub":
        context.user_data["step"] = "addsub_type"
        await query.edit_message_text(
            "🔒 *إضافة اشتراك إجباري*\n\n"
            "أرسل بيانات الهدف بهذا الشكل:\n\n"
            "`نوع | الاسم | المعرف أو ID | الرابط`\n\n"
            "مثال قناة:\n"
            "`channel | قناة MOBO | @mobotunnel | https://t.me/mobotunnel`\n\n"
            "مثال بوت:\n"
            "`bot | بوت MOBO | @mobobot | https://t.me/mobobot`",
            parse_mode="Markdown",
            reply_markup=kb.cancel_btn()
        )

    elif data.startswith("delsub_"):
        sub_id = int(data[7:])
        await db.remove_force_sub(sub_id)
        await _show_forcesub(query)

    # ── Admins ─────────────────────────────────────────
    elif data == "adm_admins":
        if not await db.is_main_admin(user.id):
            return
        admins = await db.get_all_admins()
        text   = (
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            "       👤 المشرفون\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        )
        for adm in admins:
            role = "👑" if adm["is_main"] else "👤"
            ch   = "كل القنوات" if not adm["allowed_channels"] else "، ".join(adm["allowed_channels"])
            text += f"{role} {adm['full_name']}\n🆔 `{adm['user_id']}`\n📢 {ch}\n\n"
        text += "لإضافة مشرف: `/addadmin ID`"
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=kb.admins_menu(admins))

    elif data.startswith("deladmin_"):
        if not await db.is_main_admin(user.id):
            return
        target = int(data[9:])
        await db.remove_admin(target)
        await query.edit_message_text("✅ تم حذف المشرف.", reply_markup=kb.back_btn("adm_admins"))

    # ── Broadcast ──────────────────────────────────────
    elif data == "adm_broadcast":
        if not await db.is_main_admin(user.id):
            return
        context.user_data["step"] = "broadcast"
        await query.edit_message_text(
            "📣 *بث رسالة للجميع*\n\n"
            "أرسل الرسالة الآن — يمكن أن تكون:\n"
            "• نص\n• صورة مع تعليق\n• ملف\n• فيديو\n• أي شيء آخر",
            parse_mode="Markdown",
            reply_markup=kb.cancel_btn()
        )

    # ── Publish ────────────────────────────────────────
    elif data == "adm_publish":
        await _start_publish(query, context, user.id)

    elif data.startswith("pub_addfile_"):
        ft_id = data[12:]
        context.user_data["step"]        = "pub_file"
        context.user_data["current_type"] = ft_id
        fts = await db.get_file_types()
        ft  = next((f for f in fts if f["id"] == ft_id), {"emoji": "📦", "name": ft_id})
        await query.edit_message_text(
            f"📤 أرسل ملف *{ft['emoji']} {ft['name']}* الآن:\n"
            "_(يمكنك إرسال أي نوع ملف)_",
            parse_mode="Markdown",
            reply_markup=kb.cancel_btn()
        )

    elif data == "pub_done_files":
        pending = await db.get_pending(user.id)
        files   = pending.get("files", [])
        if not files:
            await query.answer("❌ يجب إرسال ملف واحد على الأقل!", show_alert=True)
            return
        context.user_data["step"] = "pub_logo"
        await query.edit_message_text(
            f"✅ تم إضافة {len(files)} ملف/ملفات\n\n🖼 أرسل شعار المنشور (اختياري):",
            reply_markup=kb.publish_logo_menu()
        )

    elif data == "pub_skiplogo":
        await db.update_pending(user.id, {"logo_file_id": ""})
        context.user_data["step"] = "pub_title"
        await query.edit_message_text(
            "✏️ أرسل عنوان المنشور:\nمثال: `⚡ تم تجديد الكونفيجات!`\n\n_(أو `-` لتخطيه)_",
            parse_mode="Markdown",
            reply_markup=kb.cancel_btn()
        )

    elif data.startswith("pub_ch_"):
        ch_id = data[7:]
        await db.update_pending(user.id, {"channel_id": ch_id})
        context.user_data["step"] = "pub_caption"
        await query.edit_message_text(
            "✏️ أرسل وصف المنشور:\n_(أو `-` لبدون وصف)_",
            reply_markup=kb.cancel_btn()
        )

    elif data == "pub_confirm":
        await query.edit_message_text("⏳ جاري النشر في القنوات...")
        await _do_publish(query, context, user.id)


async def _show_forcesub(query):
    subs = await db.get_force_subs()
    text = (
        "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
        "     🔒 اشتراك إجباري\n"
        "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
    )
    if subs:
        for s in subs:
            icon = "📢" if s["target_type"] == "channel" else "🤖"
            text += f"{icon} {s['target_name']} ({s['target_id']})\n"
    else:
        text += "لا يوجد اشتراك إجباري مفعّل.\n"
    await query.edit_message_text(text, reply_markup=kb.forcesub_menu(subs))


# ════════════════════════════════════════════════════════
#  Publish wizard
# ════════════════════════════════════════════════════════
async def _start_publish(query, context, user_id: int):
    await db.clear_pending(user_id)
    await db.set_pending(user_id, {"files": [], "step": "type"})
    context.user_data.clear()
    context.user_data["step"] = "pub_type"

    fts = await db.get_file_types()
    await query.edit_message_text(
        "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
        "     📤 نشر ملفات جديدة\n"
        "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "📌 اختر نوع الملف الأول:\n"
        "_(يمكنك إضافة أكثر من ملف من أنواع مختلفة)_",
        reply_markup=kb.publish_type_menu(fts)
    )


async def _do_publish(query, context, admin_id: int):
    pending  = await db.get_pending(admin_id)
    files    = pending.get("files", [])
    ch_id    = pending.get("channel_id", "")
    caption  = pending.get("caption", "")
    title    = pending.get("title", "")
    logo     = pending.get("logo_file_id", "")

    if not files:
        await query.edit_message_text("❌ لا توجد ملفات.")
        return

    all_fts  = await db.get_file_types()
    ft_map   = ft_map_from_list(all_fts)
    channels = await db.get_all_channels()

    # Build target channels list
    admin = await db.get_admin(admin_id)
    if ch_id == "ALL":
        targets = channels
    else:
        targets = [c for c in channels if c["channel_id"] == ch_id]

    if not await db.is_main_admin(admin_id) and admin and admin.get("allowed_channels"):
        allowed = admin["allowed_channels"]
        targets = [c for c in targets if c["channel_id"] in allowed]

    if not targets:
        await query.edit_message_text("❌ لا توجد قنوات مصرح لك بالنشر فيها.")
        return

    post_text   = build_post_text(title, caption, files, ft_map)
    bot_username = context.bot.username
    success = 0

    for ch in targets:
        try:
            # Create the group first (to get group_id)
            group_id = await db.create_group(
                title=title,
                caption=caption,
                logo=logo,
                published_by=admin_id,
                channel_id=ch["channel_id"]
            )

            # Send channel post
            if logo:
                msg = await context.bot.send_photo(
                    chat_id=ch["channel_id"],
                    photo=logo,
                    caption=post_text,
                )
            else:
                msg = await context.bot.send_message(
                    chat_id=ch["channel_id"],
                    text=post_text,
                )

            # Save files to DB and link to group + message
            for i, f in enumerate(files):
                await db.add_file_to_group(
                    group_id=group_id,
                    file_id=f["file_id"],
                    file_type=f["file_type"],
                    file_name=f.get("file_name", ""),
                    file_caption=f.get("file_caption", ""),
                    sort_order=i,
                    channel_id=ch["channel_id"],
                    message_id=msg.message_id
                )

            # Add buttons
            markup = kb.channel_post_buttons(group_id, 0, 0, bot_username)
            if logo:
                await context.bot.edit_message_caption(
                    chat_id=ch["channel_id"],
                    message_id=msg.message_id,
                    caption=post_text,
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
                text=f"❌ فشل النشر في {ch['name']}:\n{e}"
            )

    await db.clear_pending(admin_id)
    context.user_data.clear()
    await query.edit_message_text(
        f"┏━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"  ✅ تم النشر بنجاح!\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"📢 نُشر في {success}/{len(targets)} قناة\n"
        f"📁 عدد الملفات: {len(files)}",
        reply_markup=kb.back_btn("adm_main")
    )


# ════════════════════════════════════════════════════════
#  Message handler (admin wizard steps)
# ════════════════════════════════════════════════════════
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await db.is_admin(user.id):
        return  # Completely ignore non-admin messages

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

    # ── Edit file type desc ────────────────────────────
    elif step == "editft_desc":
        ft_id = context.user_data.get("ft_edit", "")
        desc  = "" if msg.text and msg.text.strip() == "-" else (msg.text or "").strip()
        await db.set_filetype_desc(ft_id, desc)
        context.user_data.clear()
        await msg.reply_text(f"✅ تم تحديث وصف النوع `{ft_id}`.", parse_mode="Markdown")

    # ── Add file type ──────────────────────────────────
    elif step == "addft_id":
        tid = (msg.text or "").strip().lower().replace(" ", "_")
        context.user_data["new_ft_id"] = tid
        context.user_data["step"]      = "addft_emoji"
        await msg.reply_text(f"✅ المعرف: `{tid}`\n\nأرسل الإيموجي:", parse_mode="Markdown")

    elif step == "addft_emoji":
        context.user_data["new_ft_emoji"] = (msg.text or "").strip()
        context.user_data["step"]         = "addft_name"
        await msg.reply_text("✅ أرسل الاسم بالعربية:")

    elif step == "addft_name":
        tid   = context.user_data.get("new_ft_id", "")
        emoji = context.user_data.get("new_ft_emoji", "📦")
        name  = (msg.text or "").strip()
        await db.add_file_type(tid, name, emoji)
        context.user_data.clear()
        await msg.reply_text(f"✅ تمت إضافة النوع: {emoji} {name}")

    # ── Add force sub ──────────────────────────────────
    elif step == "addsub_type":
        try:
            parts = [p.strip() for p in (msg.text or "").split("|")]
            if len(parts) < 4:
                raise ValueError
            ttype, tname, tid, tlink = parts[0], parts[1], parts[2], parts[3]
            await db.add_force_sub(tid, tname, ttype, tlink)
            context.user_data.clear()
            icon = "📢" if ttype == "channel" else "🤖"
            await msg.reply_text(f"✅ تمت إضافة الاشتراك الإجباري:\n{icon} {tname}")
        except Exception:
            await msg.reply_text(
                "❌ صيغة خاطئة! أرسل:\n\n"
                "`نوع | الاسم | المعرف | الرابط`\n\n"
                "مثال:\n`channel | قناتي | @mychannel | https://t.me/mychannel`",
                parse_mode="Markdown"
            )

    # ── Broadcast ──────────────────────────────────────
    elif step == "broadcast":
        context.user_data.clear()
        user_ids = await db.get_all_user_ids()
        sent = failed = 0
        for uid in user_ids:
            try:
                await _forward_any(context, uid, msg)
                sent += 1
            except Exception:
                failed += 1
        await msg.reply_text(
            f"📣 انتهى البث!\n✅ نجح: {sent}\n❌ فشل: {failed}"
        )

    # ── Publish: receive file ──────────────────────────
    elif step == "pub_file":
        file_id = file_name = file_caption = ""
        if msg.document:
            file_id      = msg.document.file_id
            file_name    = msg.document.file_name or "file"
            file_caption = msg.caption or ""
        elif msg.photo:
            file_id      = msg.photo[-1].file_id
            file_name    = "photo.jpg"
            file_caption = msg.caption or ""
        elif msg.video:
            file_id      = msg.video.file_id
            file_name    = msg.video.file_name or "video.mp4"
            file_caption = msg.caption or ""
        elif msg.audio:
            file_id      = msg.audio.file_id
            file_name    = msg.audio.file_name or "audio.mp3"
            file_caption = msg.caption or ""
        else:
            await msg.reply_text("❌ أرسل ملفاً صحيحاً.")
            return

        ft_id   = context.user_data.get("current_type", "general")
        pending = await db.get_pending(user.id)
        files   = pending.get("files", [])
        files.append({
            "file_id":      file_id,
            "file_type":    ft_id,
            "file_name":    file_name,
            "file_caption": file_caption,
        })
        await db.update_pending(user.id, {"files": files})

        fts = await db.get_file_types()
        ft  = next((f for f in fts if f["id"] == ft_id), {"emoji": "📦", "name": ft_id})
        await msg.reply_text(
            f"✅ تم إضافة: {ft['emoji']} {file_name}\n\n"
            f"📦 إجمالي الملفات: {len(files)}\n\n"
            "اختر نوع ملف آخر أو اضغط ✅ انتهيت:",
            reply_markup=kb.publish_type_menu(fts)
        )
        context.user_data["step"] = "pub_type"

    # ── Publish: logo ──────────────────────────────────
    elif step == "pub_logo":
        if msg.photo:
            await db.update_pending(user.id, {"logo_file_id": msg.photo[-1].file_id})
            context.user_data["step"] = "pub_title"
            await msg.reply_text(
                "✅ تم حفظ الشعار!\n\n✏️ أرسل عنوان المنشور:\n_(أو `-` لتخطيه)_",
                reply_markup=kb.cancel_btn()
            )
        else:
            await msg.reply_text("❌ أرسل صورة أو اضغط (بدون شعار).")

    # ── Publish: title ─────────────────────────────────
    elif step == "pub_title":
        title = "" if (msg.text or "").strip() == "-" else (msg.text or "").strip()
        await db.update_pending(user.id, {"title": title})
        context.user_data["step"] = "pub_channel"

        admin    = await db.get_admin(user.id)
        channels = await db.get_all_channels()
        is_main  = await db.is_main_admin(user.id)
        if not is_main and admin and admin.get("allowed_channels"):
            channels = [c for c in channels if c["channel_id"] in admin["allowed_channels"]]

        if not channels:
            await msg.reply_text("❌ لا توجد قنوات.")
            return

        await msg.reply_text(
            "📢 اختر القناة للنشر:",
            reply_markup=kb.publish_channel_menu(channels, is_main)
        )

    # ── Publish: caption ───────────────────────────────
    elif step == "pub_caption":
        caption = "" if (msg.text or "").strip() == "-" else (msg.text or "").strip()
        await db.update_pending(user.id, {"caption": caption})

        pending = await db.get_pending(user.id)
        files   = pending.get("files", [])
        all_fts = await db.get_file_types()
        ft_map  = ft_map_from_list(all_fts)

        preview = build_post_text(
            pending.get("title", ""),
            caption,
            files,
            ft_map
        )
        await msg.reply_text(
            f"📋 *معاينة المنشور:*\n\n{preview}\n\n"
            "هل تريد النشر؟",
            parse_mode="Markdown",
            reply_markup=kb.publish_confirm_menu()
        )
        context.user_data["step"] = "pub_confirm"


# ════════════════════════════════════════════════════════
#  Commands
# ════════════════════════════════════════════════════════
async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await db.is_main_admin(update.effective_user.id):
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
        tid = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ معرف غير صحيح.")
        return

    channels = args[1].split(",") if len(args) > 1 else []
    try:
        chat  = await context.bot.get_chat(tid)
        name  = chat.full_name or str(tid)
        uname = chat.username or ""
    except Exception:
        name  = str(tid)
        uname = ""

    await db.add_admin(tid, uname, name, update.effective_user.id, channels)
    ch_text = "، ".join(channels) if channels else "جميع القنوات"
    await update.message.reply_text(
        f"✅ تمت إضافة المشرف:\n👤 {name}\n🆔 `{tid}`\n📢 {ch_text}",
        parse_mode="Markdown"
    )


async def removeadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await db.is_main_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("الاستخدام: `/removeadmin [user_id]`", parse_mode="Markdown")
        return
    try:
        tid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ معرف غير صحيح.")
        return
    if tid == MAIN_ADMIN_ID:
        await update.message.reply_text("❌ لا يمكن حذف المشرف الرئيسي.")
        return
    await db.remove_admin(tid)
    await update.message.reply_text(f"✅ تم حذف المشرف `{tid}`.", parse_mode="Markdown")


async def addchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await db.is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "الاستخدام: `/addchannel @username_أو_ID الاسم`\n\n"
            "⚠️ أضف البوت كمشرف في القناة أولاً!",
            parse_mode="Markdown"
        )
        return
    cid  = context.args[0]
    name = " ".join(context.args[1:])
    try:
        chat  = await context.bot.get_chat(cid)
        name  = chat.title or name
        uname = chat.username or ""
        cid   = str(chat.id)
    except Exception:
        uname = ""
    await db.add_channel(cid, name, uname, update.effective_user.id)
    await update.message.reply_text(
        f"✅ تمت إضافة القناة: *{name}*\n🆔 `{cid}`",
        parse_mode="Markdown"
    )


async def addfiletype_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await db.is_main_admin(update.effective_user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "الاستخدام: `/addfiletype id emoji الاسم`",
            parse_mode="Markdown"
        )
        return
    await db.add_file_type(
        context.args[0].lower(),
        " ".join(context.args[2:]),
        context.args[1]
    )
    await update.message.reply_text(
        f"✅ تمت الإضافة: {context.args[1]} {' '.join(context.args[2:])}"
    )


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await db.is_main_admin(update.effective_user.id):
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
#  Helper: forward any message type
# ════════════════════════════════════════════════════════
async def _forward_any(context, chat_id: int, msg):
    if msg.photo:
        await context.bot.send_photo(
            chat_id=chat_id, photo=msg.photo[-1].file_id, caption=msg.caption or "")
    elif msg.document:
        await context.bot.send_document(
            chat_id=chat_id, document=msg.document.file_id, caption=msg.caption or "")
    elif msg.video:
        await context.bot.send_video(
            chat_id=chat_id, video=msg.video.file_id, caption=msg.caption or "")
    elif msg.audio:
        await context.bot.send_audio(
            chat_id=chat_id, audio=msg.audio.file_id, caption=msg.caption or "")
    elif msg.voice:
        await context.bot.send_voice(chat_id=chat_id, voice=msg.voice.file_id)
    elif msg.sticker:
        await context.bot.send_sticker(chat_id=chat_id, sticker=msg.sticker.file_id)
    elif msg.animation:
        await context.bot.send_animation(
            chat_id=chat_id, animation=msg.animation.file_id, caption=msg.caption or "")
    else:
        await context.bot.send_message(chat_id=chat_id, text=msg.text or "")
