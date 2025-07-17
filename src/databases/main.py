import redis
from redis.exceptions import ConnectionError
from typing import List, Tuple

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

    def store_user(self, discord_id, riot_user, puuid, author_discord_tag, strikes=0, points=500, strike_1="", strike_2="", strike_3="", total_strikes=0, strike_quota=3, total_honors = 0) -> None:
        self.connect()
        self.client.hset(discord_id, "riot_user", riot_user)
        self.client.hset(discord_id, "puuid", puuid)
        self.client.hset(discord_id, "discord_tag", author_discord_tag)
        self.client.hset(discord_id, "strikes", strikes) # strike count on user
        self.client.hset(discord_id, "lifetime_strikes", total_strikes) # life_time strike count
        self.client.hset(discord_id, "points", points)
        self.client.hset(discord_id, "total_honors", total_honors)
        self.client.hset(discord_id, "strike_1", strike_1)
        self.client.hset(discord_id, "strike_2", strike_2)
        self.client.hset(discord_id, "strike_3", strike_3)
        self.client.hset(discord_id, "strike_quota", strike_quota) # strikes you can give
        
    def get_user(self, discord_id) -> dict:
        self.connect()
        user_data = self.client.hgetall(discord_id)
        if user_data:
            # Convert byte literals to strings if needed
            user_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in user_data.items()}
        return user_data
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
    
    def get_all_users_sorted_by_field(self, field, desc, start, number) -> list[tuple[str, int]]:
        # Does only work if the field stores somes kind of integer :)
        self.connect()
        user_field_combo = [(user.decode('utf-8'), self.get_user_field(user.decode('utf-8'), field)) 
                            for user in self.get_all_users()]
        user_field_combo = [(username, int(raw_val.decode('utf-8'))) 
                            for username, raw_val in user_field_combo if raw_val is not None]
        user_field_combo.sort(key=lambda x: x[1], reverse=desc)
        return user_field_combo[start:start+number]

    def check_user_existence(self, discord_id):
        self.connect()
        return self.client.exists(str(discord_id))

    def increment_field(self, discord_id, field, amount=1):
        self.connect()
        return self.client.hincrby(discord_id, field, amount)

    def decrement_field(self, discord_id, field, amount=1):
        self.connect()
        neg_amount = -int(amount)
        return self.client.hincrby(discord_id, field, str(neg_amount))

    def get_most_honorable(self, top=3) -> list[tuple[str, int]]:
        """
        Retrieves the top amount of users based on their 'total_honors' field,
        considering ties for the third position.

        Returns:
            A list of tuples, where each tuple contains the discord_id (str)
            and the total_honors (int) of a user, sorted in descending order
            of total_honors. If multiple users share the same total_honors
            value as the 3rd ranked user, all of them are included.
            Returns an empty list if no users are found or no 'total_honors' data exists.
        """
        self.connect()
        all_users = self.get_all_users()                   # list of user keys (bytes)
        user_count = len(all_users)

        users_to_honors = self.get_all_users_sorted_by_field(
            field="total_honors",
            desc=True,
            start=0,
            number=user_count
        )  # -> list[tuple[str, int]]

        if not users_to_honors:
            return []

        cutoff_index = min(top, len(users_to_honors)) - 1
        cutoff_score = users_to_honors[cutoff_index][1]

        honorable = [(user, honor) for user, honor in users_to_honors if honor >= cutoff_score]
        return honorable
