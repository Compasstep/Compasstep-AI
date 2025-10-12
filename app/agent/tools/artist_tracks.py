from typing import List, Dict, Optional
from functools import lru_cache
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils

logger = get_logger("app.agent.tools.artist_tracks")

class ArtistTracks:
    _default_limit = 5

    @staticmethod
    @lru_cache(maxsize=512)
    def fetch_top_tracks_by_artist(artist: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        재사용 가능한 순수 로직 함수
        - 다른 툴/서비스/라우터에서 직접 호출 가능
        """
        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        if not artist or not artist.strip():
            logger.warning("Empty artist provided to fetch_top_tracks_by_artist")
            return []

        limit = limit or ArtistTracks._default_limit

        try:
            network = MusicUtils.get_network()
            artist_obj = network.get_artist(artist.strip())
            top_tracks = artist_obj.get_top_tracks(limit=limit)
        except Exception as e:
            logger.error(f"Failed to fetch tracks for artist '{artist}': {e}")
            return []

        results: List[Dict[str, str]] = []
        for wrapper in top_tracks:
            try:
                info = MusicUtils.format_track_info(wrapper.item)  # {"artist","title","url"}
                results.append(info)
            except Exception as e:
                logger.error(f"Error processing track for artist '{artist}': {e}")
                continue

        return results

    @staticmethod
    @tool("get_top_tracks_by_artist")
    def get_top_tracks_by_artist(artist: str) -> List[Dict[str, str]]:
        """
        Gets the top popular tracks for a specific artist.

        Examples:
        - "Recommend songs by IU" -> get_top_tracks_by_artist("IU")
        - "Recommend songs by BTS" -> get_top_tracks_by_artist("BTS")

        Parameters:
        - artist: The name of the artist (e.g., "BTS").

        Returns:
        A list of track information [{"artist": "artist_name", "title": "track_title", "url": "link"}, ...].
        """
        # 툴 래퍼는 내부의 순수 함수만 호출
        return ArtistTracks.fetch_top_tracks_by_artist(artist, limit=ArtistTracks._default_limit)
