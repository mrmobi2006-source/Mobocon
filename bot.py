import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)
from config import BOT_TOKEN
from database import init_db
from handlers.user_handlers import (
    start, check_sub_callback, handle_react,
    handle_getfile_btn, handle_user_filetype
)
from handlers.admin_handlers import (
    admin_cmd, admin_callback, handle_message,
    addadmin_cmd, removeadmin_cmd, addchannel_cmd,
    addfiletype_cmd, broadcast_cmd
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(app: Application):
    await init_db()
    # Remove all public commands — users see nothing
    await app.bot.set_my_commands([])
    logger.info("✅ MOBO TUNNEL Bot ready")


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # ── User ──────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_sub_callback,  pattern=r"^check_sub$"))
    app.add_handler(CallbackQueryHandler(handle_react,        pattern=r"^react_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_getfile_btn,  pattern=r"^getfile_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_user_filetype, pattern=r"^userget_\d+_.+$"))

    # ── Admin callbacks ────────────────────────────────
    app.add_handler(CallbackQueryHandler(
        admin_callback,
        pattern=r"^(adm_|pub_|del|editft_)"
    ))

    # ── Admin commands ─────────────────────────────────
    app.add_handler(CommandHandler("admin",       admin_cmd))
    app.add_handler(CommandHandler("addadmin",    addadmin_cmd))
    app.add_handler(CommandHandler("removeadmin", removeadmin_cmd))
    app.add_handler(CommandHandler("addchannel",  addchannel_cmd))
    app.add_handler(CommandHandler("addfiletype", addfiletype_cmd))
    app.add_handler(CommandHandler("broadcast",   broadcast_cmd))

    # ── Admin message flows (files, text, photos…) ────
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.Document.ALL | filters.PHOTO |
         filters.VIDEO | filters.AUDIO | filters.VOICE |
         filters.ANIMATION | filters.Sticker.ALL) & ~filters.COMMAND,
        handle_message
    ))

    logger.info("🚀 MOBO TUNNEL Bot started!")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
