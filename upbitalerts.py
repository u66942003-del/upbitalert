import random

import aiohttp
import asyncio
import time

# ---------------- CONFIG ----------------
UPBIT_URL = "https://api-manager.upbit.com/api/v1/announcements"
UPBIT_PARAMS = {
    "os": "web",
    "page": 1,
    "per_page": 1,
    "category": "all"
}

BOT_TOKEN = "8414741935:AAHrQxNw9iFHZxf-5syA6uG2lFyJzKVHQ_A"
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
# ----------------------------------------

last_title = None                  # title used as unique ID
subscribers = set()                # chat_ids auto-collected


# -------- Telegram handling --------
async def poll_telegram(session):
    offset = None

    while True:
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset

        async with session.get(f"{TG_API}/getUpdates", params=params) as resp:
            data = await resp.json()

        for update in data.get("result", []):
            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            if text == "/start":
                subscribers.add(chat_id)
                await send_message(session, chat_id, "✅ You are subscribed to Upbit alerts.")

        await asyncio.sleep(0.1)


async def send_message(session, chat_id, text):
    await session.post(
        f"{TG_API}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )


# -------- Upbit polling --------
async def poll_upbit(session):
    global last_title

    while True:
        try:
            start = time.perf_counter()

            async with session.get(UPBIT_URL, params=UPBIT_PARAMS) as resp:
                data = await resp.json()

            notice = data["data"]["notices"][0]
            title = notice["title"].replace(" ", "")

            if last_title is None:
                last_title = title
                print("Initialized with:", title)


            elif title != last_title:
                print("🚨 NEW ANNOUNCEMENT:", notice["title"])

                for chat_id in subscribers:
                    await send_message(
                        session,
                        chat_id,
                        f"🚨 New Upbit Announcement 🚨\n\n{notice['title']}"
                    )

                last_title = title

            end = time.perf_counter()
            print(f"⏱️ {end - start:.4f}s")

        except Exception as e:
            print("Upbit error:", e)

        rnd=random.randint(40,55)


        await asyncio.sleep(rnd/100)  # your polling speed


# -------- Main --------
async def main():
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(
            poll_telegram(session),
            poll_upbit(session)
        )

asyncio.run(main())
