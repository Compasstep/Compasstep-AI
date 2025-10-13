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
    def get_youtube_thumbnail_urls(cls, video_id: str) -> Dict[str, str]:
        """
        주어진 YouTube video_id에 대한 썸네일 URL 모음 반환.
        일부 영상은 sd/maxres가 없을 수 있으니, 사용처에서 Fallback 순서를 정해 쓰세요.
        """
        base = f"https://i.ytimg.com/vi/{video_id}"
        return {
            "default": f"{base}/default.jpg",     # 120x90
            "mq": f"{base}/mqdefault.jpg",        # 320x180
            "hq": f"{base}/hqdefault.jpg",        # 480x360
            "sd": f"{base}/sddefault.jpg",        # 640x480 (없을 수 있음)
            "maxres": f"{base}/maxresdefault.jpg" # 1280x720 (없을 수 있음)
        }

    @classmethod
    def get_youtube_basic_info(cls, query: str) -> Optional[Dict[str, str]]:
        """
        검색 쿼리로 YouTube Data API(search.list, part=snippet)를 호출해
        videoId, title, channelName, thumbnailUrl, youtubeUrl 을 1개 반환.
        """
        if not cls._youtube_api_key:
            logger.warning("YOUTUBE_API_KEY not configured. Skipping YouTube search.")
            return None

        cls.rate_limit()
        try:
            params = {
                "part": "snippet",
                "q": query,
                "key": cls._youtube_api_key,
                "type": "video",
                "maxResults": 1,
                "safeSearch": "none",
            }
            resp = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items") or []
            if not items:
                return None

            item = items[0]
            vid = item["id"]["videoId"]
            snip = item.get("snippet") or {}
            thumbs = snip.get("thumbnails") or {}

            def _pick(d): return (d or {}).get("url")
            thumbnail_url = (
                _pick(thumbs.get("maxres"))
                or _pick(thumbs.get("standard"))
                or _pick(thumbs.get("high"))
                or _pick(thumbs.get("medium"))
                or _pick(thumbs.get("default"))
                or ""
            )

            return {
                "videoId": vid,
                "title": snip.get("title", ""),
                "channelName": snip.get("channelTitle", ""),
                "thumbnailUrl": thumbnail_url,
                "youtubeUrl": f"https://www.youtube.com/watch?v={vid}",
            }
        except Exception as e:
            logger.error(f"YouTube basic info failed for query '{query}': {e}")
            return None

    @classmethod
    def format_track_info(cls, track: pylast.Track) -> Dict[str, str]:
        """
        Last.fm Track → 요구 스키마:
        { videoId, title, channelName, thumbnailUrl, youtubeUrl }
        """
        try:
            artist_name = track.get_artist().get_name()
            track_title = track.get_title()
            query = f"{artist_name} - {track_title}"

            # 1순위: YouTube snippet 기반 정확 정보
            yt = cls.get_youtube_basic_info(query)
            if yt:
                return yt

            # 2순위: videoId + 정적 썸네일로 최소 구성
            vid = cls.get_youtube_video_id(query)
            if vid:
                thumbs = cls.get_youtube_thumbnail_urls(vid)
                return {
                    "videoId": vid,
                    "title": f"{artist_name} - {track_title}",
                    "channelName": "",
                    "thumbnailUrl": thumbs.get("hq") or thumbs.get("mq") or thumbs.get("default") or "",
                    "youtubeUrl": f"https://www.youtube.com/watch?v={vid}",
                }

            # 3순위: 전혀 못 찾았을 때 안전값
            return {
                "videoId": "",
                "title": f"{artist_name} - {track_title}",
                "channelName": "",
                "thumbnailUrl": "",
                "youtubeUrl": "",
            }

        except Exception as e:
            logger.error(f"Error formatting track info: {e}")
            return {
                "videoId": "",
                "title": "Unknown",
                "channelName": "",
                "thumbnailUrl": "",
                "youtubeUrl": "",
            }
