from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
import database as db
import keyboards as kb
from utils import check_force_sub
from config import BOT_NAME, FORCE_SUB_TEXT, NOT_REACTED_TEXT


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    enabled = await db.get_setting("bot_enabled", "1")
    if enabled != "1" and not await db.is_admin(user.id):
        await update.message.reply_text(
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            "  ⚠️ البوت متوقف مؤقتاً\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n🔄 عد لاحقاً!")
        return

    args = context.args or []
    if args and args[0].startswith("getfile_"):
        try:
            group_id = int(args[0].split("_")[1])
            await handle_receive_files(update, context, user.id, group_id)
            return
        except Exception:
            pass

    if not await db.is_admin(user.id):
        if await db.is_banned(user.id):
            await update.message.reply_text(
                "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                "      🚫 محظور\n"
                "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                "⛔ أنت محظور من استخدام هذا البوت.")
            return
        not_joined = await check_force_sub(context.bot, user.id)
        if not_joined:
            names = "، ".join([s["target_name"] for s in not_joined])
            text  = FORCE_SUB_TEXT.replace("{target_name}", names)
            await update.message.reply_text(text, reply_markup=kb.force_sub_user_buttons(not_joined))
            return

    welcome = await db.get_setting("welcome_message")
    welcome = welcome.replace("{name}", user.first_name or "صديقي").replace("{bot}", BOT_NAME)
    logo    = await db.get_setting("bot_logo")
    markup  = None
    if await db.is_admin(user.id):
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("👑 لوحة التحكم", callback_data="adm_main")
        ]])
    try:
        if logo:
            await update.message.reply_photo(photo=logo, caption=welcome, reply_markup=markup)
            return
    except Exception:
        pass
    await update.message.reply_text(welcome, reply_markup=markup)


async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()
    not_joined = await check_force_sub(context.bot, user.id)
    if not_joined:
        names = "، ".join([s["target_name"] for s in not_joined])
        text  = FORCE_SUB_TEXT.replace("{target_name}", names)
        try:
            await query.edit_message_text(text, reply_markup=kb.force_sub_user_buttons(not_joined))
        except Exception:
            await context.bot.send_message(chat_id=user.id, text=text,
                                           reply_markup=kb.force_sub_user_buttons(not_joined))
        return
    welcome = await db.get_setting("welcome_message")
    welcome = welcome.replace("{name}", user.first_name or "صديقي").replace("{bot}", BOT_NAME)
    try:
        await query.edit_message_text(welcome)
    except Exception:
        await context.bot.send_message(chat_id=user.id, text=welcome)


async def handle_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    user     = update.effective_user
    group_id = int(query.data.split("_")[1])
    await db.register_user(user.id, user.username or "", user.full_name or "")

    if await db.get_setting("bot_enabled", "1") != "1":
        await query.answer("⚠️ البوت متوقف مؤقتاً.", show_alert=True)
        return
    if await db.is_banned(user.id):
        await query.answer("🚫 أنت محظور من استخدام البوت.", show_alert=True)
        return

    is_new = await db.add_reaction(user.id, group_id)
    rc = await db.reaction_count(group_id)
    dc = await db.delivery_count(group_id)

    if is_new:
        await query.answer("❤️ تم تسجيل دعمك! الآن اضغط 📥 لاستلام الملفات.", show_alert=True)
    else:
        await query.answer("✅ سبق ودعمت! اضغط 📥 لاستلام الملفات.", show_alert=True)

    try:
        await query.edit_message_reply_markup(
            reply_markup=kb.channel_post_buttons(group_id, rc, dc, context.bot.username)
        )
    except Exception:
        pass


