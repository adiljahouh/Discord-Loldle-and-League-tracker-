from api.ddragon import get_name_resource_ranged_type_class, get_individual_champ_info_raw
import aiohttp
from bs4 import BeautifulSoup

async def get_gender_releaseDate_per_champ(champion):
    if champion == 'Nunu & Willump':
        champion = 'Nunu%20%26amp%3B%20Willump' 
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://lol.fandom.com/api.php?action=cargoquery&format=json&limit=50&tables=Champions&fields=Name%2CPronoun%2CReleaseDate&where=Name%3D%22{champion}%22") as response:
            response.raise_for_status()
            content = await response.json()
            return content['cargoquery'][0]['title']

async def get_region(champion):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://leagueoflegends.fandom.com/wiki/{champion}") as response:
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
            
async def get_base_lodle_champ_data(ddrag_version, champ) -> dict:
    print(f"Processing {champ}")
    champ_info_base = await get_individual_champ_info_raw(ddrag_version, champ)
    champ_resource_name_class = await get_name_resource_ranged_type_class(champ_info_base, champ)
    try:
        gender_releasdate = await get_gender_releaseDate_per_champ(champ)
    except IndexError as e:
        gender_releasdate = await get_gender_releaseDate_per_champ(champ_resource_name_class['Name'])
    try:
        region, species = await get_region(champ_resource_name_class['Name'])
    except Exception as e:
        print(f'First attempt {champ_resource_name_class["Name"]} failed')
        try:
            spaceless_champ = champ_resource_name_class['Name'].replace(" ", "_").replace("'","%27")
            print(f"second: {spaceless_champ}")
            region, species = await get_region(spaceless_champ)
        except Exception as e:
            region, species = await get_region(champ)
    if 'ReleaseDate__precision' in gender_releasdate:
        del gender_releasdate['ReleaseDate__precision']
        
        # Convert the ReleaseDate to just the year
    if 'ReleaseDate' in gender_releasdate:
        # Assuming the date is in a standard format like 'YYYY-MM-DD'
        release_date = gender_releasdate['ReleaseDate']
        release_year = release_date.split('-')[0]  # Get the year part
        gender_releasdate['ReleaseDate'] = release_year
    # print("REGION ", region)
    merged_dict = {**champ_resource_name_class, **gender_releasdate}
    merged_dict['Region'] = region
    merged_dict['Species'] = species
    return merged_dict
