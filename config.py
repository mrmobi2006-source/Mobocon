import os

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8741656871:AAEFrxiiRqvDYBxT7sS7FofW0YSP6VYGJXQ")
BOT_NAME = "MOBO TUNNEL"
BOT_USERNAME = os.getenv("BOT_USERNAME", "mobotunnel_bot")  # Update after bot creation

# Main Admin ID
MAIN_ADMIN_ID = 6154678499

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "mobo_tunnel.db")

# Default Settings
DEFAULT_DESCRIPTION = {
    "youtube": "🎬 ملف يوتيوب جديد متاح الآن!\n\n✨ محتوى حصري لأعضاء قناتنا\n\n⚡ تفاعل للحصول على الملف مجاناً",
    "internet": "🌐 ملف إنترنت مجاني جديد!\n\n✨ VPN وأدوات الإنترنت الحصرية\n\n⚡ تفاعل للحصول على الملف مجاناً",
    "general": "📦 ملف جديد متاح الآن!\n\n✨ محتوى حصري لأعضاء قناتنا\n\n⚡ تفاعل للحصول على الملف مجاناً"
}

# Emojis
HEART_EMOJI = "❤️"
JOIN_EMOJI = "🔗"
FILE_EMOJI = "📥"
ACTIVATE_EMOJI = "⚡"

# File types
DEFAULT_FILE_TYPES = [
    {"id": "youtube", "name": "يوتيوب", "emoji": "🎬"},
    {"id": "internet", "name": "إنترنت مجاني", "emoji": "🌐"},
]

# Reactions required to get file (default)
DEFAULT_REACTIONS_REQUIRED = 1
