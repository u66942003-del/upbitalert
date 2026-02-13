import aiohttp

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://upbit.com/"
}

async with aiohttp.ClientSession(headers=headers) as session:
    async with session.get("https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=1&category=all") as resp:
        data = await resp.json()
        print(data)
