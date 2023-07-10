from pydantic import AnyUrl, AnyHttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DISCORDTOKEN: str
    CHANNELID: int
    WEBHOOK: str
    RIOTTOKEN:str
    REDISURL: str
    GPTAPI: str

    class Config:
        env_file = ".env"