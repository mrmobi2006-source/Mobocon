from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
import database as db
from config import BOT_NAME, MAIN_ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    welcome = await db.get_setting("welcome_message")
    welcome = welcome.replace("{name}", user.first_name or "صديقي")

    logo = await db.get_setting("bot_logo")

    file_types = await db.get_file_types()
    buttons = []
    for ft in file_types:
        buttons.append([InlineKeyboardButton(
            f"{ft['emoji']} احصل على أحدث {ft['name']}",
            callback_data=f"getfile_type_{ft['id']}"
        )])
    buttons.append([InlineKeyboardButton("📊 إحصائياتي", callback_data="getfile_mystats")])

    markup = InlineKeyboardMarkup(buttons)

    if logo:
        try:
            await update.message.reply_photo(photo=logo, caption=welcome, reply_markup=markup)
            return
        except:
            pass
    await update.message.reply_text(welcome, reply_markup=markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_adm = await db.is_admin(user.id)

    text = f"🤖 *{BOT_NAME} - دليل الاستخدام*\n\n"
    text += "👤 *للمستخدمين:*\n"
    text += "/start - بدء البوت\n"
    text += "/getfile - احصل على أحدث ملف\n"
    text += "/help - المساعدة\n\n"

    if is_adm:
        text += "👑 *للمشرفين:*\n"
        text += "/admin - لوحة التحكم\n"
        text += "/publish - نشر ملف جديد\n"
        text += "/stats - الإحصائيات\n"
        text += "/addchannel [ID] [الاسم] - إضافة قناة\n"
        text += "/channels - قائمة القنوات\n"
        text += "/setdesc [type] [الوصف] - تعديل وصف نوع ملف\n"
        text += "/setlogo - تعيين صورة شعار\n"
        text += "/setreactions [عدد] - عدد التفاعلات المطلوبة\n\n"

    if await db.is_main_admin(user.id):
        text += "🔑 *للمشرف الرئيسي فقط:*\n"
        text += "/addadmin [ID] [القنوات] - إضافة مشرف\n"
        text += "/removeadmin [ID] - حذف مشرف\n"
        text += "/admins - قائمة المشرفين\n"
        text += "/broadcast [الرسالة] - إرسال للجميع\n"
        text += "/addfiletype [id] [emoji] [الاسم] - إضافة نوع ملف\n"
        text += "/filetypes - أنواع الملفات\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def get_latest_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    file_types = await db.get_file_types()
    if not file_types:
        await update.message.reply_text("❌ لا توجد ملفات متاحة حالياً.")
        return

    buttons = [[InlineKeyboardButton(f"{ft['emoji']} {ft['name']}", callback_data=f"getfile_type_{ft['id']}")] for ft in file_types]
    await update.message.reply_text(
        "📂 اختر نوع الملف الذي تريده:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    data = query.data  # react_{file_db_id}
    file_db_id = int(data.split("_")[1])

    already = await db.has_reacted(user.id, file_db_id)
    if already:
        await query.answer("✅ لقد تفاعلت مسبقاً! يمكنك الآن استلام الملف.", show_alert=True)
        return

    await db.add_reaction(user.id, file_db_id)
    count = await db.get_reaction_count(file_db_id)
    required = int(await db.get_setting("reactions_required") or "1")

    await query.answer(f"❤️ شكراً على تفاعلك! إجمالي التفاعلات: {count}", show_alert=True)

    # Update the channel message reaction count if possible
    try:
        file_info = await db.get_file_by_id(file_db_id)
        if file_info and file_info["channel_id"] and file_info["message_id"]:
            # Try to edit the channel message buttons to show updated count
            bot_username = context.bot.username
            new_markup = build_channel_buttons(file_db_id, count, bot_username, file_info["file_type"])
            await context.bot.edit_message_reply_markup(
                chat_id=file_info["channel_id"],
                message_id=file_info["message_id"],
                reply_markup=new_markup
            )
    except Exception as e:
        pass  # Channel message update failed, ignore

async def handle_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    data = query.data
    parts = data.split("_")

    # getfile_type_{type_id} - get latest of type
    if parts[1] == "type":
        file_type = parts[2]
        file_info = await db.get_latest_file(file_type)
        if not file_info:
            await query.answer("❌ لا توجد ملفات من هذا النوع حالياً.", show_alert=True)
            return
    elif parts[1] == "id":
        file_db_id = int(parts[2])
        file_info = await db.get_file_by_id(file_db_id)
        if not file_info:
            await query.answer("❌ الملف غير موجود.", show_alert=True)
            return
    elif parts[1] == "mystats":
        await query.answer()
        await show_user_stats(query, user.id)
        return
    else:
        await query.answer("❌ طلب غير صالح.", show_alert=True)
        return

    required = int(await db.get_setting("reactions_required") or "1")
    reacted = await db.has_reacted(user.id, file_info["id"])

    if not reacted:
        await query.answer(
            f"❌ يجب التفاعل أولاً!\n\nاضغط على زر ❤️ في القناة للتفاعل، ثم عد وحاول مجدداً.",
            show_alert=True
        )
        return

    await query.answer("✅ جاري إرسال الملف إليك...")

    # Send file privately
    file_types_list = await db.get_file_types()
    ft_map = {ft["id"]: ft for ft in file_types_list}
    ft_info = ft_map.get(file_info["file_type"], {"name": "ملف", "emoji": "📦"})

    caption = f"{ft_info['emoji']} *{ft_info['name']}*\n\n"
    if file_info["caption"]:
        caption += file_info["caption"] + "\n\n"
    caption += "⚠️ *ممنوع مشاركة أو تحويل هذا الملف*\n"
    caption += f"🤖 {BOT_NAME}"

    try:
        logo = await db.get_setting("bot_logo")
        if logo:
            await context.bot.send_photo(
                chat_id=user.id,
                photo=logo,
                caption=caption,
                parse_mode="Markdown"
            )

        await context.bot.send_document(
            chat_id=user.id,
            document=file_info["file_id"],
            caption=f"📦 هنا ملفك! من {BOT_NAME}",
            protect_content=True  # Prevents forwarding/saving
        )
    except BadRequest as e:
        if "chat not found" in str(e).lower() or "bot was blocked" in str(e).lower():
            await query.answer("❌ يجب فتح البوت أولاً! اضغط /start في البوت.", show_alert=True)

async def show_user_stats(query, user_id: int):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    reactions = 0
    async with __import__('aiosqlite').connect(__import__('config').DATABASE_URL) as db_conn:
        cur = await db_conn.execute("SELECT COUNT(*) FROM reactions WHERE user_id = ?", (user_id,))
        r = await cur.fetchone()
        reactions = r[0] if r else 0

    text = f"📊 *إحصائياتك في {BOT_NAME}*\n\n"
    text += f"❤️ إجمالي تفاعلاتك: {reactions}\n"
    text += f"\n🤖 استمر في التفاعل للحصول على المزيد من الملفات!"

    await query.message.reply_text(text, parse_mode="Markdown")

def build_channel_buttons(file_db_id: int, reaction_count: int, bot_username: str, file_type: str = "general"):
    """Build the 3-button layout for channel posts"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"⚡ فعّل البوت أولاً",
            url=f"https://t.me/{bot_username}?start=activate"
        )],
        [
            InlineKeyboardButton(f"❤️ تفاعل ({reaction_count})", callback_data=f"react_{file_db_id}"),
            InlineKeyboardButton("📥 استلام الملف", url=f"https://t.me/{bot_username}?start=getfile_{file_db_id}")
        ]
    ])
