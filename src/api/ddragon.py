import aiohttp


async def get_latest_ddragon():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://ddragon.leagueoflegends.com/api/versions.json") as response:
            response.raise_for_status()
            content = await response.json()
            return content[0]


async def get_champion_list():
    async with aiohttp.ClientSession() as session:
        latest = await get_latest_ddragon()
        async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/champion.json") as response:
            response.raise_for_status()
            content = await response.json()
            champ_list = {}
            for attribute, value in content['data'].items():
                champ_list.update({value['key']: attribute})
            return champ_list

