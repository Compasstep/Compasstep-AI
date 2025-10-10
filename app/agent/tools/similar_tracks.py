from typing import List, Dict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils

logger = get_logger("app.agent.tools.similar_tracks")

class SimilarTracks:
    _default_limit = 3

    @staticmethod
    @tool
    def get_similar_tracks(artist: str, track: str) -> List[Dict[str, str]]:
        """
        Finds similar songs by entering a track title and artist.

        Parameters:
        - track_title: The title of the track (e.g., "Good Day", "Gangnam Style").
        - artist_name: The name of the artist (use the English name if possible, e.g., "아이유" -> "IU", "싸이" -> "Psy").

        Returns:
        A list of track information [{"artist": "artist_name", "title": "track_title", "url": "link"}, ...].
        """
        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        if not artist.strip() or not track.strip():
            logger.warning("Empty artist or track provided to get_similar_tracks")
            return []

        try:
            network = MusicUtils.get_network()
            track_obj = network.get_track(artist.strip(), track.strip())
            similar_tracks = track_obj.get_similar(limit=SimilarTracks._default_limit)
        except Exception as e:
            logger.error(f"Failed to fetch similar tracks for '{artist} - {track}': {e}")
            return []

        results = []
        for wrapper in similar_tracks:
            try:
                track_info = MusicUtils.format_track_info(wrapper.item)
                results.append(track_info)
            except Exception as e:
                logger.error(f"Error processing similar track for '{artist} - {track}': {e}")
                continue

        return results
