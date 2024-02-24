from redis import asyncio as aioredis
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()

class RedisDB:
    def __init__(self, host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0):
        self.redis = aioredis.Redis(host=host, port=port, db=db)
    
    async def save_request_usage(self, api_key, token_usage):
        """Saves the token usage to Redis."""
        data = json.dumps({'token_usage': token_usage,
                           'timestamp': time.time()})
        await self.redis.rpush(f"requests:{api_key}", data)
        await self.redis.incr(f"counter:{api_key}")

    async def get_request_count(self, api_key):
        """Returns the amount of requests made by the user."""
        count = await self.redis.get(f"counter:{api_key}")
        return int(count) if count else 0
    
    async def get_total_token_usage(self, api_key):
        """Returns the total token usage for a given API key."""
        total_token_usage = 0
        request_list = await self.redis.lrange(f"requests:{api_key}", 0, -1)
        for request in request_list:
            data = json.loads(request)
            total_token_usage += data['token_usage']
        return total_token_usage
    
    async def cache_request(self, request, response):
        await self.redis.set(request, response)

    async def get_cached_response(self, request):
        return await self.redis.get(request)