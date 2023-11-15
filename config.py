import random
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

RATE_LIMIT = 100 
PERIOD = 60 * 1000  # Period in milliseconds
SERVER_PORT = 3000
DEBUG = True
OPENAI_KEYS = []

def get_open_ai_key():
    return random.choice(OPENAI_KEYS)