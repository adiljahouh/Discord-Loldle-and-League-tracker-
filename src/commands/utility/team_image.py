from io import BytesIO
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from ddragon import get_latest_ddragon


class imageCreator():

    def __init__(self, champions, players, game_mode):
        self.champions = champions
        self.players = players
        self.game_mode = game_mode

    def get_champions(self):
        return self.champions

    def get_players(self):
        return self.players

    async def get_team_image(self):
        base_image = Image.new(mode="RGB", size=(1100, 1020))
        img = Image.open('/assets/team_background.png')
        img = img.convert('RGBA')
        base_image.paste(img, (0, 0), img)
        myFont = ImageFont.truetype('/assets/Gidole-Regular.ttf', 37)
        draw_text = ImageDraw.Draw(base_image)
        for team_num, team in enumerate(self.champions):
            for champ_num, champ in enumerate(team):
                champ_image: Image = await self.champion_splash(champ)
                champ_image = champ_image.convert('RGBA')
                position = (70 + (520 * team_num), 110 + (170 * champ_num))
                base_image.paste(champ_image, position, champ_image)
                position = (position[0] + 130, position[1] + 40)
                draw_text.text(position, self.players[team_num][champ_num], fill=(255, 255, 255), font=myFont)
        bet_text_upper = "BETTING HAS STARTED"
        bet_text_lower = ".bet <win/lose> <amount>"
        _, _, w, h = draw_text.textbbox((0, 0), bet_text_upper, font=myFont)
        draw_text.text(((1100 - w) / 2, 925 + (50 - h) / 2), bet_text_upper, font=myFont, fill=(255, 255, 255))
        _, _, w, h = draw_text.textbbox((0, 0), bet_text_lower, font=myFont)
        draw_text.text(((1100 - w) / 2, 955 + (50 - h) / 2), bet_text_lower, font=myFont, fill=(255, 255, 255))
        myFont = ImageFont.truetype('/assets/Gidole-Regular.ttf', 50)
        _, _, w, h = draw_text.textbbox((0, 0), self.game_mode, font=myFont)
        draw_text.text(((1100 - w) / 2, (100 - h) / 2), self.game_mode, font=myFont, fill=(255, 255, 255))
        return self.img_to_bytes(base_image)

    def img_to_bytes(self, image: Image):
        bytes = BytesIO()
        image.save(bytes, format="PNG")
        bytes.seek(0)
        return bytes

    async def champion_splash(self, champion):
        version = await get_latest_ddragon()
        async with aiohttp.ClientSession() as session:
            url = f"http://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion}.png"
            async with session.get(url) as resp:
                resp.raise_for_status()
                if resp.status == 200:
                    content = await resp.read()
                    return Image.open(BytesIO(content))
