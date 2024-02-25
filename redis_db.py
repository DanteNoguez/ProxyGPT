from redis import asyncio as aioredis
import json
import time
import os
from dotenv import load_dotenv
import logging
load_dotenv()

logger = logging.getLogger(__name__)

class RedisDB:
    def __init__(self, host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0):
        self.redis = aioredis.Redis(host=host, port=port, db=db)
        self.expire_time = 60*60*24*7 # 1 week
    
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
    
    async def get_total_usage(self, api_key):
        token_usage = await self.get_total_token_usage(api_key)
        request_count = await self.get_request_count(api_key)
        return {"token_usage": token_usage, "request_count": request_count}
    
    async def cache_request(self, request, response):
        await self.redis.set(request, response, ex=self.expire_time)

    async def get_cached_response(self, request):
        return await self.redis.get(request)