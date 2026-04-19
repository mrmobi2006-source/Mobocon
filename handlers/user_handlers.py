from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden
import database as db
import keyboards as kb
from config import BOT_NAME


# ── /start ────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    # Check if bot is enabled (admins always pass)
    enabled = await db.get_setting("bot_enabled", "1")
    if enabled != "1" and not await db.is_admin(user.id):
        await update.message.reply_text("⚠️ البوت متوقف مؤقتاً. عد لاحقاً!")
        return

    args = context.args or []

    # Deep link: getfile_{file_db_id}
    if args and args[0].startswith("getfile_"):
        try:
            file_db_id = int(args[0].split("_")[1])
            await send_file_to_user(update, context, user.id, file_db_id)
            return
        except Exception:
            pass

    # Normal welcome
    welcome = await db.get_setting("welcome_message")
    welcome = welcome.replace("{name}", user.first_name or "صديقي").replace("{bot}", BOT_NAME)
    logo = await db.get_setting("bot_logo")

    # If admin, show admin panel button too
    if await db.is_admin(user.id):
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("👑 لوحة التحكم", callback_data="adm_main")
        ]])
    else:
        markup = None  # Members have NO buttons — only channel interaction

    if logo:
        try:
            await update.message.reply_photo(photo=logo, caption=welcome, reply_markup=markup)
            return
        except Exception:
            pass
    await update.message.reply_text(welcome, reply_markup=markup)


# ── React button (from channel) ───────────────────────────────────
async def handle_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    enabled = await db.get_setting("bot_enabled", "1")
    if enabled != "1":
        await query.answer("⚠️ البوت متوقف مؤقتاً.", show_alert=True)
        return

    file_db_id = int(query.data.split("_")[1])
    is_new = await db.add_reaction(user.id, file_db_id)

    rc = await db.reaction_count(file_db_id)
    dc = await db.delivery_count(file_db_id)

    if is_new:
        await query.answer("❤️ تم تسجيل تفاعلك! يمكنك الآن استلام الملف.", show_alert=True)
    else:
        await query.answer("✅ سبق وتفاعلت! اضغط زر استلام الملف.", show_alert=True)

    # Update channel post counters silently
    bot_username = context.bot.username
    try:
        new_markup = kb.channel_post_buttons(file_db_id, rc, dc, bot_username)
        await query.edit_message_reply_markup(reply_markup=new_markup)
    except Exception:
        pass


# ── Get file button (from channel) ────────────────────────────────
async def handle_getfile_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    enabled = await db.get_setting("bot_enabled", "1")
    if enabled != "1":
        await query.answer("⚠️ البوت متوقف مؤقتاً.", show_alert=True)
        return

    file_db_id = int(query.data.split("_")[1])
    reacted = await db.has_reacted(user.id, file_db_id)

    if not reacted:
        await query.answer(
            "❌ يجب التفاعل أولاً!\n\nاضغط زر ❤️ تفاعل ثم حاول مجدداً.",
            show_alert=True
        )
        return

    await query.answer("📥 جاري إرسال الملف في البوت...")

    # Redirect user to bot via deep link
    bot_username = context.bot.username
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text="⏳ جاري تجهيز ملفك..."
        )
        await send_file_to_user_direct(context, user.id, file_db_id)
    except (Forbidden, BadRequest):
        # User hasn't started the bot yet — send them the deep link
        await query.answer(
            "⚠️ يجب فتح البوت أولاً!\nاضغط زر (فعّل البوت أولاً) ثم حاول مجدداً.",
            show_alert=True
        )


# ── Core: send file to user ───────────────────────────────────────
async def send_file_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             user_id: int, file_db_id: int):
    """Called from deep link /start getfile_X"""
    reacted = await db.has_reacted(user_id, file_db_id)
    if not reacted:
        await update.message.reply_text(
            "❌ يجب التفاعل في القناة أولاً!\n\nاضغط زر ❤️ ثم عد هنا."
        )
        return
    await send_file_to_user_direct(context, user_id, file_db_id)


async def send_file_to_user_direct(context, user_id: int, file_db_id: int):
    """Send the actual file privately"""
    file_info = await db.get_file_by_id(file_db_id)
    if not file_info:
        await context.bot.send_message(chat_id=user_id, text="❌ الملف غير موجود.")
        return

    ft_list = await db.get_file_types()
    ft_map  = {ft["id"]: ft for ft in ft_list}
    ft      = ft_map.get(file_info["file_type"], {"name": "ملف", "emoji": "📦"})

    caption = f"{ft['emoji']} *{ft['name']}*"
    if file_info["caption"]:
        caption += f"\n\n{file_info['caption']}"
    caption += f"\n\n⚠️ ممنوع مشاركة أو تحويل هذا الملف\n🤖 {BOT_NAME}"

    logo = file_info.get("logo_file_id") or await db.get_setting("bot_logo")

    try:
        if logo:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=logo,
                caption=caption,
                parse_mode="Markdown"
            )
        await context.bot.send_document(
            chat_id=user_id,
            document=file_info["file_id"],
            protect_content=True,
            caption=f"📦 ملفك من {BOT_NAME}"
        )
        await db.add_delivery(user_id, file_db_id)

        # Update delivery counter in channel
        rc = await db.reaction_count(file_db_id)
        dc = await db.delivery_count(file_db_id)
        bot_username = context.bot.username
        if file_info["channel_id"] and file_info["message_id"]:
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=file_info["channel_id"],
                    message_id=file_info["message_id"],
                    reply_markup=kb.channel_post_buttons(file_db_id, rc, dc, bot_username)
                )
            except Exception:
                pass
    except (Forbidden, BadRequest) as e:
        pass
