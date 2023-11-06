# https://lol.fandom.com/api.php?action=cargofields&format=json&table=Champions
# https://lol.fandom.com/api.php?action=cargoquery&format=json&limit=499&tables=Champions&fields=Name%2CTitle%2CAttributes%2CKeyDdragon%2CReleaseDate%2CRealName%2CPronoun
from ddragon import get_champion_list
import asyncio
import aiohttp


async def test():
    test = await get_champion_list()
    print(test)
asyncio.run(test())
# async def get_champions():
#     async with aiohttp.ClientSession() as session:
#         latest = await get_latest_ddragon()
#         async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/champion.json") as response:
#             response.raise_for_status()
#             content = await response.json()
#             champ_list = {}
#             for attribute, value in content['data'].items():
#                 champ_list.update({value['key']: attribute})
#             return champ_list