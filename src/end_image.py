from io import BytesIO
import aiohttp
import copy
from PIL import Image, ImageDraw, ImageFont


class EndImage():

    def __init__(self, data, puuid):
        self.data = data
        self.puuid = puuid
        self.player_team_id = 100
        self.swap = False
        self.won_team_id = 100
        self.team_one = self.fill_barely()
        self.team_two = self.fill_barely()
        self.teams = [self.team_one, self.team_two]
        self.game_time = 0
        self.prepare_data()

    def print_data(self):
        for team in self.teams:
            for attribute in team.keys():
                if attribute == "players":
                    for val in team[attribute]:
                        print(val)
                    continue
                print(attribute, team[attribute])
            print("-"*20)


    def fill_barely(self):
        return {"bans": [], "players": [], "kills": 0, "deaths": 0, "assists": 0, "gold": 0, "towers": 0, "drakes": 0, "elder": 0, "baron": 0}

    def prepare_data(self):
        player_indx = self.data["metadata"]['participants'].index(self.puuid)
        if player_indx >= 5:
            self.player_team_id = 200
        self.game_time = int(self.data["info"]["gameDuration"])
        self.game_time = f"{int((self.game_time/60) // 1)}:{self.game_time % 60}"
        for indx, team in enumerate(self.data["info"]["teams"]):
            for ban in team["bans"]:
                self.teams[indx]["bans"].append(ban["championId"])
            objectives = team["objectives"]
            self.teams[indx]["kills"] = objectives["champion"]["kills"]
            self.teams[indx]["towers"] = objectives["tower"]["kills"]
            self.teams[indx]["drakes"] = objectives["dragon"]["kills"]
            self.teams[indx]["baron"] = objectives["baron"]["kills"]
        if self.data["info"]["teams"][0]["win"]:
            self.won_team_id = 100
        else:
            self.won_team_id = 200
        for indx, player in enumerate(self.data["info"]["participants"]):
            if indx < 5:
                self.missing_data(self.team_one, player)
            else:
                self.missing_data(self.team_two, player)
        if self.player_team_id != 100:
            self.team_one, self.team_two = self.team_two, self.team_one
            self.teams = [self.team_one, self.team_two]


    def missing_data(self, team, player):
        team["elder"] = player["challenges"]["teamElderDragonKills"]
        team["assists"] += player["assists"]
        team["deaths"] += player["deaths"]
        team["gold"] += player["goldEarned"]
        team["players"].append({"name": player["summonerName"], "champ_id": player["championId"],
                                "champ_name": player["championName"],
                                "damage_dealt": player["totalDamageDealtToChampions"],
                                "damage_taken": player["totalDamageTaken"]})

    async def get_team_image(self):
        # Define colors
        col_red = (255, 77, 10)
        col_green = (6, 226, 191)
        col_white = (255, 255, 255)
        # Define fonts
        font_big = ImageFont.truetype('../assets/Social Gothic Bold.otf', 49)
        font_small = ImageFont.truetype('../assets/Social Gothic Bold.otf', 25)
        font_text_middle = ImageFont.truetype('../assets/nimbussannovt.ttf', 35)

        base_image = Image.new(mode="RGB", size=(1920, 1080))
        img = Image.open('../assets/end_image.png')
        img = img.convert('RGBA')
        base_image.paste(img, (0, 0), img)

        draw_text = ImageDraw.Draw(base_image)
        result = "Lost"
        color = col_red
        if self.player_team_id == self.won_team_id:
            result = "Won"
            color = col_green
        # Show gameresult
        _, _, w, h = draw_text.textbbox((0, 0), f"Jeroen {result}", font=font_big)
        draw_text.text((105+(775-w)/2, (190-h)/2), f"Jeroen {result}", font=font_big, fill=color)
        # Show gametime
        _, _, w, h = draw_text.textbbox((0, 0), f"Gametime {self.game_time}", font=font_small)
        draw_text.text((105+(775-w)/2, 110+(134-h)/2), f"Gametime {self.game_time}", font=font_small, fill=col_white)
        # Show middle text
        for indx, attr in enumerate(['K/D/A', 'GOLD', 'TOWERS', 'DRAKES', 'ELDER DRAGONS', 'BARONS']):
            _, _, w, h = draw_text.textbbox((0, 0), attr, font=font_text_middle)
            draw_text.text((105 + (776-w)/2, 290+(indx*100)+(100-h)/2), attr, font=font_text_middle, fill=col_white)
        # Might be able to loop from here
        team = self.teams[0]
        _, _, w, h = draw_text.textbbox((0, 0), f"{team['kills']}/{team['deaths']}/{team['assists']}", font=font_big)
        draw_text.text((105, 290+(100-h)/2), f"{team['kills']}/{team['deaths']}/{team['assists']}", font=font_big, fill=col_white)
        for indx, attr in enumerate(['gold', 'towers', 'drakes', 'elder', 'baron']):
            _, _, w, h = draw_text.textbbox((0, 0), str(team[attr]), font=font_big)
            draw_text.text((105, 390+(100*indx)+(100-h)/2), str(team[attr]), font=font_big, fill=col_white)
        team = self.teams[1]
        _, _, w, h = draw_text.textbbox((0, 0), f"{team['kills']}/{team['deaths']}/{team['assists']}", font=font_big)
        draw_text.text((880-w, 290+(100-h)/2), f"{team['kills']}/{team['deaths']}/{team['assists']}", font=font_big, fill=col_white)
        for indx, attr in enumerate(['gold', 'towers', 'drakes', 'elder', 'baron']):
            _, _, w, h = draw_text.textbbox((0, 0), str(team[attr]), font=font_big)
            draw_text.text((880-w, 390+(100*indx)+(100-h)/2), str(team[attr]), font=font_big, fill=col_white)







        base_image.show()
        # for team_num, team in enumerate(self.champions):
        #     for champ_num, champ in enumerate(team):
        #         champ_image: Image = await self.champion_splash(champ)
        #         champ_image = champ_image.convert('RGBA')
        #         position = (70+(520*team_num), 110+(170*champ_num))
        #         base_image.paste(champ_image, position, champ_image)
        #         position = (position[0]+130, position[1]+40)
        #         draw_text.text(position, self.players[team_num][champ_num], fill=(255, 255, 255), font=myFont)
        # bet_text_upper = "BETTING HAS STARTED"
        # bet_text_lower = ".bet <win/lose> <amount>"
        # _, _, w, h = draw_text.textbbox((0, 0), bet_text_upper, font=myFont)
        # draw_text.text(((1100-w)/2, 925+(50-h)/2), bet_text_upper, font=myFont, fill=(255, 255, 255))
        # _, _, w, h = draw_text.textbbox((0, 0), bet_text_lower, font=myFont)
        # draw_text.text(((1100-w)/2, 955+(50-h)/2), bet_text_lower, font=myFont, fill=(255, 255, 255))
        # myFont = ImageFont.truetype('/assets/Gidole-Regular.ttf', 50)
        # _, _, w, h = draw_text.textbbox((0, 0), self.game_mode, font=myFont)
        # draw_text.text(((1100-w)/2, (100-h)/2), self.game_mode, font=myFont, fill=(255, 255, 255))
        # return self.img_to_bytes(base_image)
    #
    # def img_to_bytes(self, image: Image):
    #     bytes = BytesIO()
    #     image.save(bytes, format="PNG")
    #     bytes.seek(0)
    #     return bytes
    #
    async def champion_splash(self, champion):
        version = await self.riot_api.get_latest_ddragon()
        async with aiohttp.ClientSession() as session:
            url = f"http://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion}.png"
            async with session.get(url) as resp:
                resp.raise_for_status()
                if resp.status == 200:
                    content = await resp.read()
                    return Image.open(BytesIO(content))