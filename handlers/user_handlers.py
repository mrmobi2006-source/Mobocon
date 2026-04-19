from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
import database as db
import keyboards as kb
from utils import check_force_sub
from config import BOT_NAME, FORCE_SUB_TEXT, NOT_REACTED_TEXT


# ════════════════════════════════════════════════════════
#  /start
# ════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    enabled = await db.get_setting("bot_enabled", "1")
    if enabled != "1" and not await db.is_admin(user.id):
        await update.message.reply_text(
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            "  ⚠️ البوت متوقف مؤقتاً\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            "🔄 عد لاحقاً!"
        )
        return

    args = context.args or []

    # Deep link: getfile_{group_id}
    if args and args[0].startswith("getfile_"):
        try:
            group_id = int(args[0].split("_")[1])
            await handle_receive_files(update, context, user.id, group_id)
            return
        except Exception:
            pass

    # Force sub check (skip for admins)
    if not await db.is_admin(user.id):
        not_joined = await check_force_sub(context.bot, user.id)
        if not_joined:
            names = "، ".join([s["target_name"] for s in not_joined])
            text  = FORCE_SUB_TEXT.replace("{target_name}", names)
            await update.message.reply_text(
                text,
                reply_markup=kb.force_sub_user_buttons(not_joined)
            )
            return

    # Show welcome
    welcome = await db.get_setting("welcome_message")
    welcome = welcome.replace("{name}", user.first_name or "صديقي").replace("{bot}", BOT_NAME)
    logo    = await db.get_setting("bot_logo")

    markup = None
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


# ════════════════════════════════════════════════════════
#  Force sub check button
# ════════════════════════════════════════════════════════
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()

    not_joined = await check_force_sub(context.bot, user.id)
    if not_joined:
        names = "، ".join([s["target_name"] for s in not_joined])
        text  = FORCE_SUB_TEXT.replace("{target_name}", names)
        await query.edit_message_text(
            text,
            reply_markup=kb.force_sub_user_buttons(not_joined)
        )
        return

    # Passed — show welcome
    welcome = await db.get_setting("welcome_message")
    welcome = welcome.replace("{name}", user.first_name or "صديقي").replace("{bot}", BOT_NAME)
    await query.edit_message_text(welcome)


# ════════════════════════════════════════════════════════
#  ❤️ React button (from channel post)
# ════════════════════════════════════════════════════════
async def handle_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    user     = update.effective_user
    group_id = int(query.data.split("_")[1])

    await db.register_user(user.id, user.username or "", user.full_name or "")

    enabled = await db.get_setting("bot_enabled", "1")
    if enabled != "1":
        await query.answer("⚠️ البوت متوقف مؤقتاً.", show_alert=True)
        return

    is_new = await db.add_reaction(user.id, group_id)
    rc = await db.reaction_count(group_id)
    dc = await db.delivery_count(group_id)

    if is_new:
        await query.answer("❤️ تم تسجيل دعمك! الآن اضغط 📥 لاستلام الملفات.", show_alert=True)
    else:
        await query.answer("✅ سبق ودعمت! اضغط 📥 لاستلام الملفات.", show_alert=True)

    bot_username = context.bot.username
    try:
        await query.edit_message_reply_markup(
            reply_markup=kb.channel_post_buttons(group_id, rc, dc, bot_username)
        )
    except Exception:
        pass


# ════════════════════════════════════════════════════════
#  📥 Receive button (from channel post)
# ════════════════════════════════════════════════════════
async def handle_getfile_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    user     = update.effective_user
    group_id = int(query.data.split("_")[1])

    await db.register_user(user.id, user.username or "", user.full_name or "")

    enabled = await db.get_setting("bot_enabled", "1")
    if enabled != "1":
        await query.answer("⚠️ البوت متوقف مؤقتاً.", show_alert=True)
        return

    reacted = await db.has_reacted(user.id, group_id)
    if not reacted:
        await query.answer(NOT_REACTED_TEXT[:200], show_alert=True)
        return

    await query.answer("📥 جاري إرسال الملفات في البوت...")
    try:
        await handle_receive_files_direct(context, user.id, group_id)
    except (Forbidden, BadRequest):
        bot_username = context.bot.username
        await query.answer(
            "⚠️ افتح البوت أولاً ثم حاول مجدداً!",
            show_alert=True
        )


