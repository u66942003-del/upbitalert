import aiohttp
import asyncio

async def fetch_data():
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}


    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(
            "https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=1&category=all"
        ) as resp:
            text = await resp.text()
            print(text)

asyncio.run(fetch_data())

