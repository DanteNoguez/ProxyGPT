import random
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

RATE_LIMIT = 1000 
PERIOD = 60 * 1000  # Period in milliseconds
SERVER_PORT = 8081
DEBUG = True
OPENAI_KEYS = os.getenv('OPENAI_KEYS').split(',')

def get_open_ai_key():
    return random.choice(OPENAI_KEYS)