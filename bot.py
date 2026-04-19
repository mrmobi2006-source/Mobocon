import logging
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from handlers import admin_handlers, user_handlers, channel_handlers
from database import init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    await init_db()
    logger.info("Database initialized")

def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Admin commands
    application.add_handler(CommandHandler("start", user_handlers.start))
    application.add_handler(CommandHandler("admin", admin_handlers.admin_panel))
    application.add_handler(CommandHandler("addadmin", admin_handlers.add_admin))
    application.add_handler(CommandHandler("removeadmin", admin_handlers.remove_admin))
    application.add_handler(CommandHandler("admins", admin_handlers.list_admins))
    application.add_handler(CommandHandler("stats", admin_handlers.stats))
    application.add_handler(CommandHandler("broadcast", admin_handlers.broadcast))
    application.add_handler(CommandHandler("setdesc", admin_handlers.set_description))
    application.add_handler(CommandHandler("setlogo", admin_handlers.set_logo))
    application.add_handler(CommandHandler("addchannel", admin_handlers.add_channel))
    application.add_handler(CommandHandler("removechannel", admin_handlers.remove_channel))
    application.add_handler(CommandHandler("channels", admin_handlers.list_channels))
    application.add_handler(CommandHandler("publish", admin_handlers.publish_file))
    application.add_handler(CommandHandler("addfiletype", admin_handlers.add_file_type))
    application.add_handler(CommandHandler("filetypes", admin_handlers.list_file_types))
    application.add_handler(CommandHandler("setreactions", admin_handlers.set_reactions_required))
    application.add_handler(CommandHandler("help", user_handlers.help_command))
    application.add_handler(CommandHandler("getfile", user_handlers.get_latest_file))

    # Callback queries
    application.add_handler(CallbackQueryHandler(user_handlers.handle_reaction, pattern="^react_"))
    application.add_handler(CallbackQueryHandler(user_handlers.handle_get_file, pattern="^getfile_"))
    application.add_handler(CallbackQueryHandler(admin_handlers.handle_admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(admin_handlers.handle_publish_callback, pattern="^publish_"))
    application.add_handler(CallbackQueryHandler(admin_handlers.handle_filetype_callback, pattern="^filetype_"))
    application.add_handler(CallbackQueryHandler(admin_handlers.handle_channel_callback, pattern="^channel_"))

    # Message handlers for admin file uploads
    application.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO,
        admin_handlers.handle_file_upload
    ))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.handle_text_input))

    logger.info("MOBO TUNNEL Bot started!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
