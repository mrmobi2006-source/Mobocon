import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8741656871:AAEFrxiiRqvDYBxT7sS7FofW0YSP6VYGJXQ")
BOT_NAME = "MOBO TUNNEL"
BOT_USERNAME = os.getenv("BOT_USERNAME", "mobotunnel_bot")
MAIN_ADMIN_ID = 6154678499
DATABASE_URL = os.getenv("DATABASE_URL", "mobo_tunnel.db")

DEFAULT_WELCOME = "👋 أهلاً {name}!\n\nمرحباً بك في {bot}\n\nتابع قناتنا للحصول على أحدث الملفات!"

DEFAULT_FILE_TYPES = [
    {"id": "internet", "name": " مجاني", "emoji": "🌐"},
    {"id": "youtube",  "name": "يوتيوب",       "emoji": "🎬"},
]
