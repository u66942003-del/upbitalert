

"""
Telegram Channel Monitor - Forwards messages from a channel to your bot
Prerequisites:
1. Install: pip install telethon --break-system-packages
2. Get API credentials from https://my.telegram.org/apps
3. Get your bot token from @BotFather
4. Get the channel username or ID you want to monitor
"""

from telethon import TelegramClient, events
import asyncio
import requests



# Your chat ID where you want to receive alerts (use @userinfobot to get your chat ID)


"""
Telegram Channel Monitor - Cloud Ready Version
Uses bot token for authentication (no phone number needed)
Perfect for deployment on cloud servers, Heroku, AWS, etc.

Prerequisites:
1. Install: pip install telethon requests python-dotenv --break-system-packages
2. Create 2 bots with @BotFather:
   - Bot 1: Monitoring bot (will read the channel)
   - Bot 2: Alert bot (will send you messages)
3. Add the monitoring bot to the channel as admin
4. Set environment variables or use .env file
"""

from telethon import TelegramClient, events
import asyncio
import requests
import os




# ============== CONFIGURATION ==============


"""
Multi-User Telegram Channel Monitor - Cloud Ready
Users can start/stop monitoring by messaging the alert bot
No manual chat ID configuration needed!

Prerequisites:
1. Install: pip install telethon requests python-dotenv --break-system-packages
2. Create 2 bots with @BotFather:
   - Bot 1: Monitoring bot (reads the channel)
   - Bot 2: Alert bot (sends messages to users)
3. Add monitoring bot to channel as admin
"""

from telethon import TelegramClient, events
import asyncio
import requests
import os
import json
from datetime import datetime

# Load environment variables





ALERT_CHAT_ID = '945859539'  # e.g., '123456789'

API_ID = 38073577
API_HASH = "9cc605c61a1c5c136dde8ffd82827917"
USER_BOT_TOKEN = "8414741935:AAHrQxNw9iFHZxf-5syA6uG2lFyJzKVHQ_A"
ALERT_BOT_TOKEN = "8414741935:AAHrQxNw9iFHZxf-5syA6uG2lFyJzKVHQ_A"
SOURCE_CHANNEL = "upbit_news"

# File to store user subscriptions
USERS_FILE = 'subscribers.json'


# ============================================


