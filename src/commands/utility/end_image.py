from io import BytesIO
from api.ddragon import get_champion_dict, get_champion_splash, get_latest_ddragon
from PIL import Image, ImageDraw, ImageFont


def team_dict():
    return {
        "bans": [], "players": [], "kills": 0, "deaths": 0, "assists": 0,
        "gold": 0, "towers": 0, "drakes": 0, "elder": 0, "baron": 0
    }


def img_to_bytes(image: Image):
    byte_arr = BytesIO()
    image.save(byte_arr, format="PNG")
    byte_arr.seek(0)
    return byte_arr


class EndImage:

    def __init__(self, data, name):
        self.data = data
        self.name: str = name
        self.puuid = 0
        self.player_team_id = 100
        self.won_team_id = 100
        self.team_one = team_dict()
        self.team_two = team_dict()
        self.teams = [self.team_one, self.team_two]
        self.game_time = 0
        self.prepare_data()

    def prepare_data(self):
        # Get puuid to place main player in team
        # print(self.data)
        for player in self.data["info"]["participants"]:
            # print(f"player found and cleaned {player['riotIdGameName'].replace(' ', '').lower()}#{player['riotIdTagline'].replace(' ', '').lower()}")
            if f"{player['riotIdGameName'].replace(' ', '').lower()}#{player['riotIdTagline'].replace(' ', '').lower()}" == self.name.replace(' ', '').lower():
                # print("found main player")
                self.puuid = player["puuid"]
        player_indx = self.data["metadata"]['participants'].index(self.puuid)
        if player_indx >= 5:
            self.player_team_id = 200
        # Set time
        self.game_time = int(self.data["info"]["gameDuration"])
        seconds = self.game_time % 60
        seconds = seconds if seconds > 10 else f"0{seconds}"
        self.game_time = f"{int((self.game_time/60) // 1)}:{seconds}"
        # Set team results
        for indx, team in enumerate(self.data["info"]["teams"]):
            for ban in team["bans"]:
                self.teams[indx]["bans"].append(ban["championId"])
            objectives = team["objectives"]
            self.teams[indx]["kills"] = objectives["champion"]["kills"]
            self.teams[indx]["towers"] = objectives["tower"]["kills"]
            self.teams[indx]["drakes"] = objectives["dragon"]["kills"]
            self.teams[indx]["baron"] = objectives["baron"]["kills"]
        # Determine result of main player
        if self.data["info"]["teams"][0]["win"]:
            self.won_team_id = 100
        else:
            self.won_team_id = 200
        for indx, player in enumerate(self.data["info"]["participants"]):
            if indx < 5:
                self.fill_player_info(self.team_one, player)
            else:
                self.fill_player_info(self.team_two, player)
        # Swap the teams if main player is not in the first team
        if self.player_team_id != 100:
            self.team_one, self.team_two = self.team_two, self.team_one
            self.teams = [self.team_one, self.team_two]

    def fill_player_info(self, team, player):
        team["elder"] = player["challenges"]["teamElderDragonKills"]
        team["assists"] += player["assists"]
        team["deaths"] += player["deaths"]
        team["gold"] += player["goldEarned"]
        hero = False
        if self.puuid == player["puuid"]:
            hero = True
        team["players"].append({"name": player["riotIdGameName"],
                                "champ_id": player["championId"],
                                "champ_name": player["championName"],
                                "damage_dealt": player["totalDamageDealtToChampions"],
                                "damage_taken": player["totalDamageTaken"],
                                "kills": player["kills"],
                                "deaths": player["deaths"],
                                "assists": player["assists"],
                                "hero": hero
                                })

    async def get_team_image(self, ddrag_version):
        # Define colors
        col_red = (255, 77, 10)
        col_green = (6, 226, 191)
        col_white = (255, 255, 255)
        col_gray = (60, 60, 60)
        col_black = (0, 0, 0)
        # Define fonts
        font_xll = ImageFont.truetype('./assets/image_generator/Social Gothic Bold.otf', 90)
        font_big = ImageFont.truetype('./assets/image_generator/Social Gothic Bold.otf', 50)
        font_small = ImageFont.truetype('./assets/image_generator/Social Gothic Bold.otf', 25)
        font_text_middle = ImageFont.truetype('./assets/image_generator/nimbussannovt.ttf', 35)

        base_image = Image.new(mode="RGB", size=(1920, 1080))

        with Image.open('./assets/image_generator/end_image.png') as img:
            img = img.convert('RGBA')
            base_image.paste(img, (0, 0), img)

        draw_text = ImageDraw.Draw(base_image)

        result = "LOST"
        color = col_red
        if self.player_team_id == self.won_team_id:
            result = "WON"
            color = col_green
        # Show game result
        print(self.name.split('#')[0])
        _, _, w, h = draw_text.textbbox((0, 0), f"{self.name.split('#')[0].upper()} {result}", font=font_xll)
        draw_text.text((105+(775-w)/2, (243-h)/2), f"{self.name.split('#')[0].upper()} {result}", font=font_xll, fill=color)
        # Show game time
        _, _, w, h = draw_text.textbbox((0, 0), f"Gametime {self.game_time}", font=font_text_middle)
        draw_text.text((105+(775-w)/2, 180+(134-h)/2), f"Gametime {self.game_time}", font=font_text_middle, fill=col_white)
        # Show middle text
        for indx, attr in enumerate(['K/D/A', 'GOLD', 'TOWERS', 'DRAKES', 'ELDER DRAGONS', 'BARONS', 'BANS']):
            _, _, w, h = draw_text.textbbox((0, 0), attr, font=font_text_middle)
            draw_text.text((105 + (776-w)/2, 290+(indx*100)+(100-h)/2), attr, font=font_text_middle, fill=col_white)

        # Show team stats
        for team_indx, team in enumerate(self.teams):
            _, _, w, h = draw_text.textbbox((0, 0), f"{team['kills']}/{team['deaths']}/{team['assists']}", font=font_big)
            draw_text.text((105 + team_indx*(775-w), 290+(100-h)/2), f"{team['kills']}/{team['deaths']}/{team['assists']}", font=font_big, fill=col_white)
            for indx, attr in enumerate(['gold', 'towers', 'drakes', 'elder', 'baron']):
                _, _, w, h = draw_text.textbbox((0, 0), str(team[attr]), font=font_big)
                draw_text.text((105 + team_indx*(775-w), 390+(100*indx)+(100-h)/2), str(team[attr]), font=font_big, fill=col_white)

        # Bans
        champ_list = await get_champion_dict(ddrag_version)
        for team_indx, team in enumerate(self.teams):
            for indx, ban in enumerate(team["bans"]):
                # No-bans should be skipped
                if str(ban) == "-1":
                    continue
                with await get_champion_splash(ddrag_version, champ_list[str(ban)]) as champ_image:
                    champ_image = champ_image.convert('RGBA')
                    if team_indx == 0:
                        pos = (110 + (65*indx), 913)
                    else:
                        pos = (825 - (65*indx), 913)
                    champ_image = champ_image.resize((55, 55))
                    base_image.paste(champ_image, pos, champ_image)

        # Min/Max stats
        min_stat = float('inf')
        max_stat = float('-inf')
        for team in self.teams:
            for player in team['players']:
                stats = [player['damage_dealt'], player['damage_taken']]
                min_stat = min(min_stat, *stats)
                max_stat = max(max_stat, *stats)

        # Draw damage graph
        for team_indx, team in enumerate(self.teams):
            for indx, player in enumerate(team["players"]):
                # Draw dealt damage
                if team_indx == 0:
                    base_image.paste(col_green, (960, 30 + (205*indx), 1150 + int(250*(player['damage_dealt'] - min_stat)/(max_stat - min_stat)), 100 + (205*indx)))
                    base_image.paste(col_gray, (960, 140 + (205*indx), 1150 + int(250*(player['damage_taken'] - min_stat)/(max_stat - min_stat)), 210 + (205*indx)))
                else:
                    base_image.paste(col_red, (1665 - int(250*(player['damage_dealt'] - min_stat)/(max_stat - min_stat)), 30 + (205*indx), 1855, 100 + (205*indx)))
                    base_image.paste(col_gray, (1665 - int(250*(player['damage_taken'] - min_stat)/(max_stat - min_stat)), 140 + (205*indx), 1855, 210 + (205*indx)))

        # Player names, damage numbers, player champ images, kda
        try:
            for team_indx, team in enumerate(self.teams):
                for indx, player in enumerate(team["players"]):
                    kda = f"{player['kills']}/{player['deaths']}/{player['assists']}"
                    # Player name
                    _, _, w, h = draw_text.textbbox((0, 0), str(player['name']), font=font_small)
                    draw_text.text((1090 + (635*team_indx) - (w*team_indx), 60 + (205*indx) + (120-h)/2), str(player['name']), font=font_small, fill=col_white, stroke_width=2, stroke_fill=col_black)
                    # Player damage dealt
                    _, _, w, h = draw_text.textbbox((0, 0), str(player['damage_dealt']), font=font_small)
                    draw_text.text((1090 + (635*team_indx) - (w*team_indx), 5 + (205*indx) + (120-h)/2), str(player['damage_dealt']), font=font_small, fill=col_white, stroke_width=2, stroke_fill=col_black)
                    # Player damage taken
                    _, _, w, h = draw_text.textbbox((0, 0), str(player['damage_taken']), font=font_small)
                    draw_text.text((1090 + (635*team_indx) - (w*team_indx), 115 + (205*indx) + (120-h)/2), str(player['damage_taken']), font=font_small, fill=col_white, stroke_width=2, stroke_fill=col_black)
                    # Player image
                    with await get_champion_splash(ddrag_version, champ_list[str(player['champ_id'])]) as champ_image:
                        champ_image = champ_image.convert('RGBA')
                        pos = (960 + (775*team_indx), 55 + (205*indx))
                        base_image.paste(champ_image, pos, champ_image)
                    # Player kda
                    _, _, w, h = draw_text.textbbox((0, 0), kda, font=font_small)
                    draw_text.text((960 + (775*team_indx) + (120-w)/2, 180 + (205*indx)), kda, font=font_small, fill=col_white, stroke_width=2, stroke_fill=col_black)
        except Exception as e:
            print(e)

        return img_to_bytes(base_image)


    def get_game_result(self):
        return self.player_team_id == self.won_team_id
