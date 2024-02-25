import random
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

RATE_LIMIT = True
NUM_MAX_REQUESTS = 10  # Number of requests
PERIOD = 60  # Period in seconds
SERVER_PORT = 8081
DEBUG = True
OPENAI_KEYS = os.getenv('OPENAI_KEYS').split(',')

def get_open_ai_key():
    return random.choice(OPENAI_KEYS)