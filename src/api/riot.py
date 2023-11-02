import datetime
import aiohttp
import asyncio
import copy
from api.ddragon import get_champion_list
from api.merakia import pull_data
from commands.utility.get_roles import get_roles
class PlayerMissingError(Exception):
    pass
# Raise the custom error



class riotAPI():
    """
        Simple functions to get matches, puuid and matchid's
    """

    # FIXME: UNCOUPLE THIS
    def __init__(self, api_key) -> None:
        self.api_key = api_key
        self.params = {
            "api_key": self.api_key
        }

    async def get_summoner_values(self, user):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{user}",
                                   params=self.params) as response:
                response.raise_for_status()
                content: dict = await response.json()
                return content

    async def get_puuid(self, user):
        return (await self.get_summoner_values(user))['puuid']

    async def get_encrypted_summoner_id(self, user):
        return (await self.get_summoner_values(user))['id']
    
    async def get_account_id(self, user):
        return (await self.get_summoner_values(user))['id']

    async def get_name_by_summoner_id(self, summoner_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}",
                                   params=self.params) as response:
                response.raise_for_status()
                content: dict = await response.json()
                return content['name']
    

    async def get_name_by_summoner_puuid(self, puuid):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}",
                                   params=self.params) as response:
                response.raise_for_status()
                content: dict = await response.json()
                return content['name']
            
    async def get_soloq_info_by_name(self, user):
        id = await self.get_encrypted_summoner_id(user)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/{id}",
                                    params=self.params) as response:
                response.raise_for_status()
                content: dict = await response.json()
                for queue in content:
                    if queue['queueType'] == "RANKED_SOLO_5x5":
                        return queue
                return None
    async def get_match_ids(self, method, credentials, count=5, queue_id=None):
        """
            Returns a list of matches by ID's in the form of:
            [
            "EUW1_6477028013",
            "EUW1_6476977329",
            ]
        """
        if method == "puuid":
            puuid = credentials
            params = copy.deepcopy(self.params)
            params['count'] = count
            if queue_id is not None:
                if isinstance(queue_id, str):
                    params['type'] = queue_id
                else:
                    params['queue'] = queue_id
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids",
                                       params=params) as response:
                    response.raise_for_status()
                    content = await response.json()
                    return content

    async def get_full_match_details_by_matchID(self, match_id):
        # /lol/match/v5/matches/{matchId}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}",
                                   params=self.params) as response:
                response.raise_for_status()
                content = await response.json()
                return content

    async def get_match_detail_by_matchID_and_filter_for_puuid(self, match_id, puuid):
        """
            Returns the details of a singular match for a singular player by passing the match ID and PUUID
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}",
                                   params=self.params) as response:
                response.raise_for_status()
                content = await response.json()
                matchinfo = dict()
                matchinfo['game_end'], matchinfo['game_mode'], matchinfo['game_type'] = content['info'][
                                                                                            'gameEndTimestamp'], \
                                                                                        content['info']['gameMode'], \
                                                                                        content['info']['queueId']
                for player in content['info']['participants']:
                    if player.get("puuid") == puuid:
                        matchinfo['match_details'] = player
                        return matchinfo

    async def get_multiple_match_details_by_matchIDs_and_filter_for_puuid(self, puuid, matchIDs) -> list:
        """
            Just a looped version of get_match_detail_by_matchID_and_filter_for_puuid.
            Returns the details of multiple matches for a singular player by passing the match ID and PUUID
        """
        matchesinfo: list = []
        for matchID in matchIDs:
            matchinfo: dict = await self.get_match_detail_by_matchID_and_filter_for_puuid(matchID, puuid)
            matchinfo['time_diff'] = datetime.datetime.now().timestamp() - matchinfo['game_end'] / 1000
            matchesinfo.append(matchinfo)
        return matchesinfo

    async def get_kda_by_puuid(self, puuid, count=10):
        matchIDs: list = await self.get_match_ids("puuid", puuid, count)
        game_details_user: list = await self.get_multiple_match_details_by_matchIDs_and_filter_for_puuid(puuid,
                                                                                                         matchIDs)
        flame = False
        flame_text = 'Nice job \n\n'
        text = ''
        game_mode_mapping = {
            420: "Ranked Solo/Duo",
            440: "Ranked Flex",
            400: "Normal"
        }
        for game in game_details_user:
            details = game["match_details"]
            time_diff = datetime.timedelta(seconds=game['time_diff']).days
            game_mode = game_mode_mapping.get(game["game_type"], "Unranked")
            result = "\u2705" if details["win"] else "\u274C"
            text += f'{result} **{time_diff}** day(s) ago | {details["kills"]}/{details["deaths"]}/{details["assists"]} on **{details["championName"]}** in __{game["game_mode"]}__ | {game_mode} \n'
        return text if flame == False else flame_text + text

    async def get_bad_kda_by_puuid(self, puuid, count=10, sleep_time=2):
        await asyncio.sleep(sleep_time)
        matchIDs: list = await self.get_match_ids("puuid", puuid, count=count)
        game_details_user: list = await self.get_multiple_match_details_by_matchIDs_and_filter_for_puuid(puuid,
                                                                                                         matchIDs)
        text = ''
        game_mode_mapping = {
            420: "Ranked Solo/Duo",
            440: "Ranked Flex",
            400: "Normal"
        }
        for game in game_details_user:
            details = game["match_details"]
            if details['deaths'] > (details['kills'] + details['assists']):
                time_diff = datetime.timedelta(seconds=game['time_diff']).days
                game_mode = game_mode_mapping.get(game["game_type"], "Unranked")
                result = "\u2705" if details["win"] else "\u274C"
                text += f'{result} **{time_diff}** day(s) ago  {details["kills"]}/{details["deaths"]}/{details["assists"]} on **{details["championName"]}** in __{game["game_mode"]}__ | {game_mode} \n'
        return text

    async def get_kda_by_user(self, user, count=10, queue_id=None):
        puuid = await self.get_puuid(user)
        matchIDs: list = await self.get_match_ids("puuid", puuid, count=count, queue_id=queue_id)
        game_details_user = await self.get_multiple_match_details_by_matchIDs_and_filter_for_puuid(puuid, matchIDs)
        flame = False
        flame_text = 'Nice job  \n\n'
        text = ''
        game_mode_mapping = {
            420: "Ranked Solo/Duo",
            440: "Ranked Flex",
            400: "Normal"
        }
        for game in game_details_user:
            details = game["match_details"]
            time_diff = datetime.timedelta(seconds=game['time_diff']).days
            game_mode = game_mode_mapping.get(game["game_type"], "Unranked")
            result = "\u2705" if details["win"] else "\u274C"
            text += f'{result} **{time_diff}** day(s) ago | {details["kills"]}/{details["deaths"]}/{details["assists"]} on **{details["championName"]}** in __{game["game_mode"]}__ | {game_mode} \n'
        return text if flame == False else flame_text + text

    async def get_highest_damage_taken_by_puuid(self, puuid, count, sleep_time, discord_id):
        await asyncio.sleep(sleep_time)
        matchIDs: list = await self.get_match_ids(method="puuid", credentials=puuid, count=count)
        game_details_user = await self.get_multiple_match_details_by_matchIDs_and_filter_for_puuid(puuid, matchIDs)
        player_details = {}
        player_details['taken'], player_details['champion'], player_details['disc_id'] = 0, '', discord_id
        for game in game_details_user:
            if game["match_details"]['totalDamageTaken'] > player_details['taken'] and game["game_mode"] not in ["ARAM",
                                                                                                                 "URF",
                                                                                                                 "CHERRY"]:
                player_details['taken'] = game["match_details"]['totalDamageTaken']
                player_details['champion'] = game["match_details"]["championName"]

        return player_details

    # Method must be caught with an aiohttp.ClientResponseError
    async def get_active_game_status(self, user):
        account_id = await self.get_account_id(user)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://euw1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{account_id}",
                    params=self.params) as response:
                response.raise_for_status()
                content = await response.json()
                status = response.status
                if status == 404:
                    return False, "User not in game", None, None
                game_mode_mapping = {
                    0: "Custom",
                    400: "Normal",
                    420: "Ranked Solo/Duo",
                    430: "Blind Pick",
                    440: "Ranked Flex",
                    450: "ARAM",
                    700: "Clash"
                }
                game_length = int(content['gameLength'])
                game_type = int(content['gameQueueConfigId'])
                if game_type in game_mode_mapping:
                    game_mode = game_mode_mapping[game_type]
                else:
                    game_mode = content['gameMode']
                champion_list = await get_champion_list()
                text_arr = [content['gameId'], []]
                team_one = []
                team_two = []
                team = 0
                for participant in content['participants']:
                    if user.lower() == participant['summonerName'].lower():
                        team = participant['teamId']
                    summonerName = participant['summonerName']
                    if participant['teamId'] == 100:
                        team_one.append([summonerName, int(participant['championId'])])
                    else:
                        team_two.append([summonerName, int(participant['championId'])])
                champion_roles = await pull_data()
                team_one = self.order_team(champion_roles, team_one, champion_list)
                team_two = self.order_team(champion_roles, team_two, champion_list)
                if team == 200:
                    text_arr[1].append(team_two)
                    text_arr[1].append(team_one)
                else:
                    text_arr[1].append(team_one)
                    text_arr[1].append(team_two)
                text_arr.append(game_mode)
                return True, text_arr, game_length, game_type

    async def get_clash_team_id(self, account_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://euw1.api.riotgames.com/lol/clash/v1/players/by-summoner/{account_id}",
                                   params=self.params) as response:
                response.raise_for_status()
                content = await response.json()
                return content[0]['teamId']

    async def get_clash_players(self, team_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://euw1.api.riotgames.com/lol/clash/v1/teams/{team_id}",
                                   params=self.params) as response:
                response.raise_for_status()
                content = await response.json()
                return content['players']

    async def get_clash_opgg(self, user):
        account_id = await self.get_account_id(user)
        team_id = await self.get_clash_team_id(account_id)
        players = await self.get_clash_players(team_id)
        text = "https://www.op.gg/multisearch/euw?summoners="
        for player in players:
            summoner = await self.get_name_by_summoner_id(player['summonerId'])
            summoner_cleaned = summoner.replace(" ", "").lower()
            text += f"{summoner_cleaned},"
        return text[:-1]

    def order_team(self, champion_roles, team, champion_list):
        champions = [combo[1] for combo in team]
        roles = get_roles(champion_roles, champions)
        team_order = []
        for pos in roles:
            for combo in team:
                if combo[1] == pos:
                    team_order.append([combo[0], champion_list[str(combo[1])]])
                    break
        return team_order
