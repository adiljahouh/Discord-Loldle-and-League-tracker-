import redis
from redis.exceptions import ConnectionError

class MainDB():
    def __init__(self, url) -> None:
        self.url = url
        self.client = None
        pass

    def connect(self):
        try:
            self.client: redis.Redis[bytes] = redis.Redis.from_url(self.url, db=0)
        except ConnectionError:
            print("Cant connect to host")

    

    def store_user(self, discord_id, riot_user, puuid, author_discord_tag, strikes=0, points=500) -> None:
        self.connect()
        self.client.hset(discord_id, "riot_user", riot_user)
        self.client.hset(discord_id, "puuid", puuid)
        self.client.hset(discord_id, "discord_tag", author_discord_tag)
        self.client.hset(discord_id, "strikes", strikes)
        self.client.hset(discord_id, "points", 500)
    
    def get_user_field(self, discord_id, field) -> (bytes|None):
        # field can be riot_user or puuid, strikes, daily
        # e.g.  121210930139 -> meshh -> 12132323
        self.connect()
        return self.client.hget(discord_id, field)
    
    def set_user_field(self, discord_id, field, value) -> (bytes|None):
        # field can be riot_user or puuid
        # e.g.  121210930139 -> meshh -> 12132323
        self.connect()
        return self.client.hset(discord_id, field, value)
    
    def remove_user(self, discord_id):
        self.connect()
        if self.client.exists(discord_id):
            self.client.delete(discord_id)
            return True
    def remove_and_return_all(self, discord_id):
        self.connect()
        if self.client.exists(discord_id):
            all_info: dict = self.client.hgetall(discord_id)
            self.client.delete(discord_id)
            return all_info
    
    def get_all_users(self) -> list[str]:
        self.connect()
        return self.client.keys('*')
    
    def check_user_existence(self, discord_id):
        self.connect()
        return self.client.exists(str(discord_id))
    
    def increment_field(self, discord_id, field, amount=1):
        self.connect()
        return self.client.hincrby(discord_id, field, amount)
    
    def decrement_field(self, discord_id, field, amount=1):
        self.connect()
        neg_amount = -int(amount)
        print(neg_amount)
        return self.client.hincrby(discord_id, field, str(neg_amount))