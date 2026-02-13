import asyncio
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import pytz

# ===== TELETHON (USER ACCOUNT) =====
api_id = 38073577
api_hash = "9cc605c61a1c5c136dde8ffd82827917"
UPBIT_CHANNEL = "upbit_news"

# ===== BOT TOKEN =====
BOT_TOKEN = "8414741935:AAHrQxNw9iFHZxf-5syA6uG2lFyJzKVHQ_A"

# ===== TIMEZONE =====
IST = pytz.timezone("Asia/Kolkata")

# ===== STORE USERS =====
subscribed_users = set()

# ================= BOT COMMAND =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribed_users.add(chat_id)

    await update.message.reply_text(
        "✅ You are now subscribed to Upbit announcement alerts!"
    )

# ================= TELETHON LISTENER =================

async def telethon_listener(bot_app):
    client = TelegramClient("session_name", api_id, api_hash)
    await client.start()

    print("Listening for announcements...")

    @client.on(events.NewMessage(chats=UPBIT_CHANNEL))
    async def handler(event):
        message_text = event.raw_text
        now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

        alert_message = f"""
🚨 NEW UPBIT ANNOUNCEMENT 🚨

🕒 Received (IST): {now_ist}

📢 Message:
{message_text}
"""

        # Send to all subscribed users
        for user in subscribed_users:
            try:
                await bot_app.bot.send_message(chat_id=user, text=alert_message)
            except:
                pass

        print("Alert sent to users at:", now_ist)

    await client.run_until_disconnected()

# ================= MAIN =================

async def main():
    # Start Telegram Bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))

    # Run both bot + telethon together
    await bot_app.initialize()
    await bot_app.start()

    await asyncio.gather(
        telethon_listener(bot_app),
        bot_app.updater.start_polling()
    )

asyncio.run(main())
