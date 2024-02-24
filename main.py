from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import time
import uvicorn
import httpx
import os
from dotenv import load_dotenv
import json
import logging
from config import *
from redis_db import RedisDB

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limit = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host
    logger.debug(f"IP: {ip}")
    api_key_used = request.headers.get("Authorization")
    #logger.debug(f"API key used: {api_key_used}")

    # current_time = int(time.time() * 1000)  # Current time in milliseconds
    # ip_data = rate_limit.get(ip, {"requests": 0, "lastRequestTime": current_time})

    # if current_time - ip_data["lastRequestTime"] > PERIOD:
    #     rate_limit[ip] = {"requests": 1, "lastRequestTime": current_time}
    # else:
    #     ip_data["requests"] += 1
    #     if ip_data["requests"] > RATE_LIMIT:
    #         return Response(
    #             content="Too many requests, please try again later",
    #             status_code=429
    #         )
    #     rate_limit[ip] = ip_data

    response = await call_next(request)
    return response


@app.exception_handler(Exception)
async def uncaught_exception_handler(request: Request, exc: Exception):
    if DEBUG:
        return Response(content=f"Caught exception: {str(exc)}", status_code=500)
    return Response(content="Internal Server Error", status_code=500)

@app.get("/")
async def root():
    return {
        "status": True,
    }

@app.post("/test")
async def test(request: Request, name: str):
    print("Received request")
    data = await request.json()
    logger.info(f"Received data: {data}")
    return {
        "status": True, "data": data, "name": name
    }

async def stream_completion(data, headers):
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", "https://api.openai.com/v1/chat/completions", data=json.dumps(data), headers=headers) as response:
                async for chunk in response.aiter_raw():
                    if b'[DONE]' in chunk:
                         break
                    yield chunk

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    data = await request.json()
    headers = {
        "Authorization": f"Bearer {get_open_ai_key()}",
        "Content-Type": "application/json"
    }
    if data.get("stream") == True:
            return StreamingResponse(stream_completion(data, headers), media_type="text/event-stream")
    else:
         async with httpx.AsyncClient() as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", data=json.dumps(data), headers=headers)
            return response.json()
         

async def startup_event():
    logger.info("Starting up...")
    # Example Usage
    tracker = RedisDB()
    api_key = 'user123'
    request_data = {'query': 'how to use Redis'}
    await tracker.save_request_usage(api_key, request_data)
    request_count = await tracker.get_request_count(api_key)
    print("Request count for 'user123':", request_count)
    logger.info("Startup complete")

app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)