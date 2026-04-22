from telegram import Bot
from telegram.error import TelegramError
import database as db


async def check_force_sub(bot: Bot, user_id: int) -> list:
    """
    Returns list of force_sub entries the user has NOT joined yet.
    Empty list = user passed all checks.
    """
    subs = await db.get_force_subs()
    not_joined = []
    for s in subs:
        try:
            member = await bot.get_chat_member(chat_id=s["target_id"], user_id=user_id)
            if member.status in ("left", "kicked", "banned"):
                not_joined.append(s)
        except TelegramError:
            # Can't check = treat as not joined
            not_joined.append(s)
    return not_joined


def ft_map_from_list(fts: list) -> dict:
    return {ft["id"]: ft for ft in fts}


def build_post_text(title: str, caption: str, files: list, ft_map: dict) -> str:
    """Build the channel post text with file list"""
    lines = []

    if title:
        lines.append(f"⚡️ {title}")
        lines.append("┄" * 22)

    if caption:
        lines.append(caption)
        lines.append("")

    # Group files by type
    by_type: dict = {}
    for f in files:
        ftype = f["file_type"]
        by_type.setdefault(ftype, []).append(f)

    for ftype, flist in by_type.items():
        ft = ft_map.get(ftype, {"emoji": "📦", "name": ftype})
        lines.append(f"{ft['emoji']} {ft['name']}:")
        for i, f in enumerate(flist, 1):
            desc = f.get("file_caption") or f.get("file_name") or f"ملف {i}"
            lines.append(f"  {i}. {desc}")
        lines.append("")

    lines.append("┄" * 22)
    lines.append("📌 طريقة الاستلام:")
    lines.append("  1️⃣ فعّل البوت بالضغط على ⚡️")
    lines.append("  2️⃣ ادعمنا بالضغط على 💗")
    lines.append("  3️⃣ اضغط 💌 لاستلام الملفات")
    lines.append("")
    lines.append("⚡ سارع قبل مـدة المـلـفـات!")

    return "\n".join(lines)
