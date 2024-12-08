import redis
from redis.exceptions import ConnectionError
import time
from api.fandom import get_base_lodle_champ_data
from api.ddragon import get_champion_dict
class loldleDB():
    def __init__(self, url):
        self.url = url
        self.client = None
        pass

    def connect(self):
        try:
            ## NOTE: THIS DB DECODES RESPONSES
            self.client: redis.Redis[bytes] = redis.Redis.from_url(self.url, db=3, decode_responses=True)
        except ConnectionError:
            print("Cant connect to host")
    def store_champion(self, champion_name, attributes) -> None:
        """
        Stores a champion's attributes in a Redis hash, including a timestamp.
        
        :param champion_name: Name of the champion (used as the Redis key).
        :param attributes: A dictionary of attribute key-value pairs.
        """
        # Add a timestamp field to the attributes
        self.connect()
        attributes['timestamp'] = int(time.time())
        for key, value in attributes.items():
            if not isinstance(value, str):
                attributes[key] = str(value)
        # Store the data in Redis as a hash
        try:
            success = self.client.hset(champion_name, mapping=attributes)
        except Exception as e:
            succes = 0
            print(f"Error storing champion {champion_name}: {e}")
        return success

    async def populate_if_needed(self):
        if self.is_stale("Graves"):
            print("Loldle data outdated....")
            champs = list((await get_champion_dict()).values())
            for champ in champs:
                champ_attributes = await get_base_lodle_champ_data(champ)
                champion_name = champ_attributes.pop('Name', None)
                if champion_name:
                    self.store_champion(champion_name, champ_attributes)
        print("Population loldle data checked.")
    
    def get_champion(self, champion_name):
        """
        Retrieves a champion's data, including attributes and timestamp.
        
        :param champion_name: The name of the champion (Redis key).
        :return: A dictionary of champion attributes, including the timestamp.
        """
        self.connect()
        return self.client.hgetall(champion_name)
    
    def is_stale(self, champion_name, ttl=86400):
        """
        Checks if a champion's data is stale based on the `timestamp` field.
        
        :param champion_name: Name of the champion (Redis key).
        :param ttl: Time-to-live in seconds (default: 1 day).
        :return: True if the data is stale, False otherwise.
        """
        self.connect()
        print("Checking staleness")
        timestamp = self.client.hget(champion_name, 'timestamp')
        if timestamp:
            return (int(time.time()) - int(timestamp)) > ttl
        return True  # If no timestamp, consider the data stale    