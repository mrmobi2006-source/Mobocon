from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
import database as db
import keyboards as kb
from utils import check_force_sub
from config import BOT_NAME, FORCE_SUB_TEXT, NOT_REACTED_TEXT


# ════════════════════════════════════════════════════════
#  /start  —  نقطة الدخول الوحيدة للمستخدمين
#  Deep link:  /start getfile_{group_id}
#              يفتحه زر استلام مباشرة من القناة
# ════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.register_user(user.id, user.username or "", user.full_name or "")

    # ── Bot disabled ───────────────────────────────────
    enabled = await db.get_setting("bot_enabled", "1")
    if enabled != "1" and not await db.is_admin(user.id):
        await update.message.reply_text(
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            "  ⚠️ البوت متوقف مؤقتاً\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n🔄 عد لاحقاً!")
        return

    args = context.args or []

    # ── Deep link: getfile_{group_id} ─────────────────
    # يُفعَّل عندما يضغط المستخدم زر "استلام" في القناة
    if args and args[0].startswith("getfile_"):
        try:
            group_id = int(args[0].split("_")[1])
            await _handle_getfile(update, context, user, group_id)
            return
        except Exception:
            pass

    # ── Checks for regular users ───────────────────────
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
            await update.message.reply_text(
                FORCE_SUB_TEXT.replace("{target_name}", names),
                reply_markup=kb.force_sub_user_buttons(not_joined))
            return

    # ── Welcome ────────────────────────────────────────
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


# ════════════════════════════════════════════════════════
#  Core: معالجة deep link استلام
# ════════════════════════════════════════════════════════
async def _handle_getfile(update, context, user, group_id: int):
    """
    يُستدعى مباشرة عند فتح البوت من زر استلام.
    الترتيب: force sub → ban → vip → تفاعل → ملفات
    """
    if not await db.is_admin(user.id):
        # 1. Ban check
        if await db.is_banned(user.id):
            await update.message.reply_text(
                "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                "      🚫 محظور\n"
                "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                "⛔ أنت محظور من استخدام هذا البوت.")
            return

        # 2. Force sub
        not_joined = await check_force_sub(context.bot, user.id)
        if not_joined:
            names = "، ".join([s["target_name"] for s in not_joined])
            await update.message.reply_text(
                FORCE_SUB_TEXT.replace("{target_name}", names),
                reply_markup=kb.force_sub_user_buttons(not_joined))
            return

        # 3. VIP check — إذا كان النظام مفعّلاً
        vip_enabled = await db.get_setting("vip_enabled", "0") == "1"
        if vip_enabled:
            user_is_vip = await db.is_vip(user.id)
            if not user_is_vip:
                vip_msg = await db.get_setting("vip_message",
                                               "💎 للحصول على VIP تواصل مع @xtt1x")
                await update.message.reply_text(
                    "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                    "      💎 خدمة VIP\n"
                    "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                    "🔒 هذا المحتوى متاح لأعضاء VIP فقط.\n\n"
                    f"{vip_msg}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💎 طلب VIP",
                                             url=f"https://t.me/xtt1x")
                    ]])
                )
                return

    # تحقق من التفاعل
    reacted = await db.has_reacted(user.id, group_id)
    if not reacted:
        await update.message.reply_text(NOT_REACTED_TEXT)
        return

    # اعرض قائمة التطبيقات أو الملفات مباشرة
    await _show_files_menu(context, user.id, group_id, reply_to=update.message)


async def _show_files_menu(context, user_id: int, group_id: int, reply_to=None):
    """عرض قائمة التطبيقات أو أنواع الملفات"""
    group = await db.get_group(group_id)
    if not group:
        text = "❌ الملفات غير موجودة أو انتهت صلاحيتها."
        if reply_to:
            await reply_to.reply_text(text)
        else:
            await context.bot.send_message(chat_id=user_id, text=text)
        return

    all_files = await db.get_files_in_group(group_id)
    if not all_files:
        text = "❌ لا توجد ملفات حالياً."
        if reply_to:
            await reply_to.reply_text(text)
        else:
            await context.bot.send_message(chat_id=user_id, text=text)
        return

    apps_in_group = await db.get_apps_in_group(group_id)
    title = group.get("title") or "الملفات الجديدة"

    if apps_in_group:
        text = (
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"  📦 {title}\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            "📱 اختر التطبيق:"
        )
        markup = kb.user_app_menu(apps_in_group, group_id)
    else:
        types_in_group = list({f["file_type"] for f in all_files})
        all_fts        = await db.get_file_types()
        fts_available  = [ft for ft in all_fts if ft["id"] in types_in_group]

        if len(fts_available) == 1:
            files_filtered = [f for f in all_files if f["file_type"] == fts_available[0]["id"]]
            await _send_files_to_user(context, user_id, group_id, files_filtered, group,
                                       reply_to=reply_to)
            return

        text = (
            "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"  📦 {title}\n"
            "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            "🎯 اختر نوع الملف:"
        )
        markup = kb.user_filetype_menu(fts_available, group_id)

    if reply_to:
        await reply_to.reply_text(text, reply_markup=markup)
    else:
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=markup)


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
        try:
            await query.edit_message_text(
                FORCE_SUB_TEXT.replace("{target_name}", names),
                reply_markup=kb.force_sub_user_buttons(not_joined))
        except Exception:
            await context.bot.send_message(
                chat_id=user.id,
                text=FORCE_SUB_TEXT.replace("{target_name}", names),
                reply_markup=kb.force_sub_user_buttons(not_joined))
        return
    welcome = await db.get_setting("welcome_message")
    welcome = welcome.replace("{name}", user.first_name or "صديقي").replace("{bot}", BOT_NAME)
    try:
        await query.edit_message_text(welcome)
    except Exception:
        await context.bot.send_message(chat_id=user.id, text=welcome)


