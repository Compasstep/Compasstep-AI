# agent/constants.py
import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# Music APIs
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
