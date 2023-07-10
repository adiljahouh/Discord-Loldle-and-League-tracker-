import redis
from redis.exceptions import ConnectionError

class cacheDB():
    def __init__(self, url) -> None:
        self.url = url
        self.client = None
        pass

    def connect(self) -> None:
        try:
            self.client : redis.Redis[bytes] = redis.Redis.from_url(self.url, db=0)
        except ConnectionError:
            print("Cant connect to host")


    def store_user(self, discord_id, riot_user, puuid, author_discord_tag) -> None:
        if self.client is None:
            self.connect()
        self.client.hset(discord_id, "riot_user", riot_user)
        self.client.hset(discord_id, "puuid", puuid)
        self.client.hset(discord_id, "discord_tag", author_discord_tag)
    
    def get_user_field(self, discord_id, field) -> (bytes|None):
        # field can be riot_user or puuid
        # e.g.  121210930139 -> meshh -> 12132323
        if self.client is None:
            self.connect()
        return self.client.hget(discord_id, field)
    
    def remove_user(self, discord_id):
        if self.client is None:
            self.connect()
        if self.client.exists(discord_id):
            riot_name = self.get_user_field(discord_id=discord_id, field="riot_user")
            self.client.delete(discord_id)
            return riot_name

    def get_all_users(self) -> list[str]:
        if self.client is None:
            self.connect()
        return self.client.keys('*')
