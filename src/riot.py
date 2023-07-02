import requests
import json
class riotAPI():
    #https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/meshh?api_key=
    #/lol/match/v5/matches/by-puuid/{puuid}/ids
    #
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
            return response.status_code
    def get_match_ids(self, method, credentials):
        if method == "puuid":
            puuid = credentials
            response =requests.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids", params= self.params)
            if response.status_code == 200:
                return json.loads(response.content)
            else:
                return response.status_code

riotapi1 = riotAPI("")
user = riotapi1.get_puuid("meshh")
test = riotapi1.get_matches_ids(method="puuid", credentials="")
print(test)