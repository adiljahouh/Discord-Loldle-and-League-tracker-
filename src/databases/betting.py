import redis
from redis.exceptions import ConnectionError
from databases.main import MainDB


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

    # If the betting state is enabled, disable it
    def disable_betting(self):
        print("Betting disabled")
        if self.get_betting_state():
            self.connect()
            self.client.delete("enable")

    # Get the current betting state
    # Returns a boolean
    def get_betting_state(self):
        self.connect()
        state = self.client.get("enable")
        if state is None:
            return False
        return True if state.decode('utf8') == 'true' else False

    def store_bet(self, discord_id, author_discord_display_name, decision, amount):
        points = self.DB_MAIN.get_user_field(discord_id, "points")
        if points is None:
            print("Not enough points")
            return 0
        points = int(points.decode('utf8'))
        if points < amount:
            print("Not enough points")
            return 0
        self.connect()
        bet = self.get_bet(discord_id, decision)
        key = discord_id + "_" + decision
        try:
            if bet == 0:
                print("Bet does not exist")
                self.DB_MAIN.decrement_field(discord_id, "points", amount)
                self.client.hset(key, "amount", amount)
                self.client.hset(key, "discord_display_name", author_discord_display_name)
            else:
                print("Bet does exist, not changing")
                # self.client.hset(key, "amount", amount)
                print(self.client.hget(key, "amount"))
                return 2
        except ConnectionError as e:
            print(e)
            return 0
        print("Successful")
        return 1

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
                discord_display_name = self.client.hget(key, "discord_display_name")
                if amount is None or discord_display_name is None:
                    continue
                result[decision].append(
                    {"name": discord_display_name.decode('utf8'), "amount": amount.decode('utf8'), "discord_id": discord_id})
        print(result)
        return result

    def remove_all_bets(self):
        self.connect()
        for key in self.client.keys('*'):
            self.client.delete(key)
