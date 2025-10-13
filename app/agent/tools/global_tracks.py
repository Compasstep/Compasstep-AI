from typing import List, Dict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils

logger = get_logger("app.agent.tools.global_tracks")

class GlobalTracks:
    _default_limit = 3

    @staticmethod
    @tool
    def get_global_top_tracks() -> List[Dict[str, str]]:
        """
        Gets the list of the most popular tracks worldwide from Last.fm.

        Examples:
        - "Recommend the most popular songs in the world right now" -> get_global_top_tracks()
        - "Recommend popular songs" -> get_global_top_tracks()

        Returns:
        A list of track information [{"artist": "artist_name", "title": "track_title", "url": "link"}, ...].
        """
        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        try:
            network = MusicUtils.get_network()
            top_tracks = network.get_top_tracks(limit=GlobalTracks._default_limit)
        except Exception as e:
            logger.error(f"Failed to fetch global top tracks: {e}")
            return []

        results = []
        for wrapper in top_tracks:
            try:
                track_info = MusicUtils.format_track_info(wrapper.item)
                results.append(track_info)
            except Exception as e:
                logger.error(f"Error processing global track: {e}")
                continue

        return results
