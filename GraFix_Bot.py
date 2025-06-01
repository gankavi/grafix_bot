from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
import os
import re
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# ENV variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
owner_id = int(os.getenv("OWNER_ID", "250598921"))
allowed_group_id = int(os.getenv("GROUP_ID", "-1002250377216"))

# Pyrogram app
app = Client("grafix_guard_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Configs
bad_words = ["badword1", "badword2"]
flood_limit = 5
time_window = 10
user_messages = defaultdict(list)
warnings = defaultdict(int)

GROUP_RULES = (
    "📜 *Grafix Prompt Group Rules* 📜\n"
    "1️⃣ நாகரிகமாக பேசவும்.\n"
    "2️⃣ Spam / Flood Strictly Prohibited.\n"
    "3️⃣ தவறான வார்த்தைகள் அனுமதி இல்லை.\n"
)

# Restriction decorator
def only_in_group(func):
    def wrapper(client, message: Message):
        if message.chat.id != allowed_group_id:
            message.reply("⛔ This bot is restricted to the official Grafix group only.")
            return
        return func(client, message)
    return wrapper

# 🔹 Start command
@app.on_message(filters.command("start") & filters.group)
@only_in_group
def start_command(client, message: Message):
    message.reply("👋 வணக்கம்! Grafix Group moderation bot. Rules பார்க்க `/rules` type செய்யவும்.")

# 🔹 Rules command
@app.on_message(filters.command("rules") & filters.group)
@only_in_group
def rules_command(client, message: Message):
    message.reply(GROUP_RULES)

# 🔹 Tag explanation request
@app.on_message(filters.group & filters.text & filters.regex(r"வேண்டும்"))
@only_in_group
def tag_explanation(client, message: Message):
    message.reply("✅ இங்கே உங்கள் tag explanation link:\nhttps://grafix-gfx.blogspot.com/p/styles.html")

# 🔸 Admin commands
@app.on_message(filters.command(["ban", "mute", "warn"]) & filters.user(owner_id))
@only_in_group
def admin_tools(client, message: Message):
    if not message.reply_to_message:
        message.reply("🔁 Reply to the user's message to apply action.")
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
        message.reply(f"⚠️ Warning {warnings[target]}/3")

# 🔸 Text monitor (link, flood, badwords)
@app.on_message(filters.group & filters.text)
@only_in_group
def moderate_text(client, message: Message):
    text = message.text.lower()
    user_id = message.from_user.id
    chat_id = message.chat.id
    now = time.time()

    if re.search(r"(https?://|t\.me/|bit\.ly|discord\.gg)", text):
        message.delete()
        return

    if any(word in text for word in bad_words):
        message.delete()
        warnings[user_id] += 1
        if warnings[user_id] >= 3:
            app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
            message.reply(f"🚫 User muted after 3 warnings.")
        else:
            message.reply(f"⚠️ Warning {warnings[user_id]}/3")
        return

    user_messages[user_id] = [t for t in user_messages[user_id] if now - t < time_window]
    user_messages[user_id].append(now)
    if len(user_messages[user_id]) > flood_limit:
        message.delete()
        warnings[user_id] += 1
        message.reply(f"🚨 Flood warning {warnings[user_id]}/3")
        if warnings[user_id] >= 3:
            app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
            message.reply(f"🔇 User auto-muted.")
        return

app.run()
