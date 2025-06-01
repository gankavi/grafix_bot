from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
import os
import re
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# 🔐 Load environment values
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
owner_id = int(os.getenv("OWNER_ID", "250598921"))
allowed_group_id = int(os.getenv("GROUP_ID", "-1002250377216"))

# 🚀 Create Pyrogram App
app = Client("grafix_guard_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# ⚙️ Settings
bad_words = ["idiot", "fool", "nonsense", "badword1", "badword2"]
flood_limit = 5
time_window = 10
user_messages = defaultdict(list)
warnings = defaultdict(int)

# 📜 Group rules text
GROUP_RULES = (
    "📜 *Grafix Prompt Group Rules* 📜\n"
    "1️⃣ நாகரிகமாக பேசவும்.\n"
    "2️⃣ Spam / Flood Strictly Prohibited.\n"
    "3️⃣ தவறான வார்த்தைகள் அனுமதி இல்லை.\n"
)

# 🛑 Only allow in your group
def only_in_group(func):
    def wrapper(client, message: Message):
        if message.chat.id != allowed_group_id:
            message.reply("⛔ இந்த bot Grafix group-க்கு மட்டுமே செயல்படும்.")
            return
        return func(client, message)
    return wrapper

# ✅ /start command
@app.on_message(filters.command("start") & filters.group)
@only_in_group
def start_command(client, message: Message):
    message.reply("👋 வணக்கம்! Grafix Group moderation bot. Rules பார்க்க `/rules` என type செய்யவும்.")

# ✅ /rules command
@app.on_message(filters.command("rules") & filters.group)
@only_in_group
def rules_command(client, message: Message):
    message.reply(GROUP_RULES)

# ✅ "வேண்டும்" keyword reply
@app.on_message(filters.group & filters.text & filters.regex(r"வேண்டும்"))
@only_in_group
def tag_explanation(client, message: Message):
    message.reply("✅ இங்கே உங்கள் tag explanation link:\nhttps://grafix-gfx.blogspot.com/p/styles.html")

# ✅ Admin-only commands
@app.on_message(filters.command(["ban", "mute", "warn"]) & filters.user(owner_id))
@only_in_group
def admin_tools(client, message: Message):
    if not message.reply_to_message:
        message.reply("🔁 User message-ஐ reply செய்து இந்த command பயன்படுத்தவும்.")
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

# ✅ Text moderation
@app.on_message(filters.group & filters.text)
@only_in_group
def moderate_text(client, message: Message):
    text = message.text.lower()
    user_id = message.from_user.id
    chat_id = message.chat.id
    now = time.time()

    # 🔗 Block unwanted links
    if re.search(r"(https?://|t\.me/|bit\.ly|discord\.gg)", text):
        message.delete()
        return

    # 🤬 Bad word filter
    if any(word in text for word in bad_words):
        message.delete()
        warnings[user_id] += 1
        if warnings[user_id] >= 3:
            app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
            message.reply(f"🚫 3 warnings-க்கு பிறகு mute செய்யப்பட்டார்.")
        else:
            message.reply(f"⚠️ Warning {warnings[user_id]}/3")
        return

    # 🚨 Flood control
    user_messages[user_id] = [t for t in user_messages[user_id] if now - t < time_window]
    user_messages[user_id].append(now)
    if len(user_messages[user_id]) > flood_limit:
        message.delete()
        warnings[user_id] += 1
        message.reply(f"🚨 Flood warning {warnings[user_id]}/3")
        if warnings[user_id] >= 3:
            app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
            message.reply(f"🔇 Flood mute applied.")
        return

# ▶️ Run the bot
app.run()
