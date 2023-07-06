import redis
from redis.exceptions import ConnectionError

class cacheDB():
    def __init__(self, url) -> None:
        self.url = url
        self.client = None
        pass

    def connect(self) -> None:
        try:
            self.client = redis.Redis.from_url(self.url, db=0)
        except ConnectionError:
            print("Cant connect to host")


    def store_user(self, discord_id, riot_user, puuid, author_discord_tag) -> None:
        if self.client is None:
            self.connect()
        self.client.hset(discord_id, "riot_user", riot_user)
        self.client.hset(discord_id, "puuid", puuid)
        self.client.hset(discord_id, "discord_tag", author_discord_tag)
    
    def get_user_field(self, discord_id, field):
        # field can be riot_user or puuid
        # e.g.  121210930139 -> meshh -> 12132323
        print("getting field")
        if self.client is None:
            self.connect()
        return self.client.hget(discord_id, field)
    
    def remove_user(self, discord_id):
        if self.client is None:
            self.connect()
        if self.client.exists(discord_id):
            self.client.delete(discord_id)
    def check_user(self):
        pass




# .register alazkav
# get disc user id -> 1231290431049 (uid discord)
# alazkav -> riot api -> wqerioewriewjjfnjdsfndskjfn (uid league)

# alazkav == 1231290431049 == wqerioewriewjjfnjdsfndskjfn


# .summary

# db.get(alazkav) -> riot userid + discord uid
# riot -> welke games heeft deze riot userid gespeeld?
# @1231290431049 league games