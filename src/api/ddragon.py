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


async def get_champion_dict(ddrag_version) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{ddrag_version}/data/en_US/champion.json") as response:
            response.raise_for_status()
            content = await response.json()
            champ_dict = {}
            for attribute, value in content['data'].items():
                champ_dict.update({value['key']: attribute})
            return champ_dict
        
async def get_champion_ddrag_format_list(ddrag_version)->list:
    champdict = await get_champion_dict(ddrag_version)
    return list(champdict.values())

async def get_individual_champ_info_raw(ddrag_version, champion):
    """Return latest champ info stats e.g. https://ddragon.leagueoflegends.com/cdn/14.23.1/data/en_US/champion/Aatrox.json"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{ddrag_version}/data/en_US/champion/{champion}.json") as response:
            response.raise_for_status()
            content = await response.json()
            return content
async def get_individual_spell_info_raw(ddrag_version, spell):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{ddrag_version}/img/spell/{spell}") as response:
            response.raise_for_status()
            content = await response.read()
            return content 
async def get_splash_art_champ(champion, num=0):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion}_{num}.jpg") as response:
            response.raise_for_status()
            content = await response.read()
            return content  
async def get_random_num_skin_champ(ddrag_champ_info, champion):
    return random.choice([skin["num"] for skin in  ddrag_champ_info['data'][champion]['skins']])

async def get_random_champ(ddrag_version):
    champion_list = await get_champion_dict(ddrag_version)
    return random.choice(list(champion_list.values()))    

async def get_name_resource_ranged_type_class(ddrag_champ_info, champion):
    # classic_lodle['name'] = champion
    champ_info = ddrag_champ_info['data'][champion]
    champion_info = {
    'Name': champ_info.get('name'),
    'Resource': champ_info.get('partype'),
    'Range_type': 'Ranged' if champ_info.get('stats', {}).get('attackrange', 0) > 325 else 'Melee',
    'Class': champ_info.get('tags')
}
    return champion_info

async def get_name_resource_ranged_type_class_and_random_spell(ddrag_champ_info, champion):
    champ_info = ddrag_champ_info['data'][champion]
    champion_info = {
    'Name': champ_info.get('name'),
    'Resource': champ_info.get('partype'),
    'Range_type': 'Ranged' if champ_info.get('stats', {}).get('attackrange', 0) > 325 else 'Melee',
    'Class': champ_info.get('tags')
}
    spells = [key for key in champ_info['spells']]
    random_spell = random.choice(spells)
    # Get the PNG image for the random spell
    spell_image_content = await get_individual_spell_info_raw(random_spell['image']['full'])
    
    return champion_info, spell_image_content
async def get_random_spell(ddrag_version, champion):
    ddrag_champ_info = await get_individual_champ_info_raw(ddrag_version, champion)
    champ_info = ddrag_champ_info['data'][champion]
    spells = [key for key in champ_info['spells']]
    random_spell = random.choice(spells)
    # Get the PNG image for the random spell
    spell_image_content = await get_individual_spell_info_raw(ddrag_version, random_spell['image']['full'])
    return spell_image_content
async def get_name_resource_ranged_type_class_and_splash(ddrag_champ_info, champion):
    champ_info = ddrag_champ_info['data'][champion]
    champion_info = {
    'Name': champ_info.get('name'),
    'Resource': champ_info.get('partype'),
    'Range_type': 'Ranged' if champ_info.get('stats', {}).get('attackrange', 0) > 325 else 'Melee',
    'Class': champ_info.get('tags')
}
    splash = get_random_skin_splash(champion)
    return champion_info, splash

async def get_random_skin_splash(ddrag_version, champion):
    ddrag_champ_info = await get_individual_champ_info_raw(ddrag_version, champion)
    skin_num = await get_random_num_skin_champ(ddrag_champ_info, champion=champion)
    splash = await get_splash_art_champ(champion=champion, num=skin_num)
    return splash

async def get_champion_splash(ddrag_version, champion):
    async with aiohttp.ClientSession() as session:
        url = f"http://ddragon.leagueoflegends.com/cdn/{ddrag_version}/img/champion/{champion}.png"
        async with session.get(url) as response:
            response.raise_for_status()
            if response.status == 200:
                content = await response.read()
                return Image.open(BytesIO(content))
