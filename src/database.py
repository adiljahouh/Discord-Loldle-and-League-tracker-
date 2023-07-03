import redis
from redis.exceptions import ConnectionError
class cacheDB():
    def __init__(self, url, port) -> None:
        self.url = url
        self.port = port
        self.client = None
        pass

    def connect(self) -> None:
        try:
            self.client = redis.Redis.from_url(self.url)
            print("connected")
            self.client.select(0)
            print("yes")
            self.client.hset("users", "disc_user", "riot_user")
            print('yeet')
            test = self.client.hget("users", "disc_user")
            print(test)
        except ConnectionError:
            print("Connection error with redis")

    def store_user(self, disc_user, riot_user):
        if self.client is None:
            print("Attempting to reconnecting..")
            # self.connect()
            print("connected.")
        self.client.hset("users", disc_user, riot_user)

        
        pass

    def remove_user(self):
        pass
    
    def check_user(self):
        pass


db1 = cacheDB(url="redis://default:redispw@localhost:32768", port=32768)
db1.connect()
# db1.store_user("adil4300", "meshh")