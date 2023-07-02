import requests
import json


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
        if response.status_code == 200:
            return json.loads(response.content)['puuid']
        else:
            raise ValueError(f"Puuid for summoner '{user}' not found.")
    def get_match_ids(self, method, credentials):
        """
            Returns a list of matches by ID's in the form of:
            [
            "EUW1_6477028013",
            "EUW1_6476977329",
            ]
        """
        if method == "puuid":
            puuid = credentials
            response =requests.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids", params= self.params)
            if response.status_code == 200:
                return json.loads(response.content)
            else:
                return response.status_code
    

    def get_match_details_by_ID(self, match_id):
        #/lol/match/v5/matches/{matchId}
        response = requests.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}", params= self.params)
        if response.status_code == 200:
            return json.loads(response.content)['puuid']
        else:
            raise ValueError(f"MatchID '{match_id}' not found.")

# riotapi1 = riotAPI("")
# user = riotapi1.get_puuid("meshh")
# test = riotapi1.get_match_ids(method="puuid", credentials="")
# print(test)