class MultiUserChannelMonitor:
    def __init__(self, api_id, api_hash, user_bot_token, alert_bot_token):
        self.client = TelegramClient('bot_session', api_id, api_hash)
        self.user_bot_token = user_bot_token
        self.alert_bot_token = alert_bot_token
        self.subscribers = self.load_subscribers()
        self.bot_username = None

    def load_subscribers(self):
        """Load subscriber list from file"""
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_subscribers(self):
        """Save subscriber list to file"""
        with open(USERS_FILE, 'w') as f:
            json.dump(self.subscribers, f, indent=2)

    def add_subscriber(self, chat_id, username=None):
        """Add a new subscriber"""
        chat_id_str = str(chat_id)
        if chat_id_str not in self.subscribers:
            self.subscribers[chat_id_str] = {
                'username': username,
                'subscribed_at': datetime.now().isoformat(),
                'active': True
            }
            self.save_subscribers()
            return True
        else:
            self.subscribers[chat_id_str]['active'] = True
            self.save_subscribers()
            return False

    def remove_subscriber(self, chat_id):
        """Remove a subscriber"""
        chat_id_str = str(chat_id)
        if chat_id_str in self.subscribers:
            self.subscribers[chat_id_str]['active'] = False
            self.save_subscribers()
            return True
        return False

    def get_active_subscribers(self):
        """Get list of active subscriber chat IDs"""
        return [chat_id for chat_id, data in self.subscribers.items()
                if data.get('active', True)]

    async def send_to_user(self, chat_id, text, parse_mode='HTML'):
        """Send message to a specific user"""
        url = f'https://api.telegram.org/bot{self.alert_bot_token}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error sending to user {chat_id}: {e}")
            return None

    async def send_media_to_user(self, chat_id, file_path, caption=''):
        """Send media to a specific user"""
        url = f'https://api.telegram.org/bot{self.alert_bot_token}/sendPhoto'
        data = {
            'chat_id': chat_id,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        try:
            with open(file_path, 'rb') as photo:
                files = {'photo': photo}
                response = requests.post(url, data=data, files=files, timeout=30)
            return response.json()
        except Exception as e:
            print(f"Error sending media to user {chat_id}: {e}")
            return None

    async def broadcast_alert(self, text):
        """Send alert to all active subscribers"""
        subscribers = self.get_active_subscribers()
        print(f"Broadcasting to {len(subscribers)} subscribers...")

        tasks = []
        for chat_id in subscribers:
            tasks.append(self.send_to_user(chat_id, text))

        # Send all messages concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_media(self, file_path, caption=''):
        """Send media to all active subscribers"""
        subscribers = self.get_active_subscribers()

        tasks = []
        for chat_id in subscribers:
            tasks.append(self.send_media_to_user(chat_id, file_path, caption))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def get_bot_username(self):
        """Get the alert bot's username"""
        url = f'https://api.telegram.org/bot{self.alert_bot_token}/getMe'
        try:
            response = requests.get(url)
            data = response.json()
            if data.get('ok'):
                return data['result'].get('username')
        except:
            pass
        return None

    async def handle_bot_commands(self):
        """Handle commands sent to the alert bot"""
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters

        app = Application.builder().token(self.alert_bot_token).build()

        async def start_command(update: Update, context):
            """Handle /start command"""
            chat_id = update.effective_chat.id
            username = update.effective_user.username

            is_new = self.add_subscriber(chat_id, username)

            if is_new:
                await update.message.reply_text(
                    f"✅ <b>Welcome!</b>\n\n"
                    f"You are now subscribed to alerts from:\n"
                    f"<code>{SOURCE_CHANNEL}</code>\n\n"
                    f"📊 Active subscribers: {len(self.get_active_subscribers())}\n\n"
                    f"Commands:\n"
                    f"• /start - Subscribe to alerts\n"
                    f"• /stop - Unsubscribe from alerts\n"
                    f"• /status - Check your subscription status",
                    parse_mode='HTML'
                )
                print(f"✓ New subscriber: {username} ({chat_id})")
            else:
                await update.message.reply_text(
                    f"🔔 <b>Reactivated!</b>\n\n"
                    f"Your alerts are now active again.\n"
                    f"Monitoring: <code>{SOURCE_CHANNEL}</code>",
                    parse_mode='HTML'
                )
                print(f"✓ Reactivated subscriber: {username} ({chat_id})")

        async def stop_command(update: Update, context):
            """Handle /stop command"""
            chat_id = update.effective_chat.id

            if self.remove_subscriber(chat_id):
                await update.message.reply_text(
                    "🔕 <b>Unsubscribed</b>\n\n"
                    "You will no longer receive alerts.\n"
                    "Send /start anytime to subscribe again.",
                    parse_mode='HTML'
                )
                print(f"✓ User unsubscribed: {chat_id}")
            else:
                await update.message.reply_text(
                    "You are not currently subscribed.",
                    parse_mode='HTML'
                )

        async def status_command(update: Update, context):
            """Handle /status command"""
            chat_id = str(update.effective_chat.id)

            if chat_id in self.subscribers and self.subscribers[chat_id].get('active'):
                sub_data = self.subscribers[chat_id]
                subscribed_at = sub_data.get('subscribed_at', 'Unknown')

                await update.message.reply_text(
                    f"✅ <b>Status: Active</b>\n\n"
                    f"📺 Monitoring: <code>{SOURCE_CHANNEL}</code>\n"
                    f"📅 Subscribed: {subscribed_at[:10]}\n"
                    f"👥 Total subscribers: {len(self.get_active_subscribers())}",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ <b>Status: Not Subscribed</b>\n\n"
                    "Send /start to subscribe to alerts.",
                    parse_mode='HTML'
                )

        # Add command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("stop", stop_command))
        app.add_handler(CommandHandler("status", status_command))

        # Start polling in background
        print("✓ Bot command handler started")
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=['message'])

    async def start_monitoring(self, channel_username):
        """Start monitoring the channel"""
        # Start the monitoring client
        await self.client.start(bot_token=self.user_bot_token)

        # Get bot username
        self.bot_username = await self.get_bot_username()

        print("=" * 70)
        print("✅ MULTI-USER TELEGRAM CHANNEL MONITOR STARTED")
        print("=" * 70)
        print(f"📺 Monitoring: {channel_username}")
        print(f"🤖 Alert Bot: @{self.bot_username}")
        print(f"👥 Active Subscribers: {len(self.get_active_subscribers())}")
        print("=" * 70)
        print(f"\n💡 Users can subscribe by messaging @{self.bot_username} with /start")
        print("🛑 Press Ctrl+C to stop\n")

        # Start bot command handler in background
        asyncio.create_task(self.handle_bot_commands())

        @self.client.on(events.NewMessage(chats=channel_username))
        async def message_handler(event):
            """Handle new messages from the channel"""
            message = event.message

            # Get message timestamp
            msg_time = message.date
            time_str = msg_time.strftime('%Y-%m-%d %H:%M:%S')
            time_display = msg_time.strftime('%I:%M %p')  # 12-hour format
            date_display = msg_time.strftime('%B %d, %Y')  # Month Day, Year

            # Build alert message with timestamp
            alert_text = (
                f"🔔 <b>New Alert from {channel_username}</b>\n\n"
                f"🕐 <b>Time:</b> {time_str}\n"
               
            )

            if message.text:
                # Truncate very long messages
                text = message.text[:2000] + "..." if len(message.text) > 2000 else message.text
                alert_text += f"<b>Message:</b>\n{text}\n\n"

            alert_text += f"━━━━━━━━━━━━━━━━━━\n"
            alert_text += f"⏰ Received at: {time_str} UTC"

            # Broadcast to all subscribers
            await self.broadcast_alert(alert_text)

            # Handle media
            if message.media:
                try:
                    print("📥 Downloading media...")
                    path = await message.download_media()
                    if path:
                        caption = (
                            f"📸 Media from {channel_username}\n"
                            f"⏰ {time_display} | {date_display}"
                        )
                        await self.broadcast_media(path, caption)
                        # Clean up
                        os.remove(path)
                        print("✓ Media sent to all subscribers")
                except Exception as e:
                    print(f"Error handling media: {e}")

            subscriber_count = len(self.get_active_subscribers())
            print(f"✓ Alert broadcasted to {subscriber_count} users | {time_str}")

        # Keep running
        await self.client.run_until_disconnected()


