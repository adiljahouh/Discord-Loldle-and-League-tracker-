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
        return self.client.hincrby(discord_id, field, str(neg_amount))

    def get_top_3_total_honor_users(self) -> list[tuple[str, int]]:
        """
        Retrieves the top 3 users based on their 'total_honors' field,
        considering ties for the third position.

        Returns:
            A list of tuples, where each tuple contains the discord_id (str)
            and the total_honors (int) of a user, sorted in descending order
            of total_honors. If multiple users share the same total_honors
            value as the 3rd ranked user, all of them are included.
            Returns an empty list if no users are found or no 'total_honors' data exists.
        """
        self.connect()
        all_users = self.get_all_users()

        honor_data = []
        for user_key_bytes in all_users:
            discord_id = user_key_bytes.decode('utf-8')
            total_honors_bytes = self.client.hget(discord_id, "total_honors")

            if total_honors_bytes is not None:
                try:
                    total_honors = int(total_honors_bytes.decode('utf-8'))
                    if total_honors > 0:
                        honor_data.append((discord_id, total_honors))
                except ValueError:
                    # Handle cases where total_honors might not be a valid integer
                    print(f"Warning: total_honors for user {discord_id} is not a valid integer: {total_honors_bytes}")
                    pass

        # Sort the users by total_honors in descending order
        honor_data.sort(key=lambda x: x[1], reverse=True)

        if not honor_data:
            return []

        top_users = []
        # Add the first two users if they exist
        if len(honor_data) >= 1:
            top_users.append(honor_data[0])
        if len(honor_data) >= 2:
            top_users.append(honor_data[1])

        # Find the threshold for the 3rd position
        third_place_score = -1  # Initialize with a value lower than any possible honor
        if len(honor_data) >= 3:
            third_place_score = honor_data[2][1]

        # Add users from the 3rd position onwards as long as their score matches the third_place_score
        for i in range(2, len(honor_data)):
            if honor_data[i][1] == third_place_score:
                top_users.append(honor_data[i])
            elif honor_data[i][1] < third_place_score and third_place_score != -1:
                # If we've passed the third place score (and it's not the initial -1), stop
                break
            elif third_place_score == -1 and i < 3:  # To handle cases with less than 3 unique scores
                top_users.append(honor_data[i])
            elif third_place_score == -1 and i >= 3:  # If there are fewer than 3 unique scores, and we've already added what's there, stop
                break

        return top_users

