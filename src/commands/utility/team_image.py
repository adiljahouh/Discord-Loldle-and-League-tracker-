from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from api.ddragon import get_champion_splash, get_latest_ddragon
from src.commands.utility.types import *

class imageCreator():

    def __init__(self, game_track_data: ActiveGameData, ddrag_version):
        self.game_track_data = game_track_data
        self.ddrag_version = ddrag_version

    async def get_team_image(self):
        ## context manager
        base_image = Image.new(mode="RGB", size=(1100, 1020))
        img = Image.open('./assets/image_generator/team_background.png')
        img = img.convert('RGBA')
        base_image.paste(img, (0, 0), img)
        myFont = ImageFont.truetype('./assets/image_generator/Gidole-Regular.ttf', 37)
        draw_text = ImageDraw.Draw(base_image)
        for team_index, team in enumerate(self.game_track_data.teams):
            for player_index, player in enumerate(team.players):
                champ_image: Image.Image = await get_champion_splash(self.ddrag_version, player.champion_id)
                champ_image = champ_image.convert('RGBA')
                position = (70 + (520 * team_index), 110 + (170 * player_index))
                base_image.paste(champ_image, position, champ_image)
                position = (position[0] + 130, position[1] + 40)
                draw_text.text(position, team.players[team_index][player_index], fill=(255, 255, 255), font=myFont)
        bet_text_upper = "BETTING HAS STARTED"
        bet_text_lower = ".bet <win/lose> <amount>"
        _, _, w, h = draw_text.textbbox((0, 0), bet_text_upper, font=myFont)
        draw_text.text(((1100 - w) / 2, 925 + (50 - h) / 2), bet_text_upper, font=myFont, fill=(255, 255, 255))
        _, _, w, h = draw_text.textbbox((0, 0), bet_text_lower, font=myFont)
        draw_text.text(((1100 - w) / 2, 955 + (50 - h) / 2), bet_text_lower, font=myFont, fill=(255, 255, 255))
        myFont = ImageFont.truetype('./assets/image_generator/Gidole-Regular.ttf', 50)
        _, _, w, h = draw_text.textbbox((0, 0), self.game_track_data.game_type, font=myFont)
        draw_text.text(((1100 - w) / 2, (100 - h) / 2), self.game_track_data.game_type, font=myFont, fill=(255, 255, 255))
        return self.img_to_bytes(base_image)

    def img_to_bytes(self, image: Image):
        bytes = BytesIO()
        image.save(bytes, format="PNG")
        bytes.seek(0)
        return bytes
