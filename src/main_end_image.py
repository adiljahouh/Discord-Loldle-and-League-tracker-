import aiohttp
from config import Settings
from api.riot import riotAPI
from commands.utility.end_image import EndImage
import asyncio


async def main():
    settings = Settings()
    client = riotAPI(settings.RIOTTOKEN)
    params = {
        "api_key": settings.RIOTTOKEN
    }
    user = "nightlon"
    puuid = await client.get_puuid(user)
    match = (await client.get_match_ids("puuid", puuid, count=5))[0] #, queue_id=420
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/{match}", params=params) as response:
            response.raise_for_status()
            content = await response.json()
            data = content
    end = EndImage(data, user)
    await end.get_team_image()



if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
