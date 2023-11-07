# https://lol.fandom.com/api.php?action=cargofields&format=json&table=Champions
# https://lol.fandom.com/api.php?action=cargoquery&format=json&limit=499&tables=Champions&fields=Name%2CTitle%2CAttributes%2CKeyDdragon%2CReleaseDate%2CRealName%2CPronoun
from api.ddragon import get_name_resource_ranged_type_class, get_random_champ
import asyncio
import aiohttp
from bs4 import BeautifulSoup

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

async def get_region(champion):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://leagueoflegends.fandom.com/wiki/{champion}") as response:
            # print(champion)
            # print(f"https://leagueoflegends.fandom.com/wiki/{champion}")
            
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')

            region_header = soup.find('div', {'data-source': 'region'})
            species_header = soup.find('div', {'data-source': 'species'})
            regions=[]
            species=[]
            if region_header:
                a_elements = region_header.find_all('a', href=True)
                for a in a_elements:
                    text = a.get_text(strip=True)
                    if text:
                        regions.append(text)
            if species_header:
                a_elements = species_header.find_all('a', href=True)
                for a in a_elements:
                    # Get the text of each 'a' element and add it to the list
                    text = a.get_text(strip=True)
                    if text:
                        species.append(text)
            return regions,species 
            

async def get_loldle_data(champ="random"):
    if champ=="random":
        champ = await get_random_champ()
    name_resource_range_class = await get_name_resource_ranged_type_class(champ)
    try:
        gender_releasdate = await get_gender_releaseDate_per_champ(champ)
    except IndexError as e:
        gender_releasdate = await get_gender_releaseDate_per_champ(name_resource_range_class['Name'])
    try:
        region, species = await get_region(champ)
    except Exception as e:
        print('First attempt failed')
        try:
            region, species = await get_region(name_resource_range_class['Name'])
        except Exception as e:
            print("second attemtp failed")
            spaceless_champ = champ.replace(" ", "_").replace("'","%27")
            region, species = await get_region(spaceless_champ)
    merged_dict = {**name_resource_range_class, **gender_releasdate}
    merged_dict['Region'] = region
    merged_dict['Species'] = species
    return merged_dict

# asyncio.run(get_loldle_data())