# ════════════════════════════════════════════════════════
#  ❤️ React button
# ════════════════════════════════════════════════════════
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
        await query.answer("💗 تم تسجيل دعمك! الآن اضغط 💌 لاستلام الملفات.", show_alert=True)
    else:
        await query.answer("✅ سبق ودعمت! اضغط 💌 لاستلام الملفات.", show_alert=True)

    try:
        await query.edit_message_reply_markup(
            reply_markup=kb.channel_post_buttons(group_id, rc, dc, context.bot.username)
        )
    except Exception:
        pass


# ════════════════════════════════════════════════════════
#  userget_{group_id}_{file_type}
# ════════════════════════════════════════════════════════
async def handle_user_filetype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()

    parts    = query.data.split("_", 2)
    group_id = int(parts[1])
    sub      = parts[2]

    if sub == "back":
        apps  = await db.get_apps_in_group(group_id)
        group = await db.get_group(group_id)
        title = group.get("title") if group else "الملفات"
        if apps:
            try:
                await query.edit_message_text(
                    f"┏━━━━━━━━━━━━━━━━━━━━━┓\n  📦 {title}\n"
                    f"┗━━━━━━━━━━━━━━━━━━━━━┛\n\n📱 اختر التطبيق:",
                    reply_markup=kb.user_app_menu(apps, group_id))
            except Exception:
                pass
        return

    # VIP check
    if not await db.is_admin(user.id):
        vip_enabled = await db.get_setting("vip_enabled", "0") == "1"
        if vip_enabled and not await db.is_vip(user.id):
            vip_msg = await db.get_setting("vip_message", "💎 للحصول على VIP تواصل مع @xtt1x")
            try:
                await query.edit_message_text(
                    f"┏━━━━━━━━━━━━━━━━━━━━━┓\n      💎 خدمة VIP\n"
                    f"┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                    f"🔒 هذا المحتوى لأعضاء VIP فقط.\n\n{vip_msg}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💎 طلب VIP", url="https://t.me/xtt1x")
                    ]]))
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


# ════════════════════════════════════════════════════════
#  uapp_{group_id}_{app_id}
# ════════════════════════════════════════════════════════
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

    # VIP check
    if not await db.is_admin(user.id):
        vip_enabled = await db.get_setting("vip_enabled", "0") == "1"
        if vip_enabled and not await db.is_vip(user.id):
            vip_msg = await db.get_setting("vip_message", "💎 للحصول على VIP تواصل مع @xtt1x")
            try:
                await query.edit_message_text(
                    f"┏━━━━━━━━━━━━━━━━━━━━━┓\n      💎 خدمة VIP\n"
                    f"┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                    f"🔒 هذا المحتوى لأعضاء VIP فقط.\n\n{vip_msg}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💎 طلب VIP", url="https://t.me/xtt1x")
                    ]]))
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
            reply_markup=kb.user_app_filetype_menu(fts, group_id, app_id))
    except Exception:
        pass


# ════════════════════════════════════════════════════════
#  uappft_{group_id}_{app_id}_{file_type}
# ════════════════════════════════════════════════════════
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


# ════════════════════════════════════════════════════════
#  Core: إرسال الملفات للمستخدم
# ════════════════════════════════════════════════════════
async def _send_files_to_user(context, user_id: int, group_id: int,
                               files: list, group=None, reply_to=None):
    if not group:
        group = await db.get_group(group_id)

    all_fts = await db.get_file_types()
    ft_map  = {ft["id"]: ft for ft in all_fts}
    logo    = (group.get("logo_file_id") if group else "") or await db.get_setting("bot_logo")

    if logo:
        try:
            cap = (
                "┏━━━━━━━━━━━━━━━━━━━━━┓\n"
                f"  🌐⚡ {BOT_NAME} ⚡🌐\n"
                "┗━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"📦 {group.get('title','الملفات الجديدة')}\n\n"
                "⬇️ ملفاتك جاهزة أدناه"
            )
            if reply_to:
                await reply_to.reply_photo(photo=logo, caption=cap, protect_content=True)
            else:
                await context.bot.send_photo(chat_id=user_id, photo=logo, caption=cap,
                                             protect_content=True)
        except Exception:
            pass

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

    # تحديث عداد الاستلامات في القناة
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
