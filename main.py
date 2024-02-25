from fastapi import FastAPI, Request, HTTPException, Response, Security, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import httpx
import os
from dotenv import load_dotenv
import json
import logging
import secrets
import hashlib
from config import *
from redis_db import RedisDB
from models import GenerateKey

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(docs_url="/docs")
security = HTTPBearer()
REDIS_DB = RedisDB()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def validate_key(api_key_header: HTTPAuthorizationCredentials = Security(security)):
    hashed_key = hashlib.sha256(api_key_header.credentials.encode()).hexdigest()
    if not await REDIS_DB.check_api_key(hashed_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return True

async def validate_admin(api_key_header: HTTPAuthorizationCredentials = Security(security)):
    if api_key_header.credentials != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
        )
    return True

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    #ip = request.client.host
    if RATE_LIMIT:
        if request.url.path in ["/v1/chat/completions"]:
            api_key = request.headers.get("Authorization").replace("Bearer ", "")
            hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
            if not await REDIS_DB.rate_limit_check(hashed_key, NUM_MAX_REQUESTS, PERIOD):
                return Response(content="Too many requests, please try again later", status_code=429)
    response = await call_next(request)
    return response

@app.exception_handler(Exception)
async def uncaught_exception_handler(request: Request, exc: Exception):
    if DEBUG:
        return Response(content=f"Caught exception: {str(exc)}", status_code=500)
    return Response(content="Internal Server Error", status_code=500)

@app.get("/")
async def root():
    return {"status": True}

@app.post("/generate_key", include_in_schema=False)
async def generate_key(request: GenerateKey, token: HTTPAuthorizationCredentials = Security(validate_admin)):
    new_key = secrets.token_urlsafe(32)
    hashed_key = hashlib.sha256(new_key.encode()).hexdigest()
    await REDIS_DB.set(hashed_key, request.username)
    return {"api_key": new_key}

@app.get("/usage")
async def usage(request: Request, key: HTTPAuthorizationCredentials = Security(validate_key)):
    api_key = request.headers.get("Authorization").replace("Bearer ", "")
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    total_token_usage = await REDIS_DB.get_total_usage(hashed_key)
    return {"total_token_usage": total_token_usage}

async def stream_completion(data: dict, headers: dict, api_key: str):
    content_string = ""
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", "https://api.openai.com/v1/chat/completions", data=json.dumps(data), headers=headers) as response:
            async for chunk in response.aiter_raw():
                chunk_str = chunk.decode("utf-8").strip()
                for line in chunk_str.split("\n"):
                    if line.startswith('data:'):
                        try:
                            data_json = json.loads(line[5:])
                            content = data_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            content_string += content
                        except json.JSONDecodeError:
                            pass
                if b'[DONE]' in chunk:
                    break
                yield chunk
    await REDIS_DB.save_request_usage(api_key, len(content_string)/4)

@app.post("/v1/chat/completions")
async def chat_completions(request: Request, key: HTTPAuthorizationCredentials = Security(validate_key)):
    data = await request.json()
    headers = {
        "Authorization": f"Bearer {get_open_ai_key()}",
        "Content-Type": "application/json"
    }
    api_key = request.headers.get("Authorization").replace("Bearer ", "")
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    if data.get("stream") == True:
            return StreamingResponse(stream_completion(data, headers, hashed_key), media_type="text/event-stream")
    else:
        cached_response = await REDIS_DB.get_cached_response(json.dumps(data))
        if cached_response:
            try:
                return json.loads(cached_response)
            except Exception as e:
                logger.error(f"Error: {e}")
                pass
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", data=json.dumps(data), headers=headers)
            token_usage = response.json().get("usage").get("total_tokens")
            await REDIS_DB.save_request_usage(hashed_key, token_usage)
            await REDIS_DB.cache_request(json.dumps(data), json.dumps(response.text))
            return response.json()

async def startup_event():
    logger.info("Starting up...")

app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)