import requests
import json
import datetime
class PlayerMissingError(Exception):
    pass

# Raise the custom error

class riotAPI():
    """
        Simple functions to get matches, puuid and matchid's
    """
    def __init__(self, api_key) -> None:
        self.api_key = api_key 
        self.params = {
            "api_key": self.api_key
        }
    def set_key(self, new_key):
        self.api_key = new_key

    def get_puuid(self, user):
        response = requests.get(f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{user}", params= self.params)
        response.raise_for_status()
        return json.loads(response.content)['puuid']
    def get_match_ids(self, method, credentials, count=10):
        """
            Returns a list of matches by ID's in the form of:
            [
            "EUW1_6477028013",
            "EUW1_6476977329",
            ]
        """
        if method == "puuid":
            puuid = credentials
            params = self.params
            params['count'] = 5
            response =requests.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids", params= self.params)
            response.raise_for_status()
            return json.loads(response.content)

    def get_match_details_by_matchID(self, match_id):
        #/lol/match/v5/matches/{matchId}
        response = requests.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}", params= self.params)
        response.raise_for_status()
        return json.loads(response.content)['info']['participants']
    
    def get_match_details_by_matchID_and_filter_for_puuid(self, match_id, puuid) -> list:
        #/lol/match/v5/matches/{matchId}
        # passed matchid and puuid
        # and receives the game data for player {puuid} in game {matchid}
        response = requests.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}", params= self.params)
        response.raise_for_status()
        content = json.loads(response.content)
        for player in content['info']['participants']:
            if player.get("puuid") == puuid:
                return player, content['info']['gameEndTimestamp'], content['info']['gameMode']
        return PlayerMissingError("No recent games found..")
    
    def get_match_details_by_user(self, user) -> list:
        puuid: dict = self.get_puuid(user)
        matchIDs: list = self.get_match_ids("puuid", puuid)

        matchinfo: list = []
        for matchID in matchIDs:
            match_details, game_end, game_mode = self.get_match_details_by_matchID_and_filter_for_puuid(matchID, puuid)
            diff = datetime.datetime.now().timestamp() - game_end/1000
            # time_difference = datetime.timedelta(seconds=diff)
            full_details = {
                "match_details": match_details,
                "game_mode": game_mode,
                "time_diff": diff
            }
            matchinfo.append(full_details)
        return matchinfo
        #     for player in match_details:
        #         if player["puuid"] == puuid:
        #             matchinfo.append(player)
      # return matchinfo
    def get_kda_by_user(self, user):
        game_details_user = riotapi1.get_match_details_by_user(user)
        text = ''
        for game in game_details_user:
            details = game["match_details"]
            time_diff = datetime.timedelta(seconds=game['time_diff']).days
            text += f'**{time_diff}** days ago, {details["kills"]}/{details["deaths"]}/{details["assists"]} in {game["game_mode"]} \n'
        return text
            
            
riotapi1 = riotAPI("RGAPI-0948687e-e67e-44c9-bf24-29a7f84ec248")
kda_text = riotapi1.get_kda_by_user("meshh")

# test = riotapi1.get_match_ids(method="puuid", credentials="")
print(kda_text)

# for i in users

