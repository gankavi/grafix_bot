from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
import os
import re
import time
from collections import defaultdict
from dotenv import load_dotenv

# 🔄 Load .env (local dev only; Render-ல் ENV settings UI-ல add செய்ய வேண்டும்)
load_dotenv()

# ✅ Environment variables (Render / local .env)
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
owner_id = int(os.getenv("OWNER_ID", "250598921"))
allowed_group_id = int(os.getenv("GROUP_ID", "-1002250377216"))

# 🔧 Pyrogram Client init
app = Client("grafix_guard_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# 🛡️ Configurations
bad_words = ["badword1", "badword2"]
flood_limit = 5
time_window = 10
user_messages = defaultdict(list)
warnings = defaultdict(int)

# 🔐 Group Restriction Decorator
def only_in_group(func):
    def wrapper(client, message: Message):
        if message.chat.id != allowed_group_id:
            message.reply("⛔ This bot is not allowed to be used in this group.")
            return
        return func(client, message)
    return wrapper

# 📩 Message Moderation
@app.on_message(filters.group & filters.text)
@only_in_group
def moderate(client, message: Message):
    text = message.text.lower()
    user_id = message.from_user.id
    chat_id = message.chat.id
    now = time.time()

    # 🔗 Block unwanted links
    if re.search(r"(https?://|t\.me/|discord\.gg|bit\.ly)", text):
        message.delete()
        return

    # 🤬 Bad word filter
    if any(word in text for word in bad_words):
        message.delete()
        return

    # 🚫 Flood control
    user_messages[user_id] = [t for t in user_messages[user_id] if now - t < time_window]
    user_messages[user_id].append(now)

    if len(user_messages[user_id]) > flood_limit:
        warnings[user_id] += 1
        message.reply_text(f"⚠️ Flood warning {warnings[user_id]}/3.")
        if warnings[user_id] >= 3:
            try:
                app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
                message.reply("🔇 User muted.")
            except Exception as e:
                message.reply(f"❌ Failed to mute user: {e}")

# 🧑‍⚖️ Admin Commands (only for owner)
@app.on_message(filters.command(["ban", "mute", "warn"]) & filters.user(owner_id))
@only_in_group
def admin_tools(client, message: Message):
    if not message.reply_to_message:
        message.reply("🔁 Reply to a user's message.")
        return

    target_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    cmd = message.command[0]

    if cmd == "ban":
        app.ban_chat_member(chat_id, target_id)
        message.reply("🚫 User banned.")
    elif cmd == "mute":
        app.restrict_chat_member(chat_id, target_id, ChatPermissions(can_send_messages=False))
        message.reply("🔇 User muted.")
    elif cmd == "warn":
        warnings[target_id] += 1
        message.reply(f"⚠️ User warned. Total warnings: {warnings[target_id]}")

# ▶️ Run the bot
app.run()
