import redis
from redis.exceptions import ConnectionError

"""
    DB layout
    key: <ign>, has field: status, with value <True/False>
    Keys are the users getting stalked
    Status is if the user is currently getting bet on
"""
class StalkingDB():
    def __init__(self, url):
        self.url = url
        self.client = None
        self.current_game = 0
        self.custom = False
        pass

    def connect(self):
        try:
            self.client: redis.Redis[bytes] = redis.Redis.from_url(self.url, db=2)
        except ConnectionError:
            print("Cant connect to host")

    def store_user(self, ign):
        self.connect()
        self.client.hset(ign, "status", str(False))

    def remove_user(self, ign):
        self.connect()
        self.client.delete(ign)

    def change_status(self, ign, status):
        self.connect()
        self.client.hset(ign, "status", str(status))

    def get_all_users(self):
        self.connect()
        clients = self.client.keys('*')
        return [str(client.decode('utf-8')) for client in clients]

    def get_user_status(self, ign):
        self.connect()
        status = self.client.hget(ign, "status")
        return status.decode('utf-8') == 'True'

    def get_active_user(self):
        self.connect()
        clients = self.client.keys('*')
        clients_deco = [str(client.decode('utf-8')) for client in clients]
        for client in clients_deco:
            if self.get_user_status(client):
                return client
        return None



