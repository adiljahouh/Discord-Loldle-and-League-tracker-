from pydantic import BaseModel, Field
from typing import List, Dict
class Player(BaseModel):
    summoner_name: str = Field(..., alias='summonerName')
    champion_id: int = Field(..., alias='championId')

class Team(BaseModel):
    team_id: int = Field(..., alias='teamId')
    role: str = Field(..., alias='role')
    players: List[Player]

class ActiveGameData(BaseModel):

    game_length: int = Field(..., alias='gameLength')
    game_type: str
    game_id: int = Field(..., alias='gameId')
    # victim_team_id: int = Field(..., alias='teamId')
    teams: List[Team]

    class Config:
        allow_population_by_field_name = True  # allows using field names as keys