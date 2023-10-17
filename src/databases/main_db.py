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

    def get_user_field(self, discord_id, field) -> (bytes | None):
        # field can be riot_user or puuid, strikes, daily
        # e.g.  121210930139 -> meshh -> 12132323
        self.connect()
        return self.client.hget(discord_id, field)

    def set_user_field(self, discord_id, field, value) -> (bytes | None):
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
    
    def get_all_users_sorted_by_field(self, field, desc, start, number) -> list[str, int]:
        # Does only work if the field stores somes kind of integer :)
        self.connect()
        # for i in self.get_all_users():
        #     print(i.decode('utf-8'))
        #     print("points",  self.get_user_field(i.decode('utf-8'), "points"))
        combo = [[user.decode('utf-8'), self.get_user_field(user.decode('utf-8'), field)] for user in self.get_all_users()]
        combo = [[user[0], int(user[1].decode('utf-8'))] for user in combo if user[1] is not None]
        print("combo" ,combo)
        combo.sort(key=lambda x: x[1], reverse=desc)
        # This just works for some reason
        # Idk why but it does not error even when accessing elements outside of the array
        return combo[start:start+number]

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
