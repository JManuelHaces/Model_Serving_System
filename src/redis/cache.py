import json
import redis
import hashlib

from typing import Union


class RedisManager:
    """Redis Manager to save or get a value into cache memory
    """
    def __init__(self) -> None:
        self.redis_client = redis.Redis(host='redis', port='6379', decode_responses=True)
    
    @staticmethod
    def create_cache_key(model_name: str, input_data: dict) -> str:
        """Creates a key for the redis cache
        Args:
            model_name (str): Model Name and Version
            input_data (dict): Inputs given to the model
        Returns:
            str: Hashed key
        """
        # Input to sorted string
        input_str = json.dumps(input_data, sort_keys=True)
        # Hashing with MD5
        input_hash = hashlib.md5(input_str.encode()).hexdigest()
        return f"{model_name}:{input_hash}"

    async def save_to_cache(self, key: str, value: str, expiration: int = 3600) -> None:
        """Saves a value into redis with expiration
        Args:
            key (str): Key of the value
            value (str): Value
            expiration (int, optional): Expiration time for the data. Defaults to 3600 (1hr).
        """
        self.redis_client.set(key, json.dumps(value), ex=expiration)
    
    async def get_from_cache(self, key: str) -> Union[str, None]:
        """Retrieves a value from the cache
        Args:
            key (_type_): _description_
        Returns:
            Union[str, None]: When theres a value matching the key it will give the value, if not it will return None
        """
        resp = self.redis_client.get(key)
        if resp:
            return json.loads(resp)
        return None