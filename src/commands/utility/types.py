from pydantic import BaseModel, Field
from typing import List, Dict
class Player(BaseModel):
    summoner_name: str = Field(..., alias='riotId')
    champion_id: int = Field(..., alias='championId')
    order: int = 0 # Default order is 0, can be set later
    model_config = {
        "populate_by_name": True
    }
class Team(BaseModel):
    team_id: int = Field(..., alias='teamId')
    # role: str = Field(..., alias='role')
    players: List[Player]
    model_config = {
        "populate_by_name": True
    }
class ActiveGameData(BaseModel):

    game_length: int = Field(..., alias='gameLength')
    game_type: str
    game_id: int = Field(..., alias='gameId')
    # victim_team_id: int = Field(..., alias='teamId')
    teams: List[Team]

    model_config = {
        "populate_by_name": True
    }