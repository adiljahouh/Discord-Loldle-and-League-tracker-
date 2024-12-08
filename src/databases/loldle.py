import redis
from redis.exceptions import ConnectionError
import time
from api.fandom import get_base_lodle_champ_data
from api.ddragon import get_champion_dict, get_latest_ddragon
import json
import asyncio
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
        
        :param champion_name: Name of the champion (used as the Redis key) FROM DDRAG (USEABLE IN LINKS)
        :param attributes: A dictionary of attribute key-value pairs.
        """
        # Add a timestamp field to the attributes
        self.connect()
        attributes['timestamp'] = int(time.time())
        attributes_json = json.dumps(attributes)
    
    # Store the data in Redis
        try:
            success = self.client.set(champion_name, attributes_json)
        except Exception as e:
            success = 0
            print(f"Error storing champion {champion_name}: {e}")
        return success

    async def populate_if_needed(self):
        if self.is_stale("Zeri"):
            print("Loldle data outdated....")
            ddrag_version = await get_latest_ddragon()
            champs = list((await get_champion_dict(ddrag_version)).values())
            batch_size = 3  # Adjust based on your system's capabilities
            async def process_champ(champ):
                champ_attributes = await get_base_lodle_champ_data(ddrag_version, champ)
                # champion_name = champ_attributes['Name']
                ## add the ddrag name
                if champ:
                    self.store_champion(champ, champ_attributes)

            # Create tasks in batches
            for i in range(0, len(champs), batch_size):
                batch = champs[i:i + batch_size]
                await asyncio.gather(*(process_champ(champ) for champ in batch))
        print("Population loldle data checked.")
    
    def get_champion_info(self, champion_name):
        """
        Retrieves a champion's data, including attributes and timestamp.
        
        :param champion_name: The name of the champion (Redis key) FROM DDRAG.
        :return: A dictionary of champion attributes, including the timestamp.
        """
        self.connect()
        return json.loads(self.client.get(champion_name))
    def get_random_champion_name(self):
        self.connect()
        return self.client.randomkey()
    def get_all_champ_keys(self):
        self.connect()
        return self.client.keys('*')
    def is_stale(self, champion_name, ttl=86400*14):
        """
        Checks if a champion's data is stale based on the `timestamp` field.
        
        :param champion_name: Name of the champion (Redis key).
        :param ttl: Time-to-live in seconds (default: 1 day).
        :return: True if the data is stale, False otherwise.
        """
        self.connect()
        print("Checking staleness")
        try:
            timestamp = self.get_champion_info(champion_name)['timestamp']
        except TypeError:
            return True
        if timestamp:
            return (int(time.time()) - int(timestamp)) > ttl
        return True  # If no timestamp, consider the data stale    