# ════════════════════════════════════════════════════════
#  userget_{group_id}_{file_type}  — user picks file type
# ════════════════════════════════════════════════════════
async def handle_user_filetype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()

    _, group_id_str, file_type = query.data.split("_", 2)
    group_id = int(group_id_str)

    reacted = await db.has_reacted(user.id, group_id)
    if not reacted:
        await query.edit_message_text(NOT_REACTED_TEXT)
        return

    files = await db.get_latest_files_by_type(file_type)
    # Filter to this group only
    files = [f for f in files if f["group_id"] == group_id]

    if not files:
        await query.edit_message_text("❌ لا توجد ملفات من هذا النوع في هذه المجموعة.")
        return

    await query.delete_message()
    await _send_files_to_user(context, user.id, group_id, files)


# ════════════════════════════════════════════════════════
#  Core: show file type selector (deep link entry)
# ════════════════════════════════════════════════════════
async def handle_receive_files(update_or_none, context, user_id: int, group_id: int):
    """Entry from deep link — check force sub, then show type selector"""
    not_joined = await check_force_sub(context.bot, user_id)
    if not_joined:
        names = "، ".join([s["target_name"] for s in not_joined])
        text  = FORCE_SUB_TEXT.replace("{target_name}", names)
        if update_or_none and hasattr(update_or_none, "message") and update_or_none.message:
            await update_or_none.message.reply_text(
                text, reply_markup=kb.force_sub_user_buttons(not_joined))
        else:
            await context.bot.send_message(
                chat_id=user_id, text=text,
                reply_markup=kb.force_sub_user_buttons(not_joined))
        return

    reacted = await db.has_reacted(user_id, group_id)
    if not reacted:
        msg = NOT_REACTED_TEXT
        if update_or_none and hasattr(update_or_none, "message") and update_or_none.message:
            await update_or_none.message.reply_text(msg)
        else:
            await context.bot.send_message(chat_id=user_id, text=msg)
        return

    await handle_receive_files_direct(context, user_id, group_id)


async def handle_receive_files_direct(context, user_id: int, group_id: int):
    """Show file type selector — user picks what they want"""
    group = await db.get_group(group_id)
    if not group:
        await context.bot.send_message(chat_id=user_id, text="❌ المجموعة غير موجودة.")
        return

    all_files = await db.get_files_in_group(group_id)
    if not all_files:
        await context.bot.send_message(chat_id=user_id, text="❌ لا توجد ملفات.")
        return

    # Get unique types in this group
    types_in_group = list({f["file_type"] for f in all_files})
    all_fts        = await db.get_file_types()
    fts_available  = [ft for ft in all_fts if ft["id"] in types_in_group]

    if len(fts_available) == 1:
        # Only one type — send directly
        files_filtered = [f for f in all_files if f["file_type"] == fts_available[0]["id"]]
        await _send_files_to_user(context, user_id, group_id, files_filtered, group)
        return

    # Multiple types — let user choose
    title = group.get("title") or "الملفات الجديدة"
    text  = (
        "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"  📦 {title}\n"
        "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "🎯 اختر نوع الملف الذي تريده:"
    )
    await context.bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=kb.user_filetype_menu(fts_available, group_id)
    )


async def _send_files_to_user(context, user_id: int, group_id: int,
                               files: list, group=None):
    """Actually send files to user privately — clean, no extra text"""
    if not group:
        group = await db.get_group(group_id)

    all_fts = await db.get_file_types()
    ft_map  = {ft["id"]: ft for ft in all_fts}
    logo    = (group.get("logo_file_id") if group else "") or await db.get_setting("bot_logo")

    # Send logo once if available
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

    # Send each file
    for f in files:
        ft   = ft_map.get(f["file_type"], {"emoji": "📦", "name": f["file_type"]})
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

    # Update channel post counters
    rc = await db.reaction_count(group_id)
    dc = await db.delivery_count(group_id)
    bot_username = context.bot.username
    if group and group.get("channel_id"):
        # We stored message_id in publish_groups? No — it's per file.
        # We update via files table
        pass
    try:
        # Try updating the last known message
        from database import DB
        import aiosqlite
        async with aiosqlite.connect(DB) as dbc:
            cur = await dbc.execute(
                "SELECT channel_id, message_id FROM files WHERE group_id=? AND message_id>0 LIMIT 1",
                (group_id,))
            r = await cur.fetchone()
            if r:
                await context.bot.edit_message_reply_markup(
                    chat_id=r[0],
                    message_id=r[1],
                    reply_markup=kb.channel_post_buttons(group_id, rc, dc, bot_username)
                )
    except Exception:
        pass