def validate_config():
    """Validate configuration"""
    errors = []

    if API_ID == 'YOUR_API_ID' or not API_ID:
        errors.append("TELEGRAM_API_ID not set")

    if API_HASH == 'YOUR_API_HASH' or not API_HASH:
        errors.append("TELEGRAM_API_HASH not set")

    if USER_BOT_TOKEN == 'YOUR_MONITORING_BOT_TOKEN' or not USER_BOT_TOKEN:
        errors.append("MONITORING_BOT_TOKEN not set")

    if ALERT_BOT_TOKEN == 'YOUR_ALERT_BOT_TOKEN' or not ALERT_BOT_TOKEN:
        errors.append("ALERT_BOT_TOKEN not set")

    if SOURCE_CHANNEL == '@your_channel_username' or not SOURCE_CHANNEL:
        errors.append("SOURCE_CHANNEL not set")

    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        print("\n💡 Set these as environment variables or in .env file")
        return False

    return True


async def main():
    """Main function"""
    if not validate_config():
        return

    print("🚀 Starting Multi-User Channel Monitor...\n")

    monitor = MultiUserChannelMonitor(
        api_id=API_ID,
        api_hash=API_HASH,
        user_bot_token=USER_BOT_TOKEN,
        alert_bot_token=ALERT_BOT_TOKEN
    )

    try:
        await monitor.start_monitoring(SOURCE_CHANNEL)
    except KeyboardInterrupt:
        print("\n\n✓ Monitor stopped gracefully")
        print(f"📊 Total subscribers: {len(monitor.subscribers)}")
        print(f"👥 Active subscribers: {len(monitor.get_active_subscribers())}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Install required package for bot commands
    try:
        import telegram
    except ImportError:
        print("Installing python-telegram-bot...")
        os.system("pip install python-telegram-bot --break-system-packages")

    asyncio.run(main())

