import redis
from redis.exceptions import ConnectionError
from main_db import MainDB


class BettingDB():
    def __init__(self, url) -> None:
        self.url = url
        self.client = None
        self.DB_MAIN = MainDB(self.url)
        self.betting_time = 600
        pass

    def connect(self):
        try:
            self.client: redis.Redis[bytes] = redis.Redis.from_url(self.url, db=1)
        except ConnectionError:
            print("Cant connect to host")

    # Enable betting for self.betting_time amount of time
    def enable_betting(self):
        print("Betting enabled")
        self.connect()
        self.client.set("enable", "true")
        self.client.expire("enable", time=self.betting_time)

    # Get the current betting state
    # Returns a boolean
    def get_betting_state(self):
        self.connect()
        state = self.client.get("enable")
        if state is None:
            return False
        return True if state.decode('utf8') == 'true' else False

    def store_bet(self, discord_id, author_discord_tag, decision, amount):
        points = self.DB_MAIN.get_user_field(discord_id, "points")
        if points is None:
            print("Not enough points")
            return False
        points = int(points.decode('utf8'))
        if points <= amount:
            print("Not enough points")
            return False
        self.DB_MAIN.decrement_field(discord_id, "points", amount)
        self.connect()
        bet = self.get_bet(discord_id, decision)
        key = discord_id + "_" + decision
        try:
            if bet == 0:
                print("Bet does not exist")
                self.client.hset(key, "amount", amount)
                self.client.hset(key, "discord_tag", author_discord_tag)
            else:
                print("Bet does exist")
                self.client.hincrby(key, "amount", amount)
                print(self.client.hget(key, "amount"))
        except ConnectionError as e:
            print(e)
            return False
        print("Successful")
        return True

    # Get current bet, 0 if fields/keys do not exist
    def get_bet(self, discord_id, decision):
        self.connect()
        key = discord_id + "_" + decision
        bet = self.client.hget(key, "amount")
        if bet is None:
            bet = 0
        else:
            bet = bet.decode('utf-8')
        return bet

    # Output {'believers': [{name: "", amount: 0, "discord_id": id}], 'doubters': [{name: "", amount: 0, "discord_id": id}]}
    def get_all_bets(self):
        print("Getting all bets")
        result = {'believers': [], 'doubters': []}
        users = self.DB_MAIN.get_all_users()
        users = [user.decode('utf8') for user in users]
        self.connect()
        for discord_id in users:
            for decision in ['believers', 'doubters']:
                key = discord_id + "_" + decision
                amount = self.client.hget(key, "amount")
                discord_tag = self.client.hget(key, "discord_tag")
                if amount is None or discord_tag is None:
                    continue
                result[decision].append(
                    {"name": discord_tag.decode('utf8'), "amount": amount.decode('utf8'), "discord_id": discord_id})
        print(result)
        return result

    def remove_all_bets(self):
        self.connect()
        for key in self.client.keys('*'):
            self.client.delete(key)
