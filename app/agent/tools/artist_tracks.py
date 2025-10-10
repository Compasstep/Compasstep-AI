from typing import List, Dict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils

logger = get_logger("app.agent.tools.artist_tracks")

class ArtistTracks:
    _default_limit = 5

    @staticmethod
    @tool
    def get_top_tracks_by_artist(artist: str) -> List[Dict[str, str]]:
        """
        Gets the top popular tracks for a specific artist.

        Examples:
        - "Recommend songs by IU" -> get_top_tracks_by_artist("IU")
        - "Recommend songs by BTS" -> get_top_tracks_by_artist("BTS")

        Parameters:
        - - artist: The name of the artist (e.g., "BTS").

        Returns:
        A list of track information [{"artist": "artist_name", "title": "track_title", "url": "link"}, ...].
        """
        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        if not artist or not artist.strip():
            logger.warning("Empty artist provided to get_top_tracks_by_artist")
            return []

        try:
            network = MusicUtils.get_network()
            artist_obj = network.get_artist(artist.strip())
            top_tracks = artist_obj.get_top_tracks(limit=ArtistTracks._default_limit)
        except Exception as e:
            logger.error(f"Failed to fetch tracks for artist '{artist}': {e}")
            return []

        results = []
        for wrapper in top_tracks:
            try:
                track_info = MusicUtils.format_track_info(wrapper.item)
                results.append(track_info)
            except Exception as e:
                logger.error(f"Error processing track for artist '{artist}': {e}")
                continue

        return results
