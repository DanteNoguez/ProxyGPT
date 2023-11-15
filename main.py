from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import time
import uvicorn
from config import *

app = FastAPI()

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
    api_key_used = request.headers.get("Authorization")
    print(f"API key used: {api_key_used}")

    current_time = int(time.time() * 1000)  # Current time in milliseconds
    ip_data = rate_limit.get(ip, {"requests": 0, "lastRequestTime": current_time})

    if current_time - ip_data["lastRequestTime"] > PERIOD:
        rate_limit[ip] = {"requests": 1, "lastRequestTime": current_time}
    else:
        ip_data["requests"] += 1
        if ip_data["requests"] > RATE_LIMIT:
            return Response(
                content="Too many requests, please try again later",
                status_code=429
            )
        rate_limit[ip] = ip_data

    response = await call_next(request)
    return response


@app.exception_handler(Exception)
async def uncaught_exception_handler(request: Request, exc: Exception):
    if DEBUG:
        return Response(content=f"Caught exception: {str(exc)}", status_code=500)
    return Response(content="Internal Server Error", status_code=500)

# Routes
@app.get("/")
async def root():
    return {
        "status": True,
    }

@app.post("/v1/completions")
async def completions(request: Request):
    # Your implementation for the completions route
    data = await request.json()
    return {"result": "Completion result here"}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # Your implementation for the chat completions route
    data = await request.json()
    return {"result": "Chat completion result here"}

# Start server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
