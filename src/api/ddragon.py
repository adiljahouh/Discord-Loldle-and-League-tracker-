import aiohttp
from io import BytesIO
from PIL import Image
import random

async def get_latest_ddragon():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://ddragon.leagueoflegends.com/api/versions.json") as response:
            response.raise_for_status()
            content = await response.json()
            return content[0]


async def get_champion_dict() -> dict:
    async with aiohttp.ClientSession() as session:
        latest = await get_latest_ddragon()
        async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/champion.json") as response:
            response.raise_for_status()
            content = await response.json()
            champ_dict = {}
            for attribute, value in content['data'].items():
                champ_dict.update({value['key']: attribute})
            return champ_dict

async def get_individual_champ_info(champion):
    async with aiohttp.ClientSession() as session:
        latest = await get_latest_ddragon()
        async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/champion/{champion}.json") as response:
            response.raise_for_status()
            content = await response.json()
            return content
        
async def get_loldle_data():
    champion_list = await get_champion_dict()
    champion = random.choice(list(champion_list.values()))
    print(champion)
    champ_info = await get_individual_champ_info(champion)
    print(champ_info['data'][champion])
    #print(champ_info['data'][champion]['spells'])
    ## get all champs
    ## random select 1
    ## get abilities of that champ
    ## distort the image
    ## loldle
    pass

async def champion_splash(champion):
    version = await get_latest_ddragon()
    async with aiohttp.ClientSession() as session:
        url = f"http://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion}.png"
        async with session.get(url) as response:
            response.raise_for_status()
            if response.status == 200:
                content = await response.read()
                return Image.open(BytesIO(content))
