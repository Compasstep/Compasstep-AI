import time
import pylast
import ssl
import certifi
import requests
from functools import lru_cache
from typing import Dict, Optional
from app.core.logger import get_logger
from app.agent.constants import LASTFM_API_KEY, YOUTUBE_API_KEY

# logger 설정
logger = get_logger("app.agent.utils")

# SSL 설정
pylast.SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class MusicUtils:
    """공통적으로 사용할 Last.fm + YouTube 관련 유틸"""

    _network: Optional[pylast.LastFMNetwork] = None
    _lastfm_api_key: Optional[str] = LASTFM_API_KEY
    _youtube_api_key: Optional[str] = YOUTUBE_API_KEY

    _last_api_call = 0
    _min_api_interval = 0.1

    @classmethod
    def initialize_lastfm(cls) -> None:
        """Last.fm 네트워크 객체 초기화"""
        if cls._network is not None:
            return
        if not cls._lastfm_api_key:
            raise RuntimeError("LASTFM_API_KEY is not set in environment variables.")
        cls._network = pylast.LastFMNetwork(api_key=cls._lastfm_api_key)
        logger.info("Last.fm API initialized successfully.")

    @classmethod
    def get_network(cls) -> pylast.LastFMNetwork:
        """외부에서 안전하게 Last.fm 네트워크 객체 가져오기"""
        cls.initialize_lastfm()
        return cls._network

    @classmethod
    def rate_limit(cls) -> None:
        """API 호출 간 최소 간격을 보장"""
        now = time.time()
        if now - cls._last_api_call < cls._min_api_interval:
            time.sleep(cls._min_api_interval - (now - cls._last_api_call))
        cls._last_api_call = time.time()

    @classmethod
    @lru_cache(maxsize=100)
    def get_youtube_video_id(cls, query: str) -> Optional[str]:
        """YouTube API로 검색해 videoId 반환"""
        if not cls._youtube_api_key:
            logger.warning("YOUTUBE_API_KEY not configured. Skipping YouTube search.")
            return None
        cls.rate_limit()
        try:
            params = {
                'part': 'id',
                'q': query,
                'key': cls._youtube_api_key,
                'type': 'video',
                'maxResults': 1
            }
            response = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
            response.raise_for_status()
            data = response.json()
            if data.get('items'):
                return data['items'][0]['id']['videoId']
            return None
        except Exception as e:
            logger.error(f"YouTube search failed for query '{query}': {e}")
            return None

    @classmethod
    def get_youtube_url(cls, query: str) -> Optional[str]:
        """YouTube 검색 결과에서 url 생성"""
        vid = cls.get_youtube_video_id(query)
        return f"https://www.youtube.com/watch?v={vid}" if vid else None

    @classmethod
    def format_track_info(cls, track: pylast.Track) -> Dict[str, str]:
        """Last.fm Track 객체를 표준 dict 형태로 변환"""
        try:
            artist_name = track.get_artist().get_name()
            title = track.get_title()
            query = f"{artist_name} - {title}"
            return {
                "artist": artist_name,
                "title": title,
                "url": cls.get_youtube_url(query) or track.get_url()
            }
        except Exception as e:
            logger.error(f"Error formatting track info: {e}")
            return {"artist": "Unknown", "title": "Unknown", "url": ""}
