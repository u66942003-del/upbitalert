import asyncio
import json
import os
import time
import aiohttp

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup, SoupStrainer

# ============================================
# CONFIG
# ============================================
TELEGRAM_BOT_TOKEN = "8414741935:AAHrQxNw9iFHZxf-5syA6uG2lFyJzKVHQ_A"
PATTERN_MATCH = "신규거래지원안내"

TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
NOTICE_URL = "https://upbit.com/service_center/notice"

# ============================================
# FILE UTILS
# ============================================
def load_last_notice():
    if os.path.exists("last_notice.txt"):
        return open("last_notice.txt", encoding="utf-8").read().strip()
    return None


def save_last_notice(title):
    with open("last_notice.txt", "w", encoding="utf-8") as f:
        f.write(title)


def load_users():
    if os.path.exists("users.json"):
        return json.load(open("users.json"))
    return []


def save_users(users):
    json.dump(users, open("users.json", "w"))

# ============================================
# SINGLE DRIVER SCRAPER
# ============================================
class UpbitScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.lock = asyncio.Lock()

    def _scrape(self):
        self.driver.get(NOTICE_URL)
        time.sleep(1)

        html = self.driver.page_source
        soup = BeautifulSoup(
            html,
            "html.parser",
            parse_only=SoupStrainer("table", class_="css-8atqhb"),
        )
        print(soup)

        notice = soup.select_one('span.css-v2zw8h')




        if notice:

            return notice.get_text(strip=True)

        return None

    async def scrape(self):
        async with self.lock:
            return await asyncio.to_thread(self._scrape)

    def close(self):
        self.driver.quit()

# ============================================
# TELEGRAM (ASYNC)
# ============================================
async def send_message(session, chat_id, text):
    await session.post(
        f"{TG_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
    )


async def get_updates(session, offset):
    async with session.get(
        f"{TG_API}/getUpdates",
        params={"offset": offset, "timeout": 30},
    ) as r:
        data = await r.json()
        return data.get("result", [])

# ============================================
# TELEGRAM LISTENER
# ============================================
async def telegram_listener(session, users):
    offset = 0
    print("📡 Telegram listener started")

    while True:
        updates = await get_updates(session, offset)

        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")

            if text == "/start" and chat_id not in users:
                users.append(chat_id)
                save_users(users)
                await send_message(session, chat_id, "✅ Subscribed")

            elif text == "/stop" and chat_id in users:
                users.remove(chat_id)
                save_users(users)
                await send_message(session, chat_id, "👋 Unsubscribed")

# ============================================
# SCRAPER LOOP (EVERY 1 SECOND)
# ============================================
async def scraper_loop(session, users, scraper):
    last_notice = load_last_notice()
    print("🔍 Scraper started")

    while True:
        if users:
            print("Checking...")
            title = await scraper.scrape()

            if title and title != last_notice:
                print("🔥 New notice:", title)

                msg = (
                    f"🚀 SPECIAL ANNOUNCEMENT 🚀\n\n{title}"
                    if PATTERN_MATCH in title
                    else title
                )

                await asyncio.gather(
                    *[send_message(session, u, msg) for u in users]
                )

                save_last_notice(title)
                last_notice = title

        await asyncio.sleep(0.1)

# ============================================
# MAIN
# ============================================
async def main():
    users = load_users()
    scraper = UpbitScraper()

    async with aiohttp.ClientSession() as session:
        print("🤖 Bot started")
        try:
            await asyncio.gather(
                telegram_listener(session, users),
                scraper_loop(session, users, scraper),
            )
        finally:
            scraper.close()

# ============================================
if __name__ == "__main__":
    asyncio.run(main())

