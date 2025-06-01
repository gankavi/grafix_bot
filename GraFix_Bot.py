from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
import re
import time
from collections import defaultdict

# ✅ Credentials
api_id = 123456  # உங்கள் API ID
api_hash = "your_api_hash"
bot_token = "your_actual_token"
owner_id = 250598921
allowed_group_id = -1001234567890  # உங்கள் group ID (negative number)

app = Client("secured_guard_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# 🔧 Configs
bad_words = ["badword1", "badword2"]
flood_limit = 5
time_window = 10
user_messages = defaultdict(list)
warnings = defaultdict(int)

# 🔐 Access Control Decorator
def only_in_group(func):
    def wrapper(client, message: Message):
        if message.chat.id != allowed_group_id:
            message.reply("⛔ This bot is not allowed to be used in this group.")
            return
        return func(client, message)
    return wrapper

# ✉️ Main Message Filter
@app.on_message(filters.group & filters.text)
@only_in_group
def moderate(client, message: Message):
    text = message.text.lower()
    user_id = message.from_user.id
    chat_id = message.chat.id
    now = time.time()

    if re.search(r"(https?://|t\.me/|discord\.gg|bit\.ly)", text):
        message.delete()
        return

    if any(word in text for word in bad_words):
        message.delete()
        return

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

# 🛠 Admin Tools (only owner)
@app.on_message(filters.command(["ban", "mute", "warn"]) & filters.user(owner_id))
@only_in_group
def admin_tools(client, message: Message):
    if not message.reply_to_message:
        message.reply("Reply to a user’s message.")
        return

    target = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    cmd = message.command[0]

    if cmd == "ban":
        app.ban_chat_member(chat_id, target)
        message.reply("🚫 User banned.")
    elif cmd == "mute":
        app.restrict_chat_member(chat_id, target, ChatPermissions(can_send_messages=False))
        message.reply("🔇 User muted.")
    elif cmd == "warn":
        warnings[target] += 1
        message.reply(f"⚠️ Warned. Total: {warnings[target]}")

app.run()