async def handle_getfile_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    زر استلام من القناة:
    - يتحقق من التفاعل
    - يرسل رسالة خاصة للمستخدم مع زر URL يفتح البوت مباشرة
    - هذا هو الحل الوحيد المضمون في تيليجرام (answer_callback_query url= غير مدعوم في كل العملاء)
    """
    query    = update.callback_query
    user     = update.effective_user
    group_id = int(query.data.split("_")[1])
    await db.register_user(user.id, user.username or "", user.full_name or "")

    if await db.get_setting("bot_enabled", "1") != "1":
        await query.answer("⚠️ البوت متوقف مؤقتاً.", show_alert=True)
        return
    if await db.is_banned(user.id):
        await query.answer("🚫 أنت محظور من استخدام البوت.", show_alert=True)
        return

    reacted = await db.has_reacted(user.id, group_id)
    if not reacted:
        await query.answer(NOT_REACTED_TEXT[:200], show_alert=True)
        return

    await query.answer()  # أغلق spinner بدون رسالة

    bot_username = context.bot.username
    deep_link    = f"https://t.me/{bot_username}?start=getfile_{group_id}"

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                f"  🌐⚡ {BOT_NAME} ⚡🌐\n"
                "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                "✅ تم التحقق من تفاعلك!\n"
                "اضغط الزر أدناه لاستلام ملفاتك:"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📥 استلام الملفات ↗️", url=deep_link)
            ]])
        )
    except (Forbidden, BadRequest):
        await query.answer(
            "⚠️ افتح البوت أولاً بالضغط على زر ⚡️ ثم حاول مجدداً.",
            show_alert=True
        )


async def handle_receive_files(update_obj, context, user_id: int, group_id: int):
    not_joined = await check_force_sub(context.bot, user_id)
    if not_joined:
        names  = "، ".join([s["target_name"] for s in not_joined])
        text   = FORCE_SUB_TEXT.replace("{target_name}", names)
        markup = kb.force_sub_user_buttons(not_joined)
        if update_obj and hasattr(update_obj, "message") and update_obj.message:
            await update_obj.message.reply_text(text, reply_markup=markup)
        else:
            await context.bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
        return

    reacted = await db.has_reacted(user_id, group_id)
    if not reacted:
        msg = NOT_REACTED_TEXT
        if update_obj and hasattr(update_obj, "message") and update_obj.message:
            await update_obj.message.reply_text(msg)
        else:
            await context.bot.send_message(chat_id=user_id, text=msg)
        return

    await handle_receive_files_direct(context, user_id, group_id)


async def handle_receive_files_direct(context, user_id: int, group_id: int):
    group = await db.get_group(group_id)
    if not group:
        await context.bot.send_message(chat_id=user_id, text="❌ الملفات غير موجودة أو انتهت صلاحيتها.")
        return

    all_files = await db.get_files_in_group(group_id)
    if not all_files:
        await context.bot.send_message(chat_id=user_id, text="❌ لا توجد ملفات حالياً.")
        return

    apps_in_group = await db.get_apps_in_group(group_id)
    if apps_in_group:
        title = group.get("title") or "الملفات الجديدة"
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                f"  📦 {title}\n"
                "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                "📱 اختر التطبيق:"
            ),
            reply_markup=kb.user_app_menu(apps_in_group, group_id)
        )
        return

    types_in_group = list({f["file_type"] for f in all_files})
    all_fts        = await db.get_file_types()
    fts_available  = [ft for ft in all_fts if ft["id"] in types_in_group]

    if len(fts_available) == 1:
        files_filtered = [f for f in all_files if f["file_type"] == fts_available[0]["id"]]
        await _send_files_to_user(context, user_id, group_id, files_filtered, group)
        return

    title = group.get("title") or "الملفات الجديدة"
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"  📦 {title}\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            "🎯 اختر نوع الملف:"
        ),
        reply_markup=kb.user_filetype_menu(fts_available, group_id)
    )


async def _show_app_or_type_menu(query_obj, context, user_id, group_id, edit=False):
    group         = await db.get_group(group_id)
    apps_in_group = await db.get_apps_in_group(group_id)
    title = group.get("title") if group else "الملفات الجديدة"

    if apps_in_group:
        text   = (f"┏━━━━━━━━━━━━━━━━━━━━━┓\n  📦 {title}\n"
                  f"┗━━━━━━━━━━━━━━━━━━━━━┛\n\n📱 اختر التطبيق:")
        markup = kb.user_app_menu(apps_in_group, group_id)
    else:
        all_files = await db.get_files_in_group(group_id)
        types     = list({f["file_type"] for f in all_files})
        all_fts   = await db.get_file_types()
        fts       = [ft for ft in all_fts if ft["id"] in types]
        text      = (f"┏━━━━━━━━━━━━━━━━━━━━━┓\n  📦 {title}\n"
                     f"┗━━━━━━━━━━━━━━━━━━━━━┛\n\n🎯 اختر نوع الملف:")
        markup    = kb.user_filetype_menu(fts, group_id)

    if edit and query_obj:
        try:
            await query_obj.edit_message_text(text, reply_markup=markup)
            return
        except Exception:
            pass
    await context.bot.send_message(chat_id=user_id, text=text, reply_markup=markup)


async def handle_user_filetype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()

    parts    = query.data.split("_", 2)
    group_id = int(parts[1])
    sub      = parts[2]

    if sub == "back":
        await _show_app_or_type_menu(query, context, user.id, group_id, edit=True)
        return

    reacted = await db.has_reacted(user.id, group_id)
    if not reacted:
        try:
            await query.edit_message_text(NOT_REACTED_TEXT)
        except Exception:
            pass
        return

    apps_in_group = await db.get_apps_in_group(group_id)
    if apps_in_group:
        await _show_app_or_type_menu(query, context, user.id, group_id, edit=True)
        return

    all_files = await db.get_files_in_group(group_id)
    files     = [f for f in all_files if f["file_type"] == sub]
    if not files:
        try:
            await query.edit_message_text("❌ لا توجد ملفات من هذا النوع.")
        except Exception:
            pass
        return

    group = await db.get_group(group_id)
    try:
        await query.delete_message()
    except Exception:
        pass
    await _send_files_to_user(context, user.id, group_id, files, group)


async def handle_user_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()

    _, group_id_str, app_id_str = query.data.split("_", 2)
    group_id = int(group_id_str)
    app_id   = int(app_id_str)

    if await db.is_banned(user.id):
        try:
            await query.edit_message_text("🚫 أنت محظور.")
        except Exception:
            pass
        return

    reacted = await db.has_reacted(user.id, group_id)
    if not reacted:
        try:
            await query.edit_message_text(NOT_REACTED_TEXT)
        except Exception:
            pass
        return

    fts = await db.get_filetypes_in_app(group_id, app_id)
    if not fts:
        try:
            await query.edit_message_text("❌ لا توجد ملفات في هذا التطبيق.")
        except Exception:
            pass
        return

    if len(fts) == 1:
        files = await db.get_files_by_app_and_type(group_id, app_id, fts[0]["id"])
        group = await db.get_group(group_id)
        try:
            await query.delete_message()
        except Exception:
            pass
        await _send_files_to_user(context, user.id, group_id, files, group)
        return

    app = await db.get_app(app_id)
    try:
        await query.edit_message_text(
            f"┏━━━━━━━━━━━━━━━━━━━━━┓\n  {app['emoji']} {app['name']}\n"
            f"┗━━━━━━━━━━━━━━━━━━━━━┛\n\n🎯 اختر نوع الملف:",
            reply_markup=kb.user_app_filetype_menu(fts, group_id, app_id)
        )
    except Exception:
        pass


async def handle_user_app_filetype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()

    parts     = query.data.split("_", 3)
    group_id  = int(parts[1])
    app_id    = int(parts[2])
    file_type = parts[3]

    if await db.is_banned(user.id):
        try:
            await query.edit_message_text("🚫 أنت محظور.")
        except Exception:
            pass
        return

    reacted = await db.has_reacted(user.id, group_id)
    if not reacted:
        try:
            await query.edit_message_text(NOT_REACTED_TEXT)
        except Exception:
            pass
        return

    files = await db.get_files_by_app_and_type(group_id, app_id, file_type)
    if not files:
        try:
            await query.edit_message_text("❌ لا توجد ملفات.")
        except Exception:
            pass
        return

    group = await db.get_group(group_id)
    try:
        await query.delete_message()
    except Exception:
        pass
    await _send_files_to_user(context, user.id, group_id, files, group)


async def _send_files_to_user(context, user_id: int, group_id: int,
                               files: list, group=None):
    if not group:
        group = await db.get_group(group_id)

    all_fts = await db.get_file_types()
    ft_map  = {ft["id"]: ft for ft in all_fts}
    logo    = (group.get("logo_file_id") if group else "") or await db.get_setting("bot_logo")

    if logo:
        try:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=logo,
                caption=(
                    "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                    f"  🌐⚡ {BOT_NAME} ⚡🌐\n"
                    "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                    f"📦 {group.get('title','الملفات الجديدة')}\n\n"
                    "⬇️ ملفاتك جاهزة أدناه"
                )
            )
        except Exception:
            pass

    for f in files:
        ft  = ft_map.get(f["file_type"], {"emoji": "📦", "name": f["file_type"]})
        desc = f.get("file_caption") or f.get("file_name") or "ملف"
        cap  = f"{ft['emoji']} *{ft['name']}*\n`{desc}`"
        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=f["file_id"],
                caption=cap,
                parse_mode="Markdown",
                protect_content=True
            )
        except Exception:
            pass

    await db.add_delivery(user_id, group_id)

    rc = await db.reaction_count(group_id)
    dc = await db.delivery_count(group_id)
    try:
        import aiosqlite
        from database import DB
        async with aiosqlite.connect(DB) as dbc:
            cur = await dbc.execute(
                "SELECT channel_id, message_id FROM files WHERE group_id=? AND message_id>0 LIMIT 1",
                (group_id,))
            r = await cur.fetchone()
            if r:
                await context.bot.edit_message_reply_markup(
                    chat_id=r[0], message_id=r[1],
                    reply_markup=kb.channel_post_buttons(group_id, rc, dc, context.bot.username)
                )
    except Exception:
        pass
