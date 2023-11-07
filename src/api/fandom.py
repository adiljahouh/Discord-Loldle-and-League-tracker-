# https://lol.fandom.com/api.php?action=cargofields&format=json&table=Champions
# https://lol.fandom.com/api.php?action=cargoquery&format=json&limit=499&tables=Champions&fields=Name%2CTitle%2CAttributes%2CKeyDdragon%2CReleaseDate%2CRealName%2CPronoun
from ddragon import get_name_resource_ranged_type_class, get_random_champ
import asyncio
import aiohttp


# async def test():
#     test = await get_loldle_data()
# asyncio.run(test())
async def get_gender_releaseDate_per_champ(champion):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://lol.fandom.com/api.php?action=cargoquery&format=json&limit=50&tables=Champions&fields=Name%2CPronoun%2CReleaseDate&where=Name%3D%22{champion}%22") as response:
            response.raise_for_status()
            content = await response.json()
            return content['cargoquery'][0]['title']

# async def get_year_class_role_per_champ(champion):
#     async with aiohttp.ClientSession() as session:
#         async with session.get(f"https://lol.fandom.com/api.php?action=cargoquery&format=json&limit=50&tables=ChampionFlashcards&fields=Champion%2C%20Year%2C%20Classes%2C%20Roles&where=Champion%3D%22{champion}%22") as response:
#             response.raise_for_status()
#             print(f"https://lol.fandom.com/api.php?action=cargoquery&format=json&limit=50&tables=ChampionFlashcards&fields=Champion%2C%20Year%2C%20Classes%2C%20Roles&where=Champion%3D%22{champion}%22")
#             content = await response.json()
#             return content

async def get_loldle_data():
    champ = await get_random_champ()
    test = await get_name_resource_ranged_type_class(champ)
    print(test)
    test2 = await get_gender_releaseDate_per_champ(champ)
    print(test2)
    # test3 = await get_year_class_role_per_champ(champ)
    # print(test3)
    # await get_champions
asyncio.run(get_loldle_data())

# need region and roles (merakia)