from pydantic import AnyUrl, AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DISCORDTOKEN: str
    CHANNELID: int
    JAILROLE: int
    RIOTTOKEN: str
    REDISURL: str
    PLAYERROLE: int
    GROLE: int
    PINGROLE: int

    class Config:
        env_file = ".env"
