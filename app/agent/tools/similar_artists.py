from typing import List, Dict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils

logger = get_logger("app.agent.tools.similar_artists")

class SimilarArtists:
    _default_limit = 1

    @staticmethod
    @tool
    def get_similar_artists(artist: str) -> List[Dict[str, str]]:
        """
        Finds artists similar to a specific artist.

        Examples:
        - "Find artists similar to BTS" -> get_similar_artists("BTS")
        - "Find artists similar to IU" -> get_similar_artists("IU")

        Parameters:
        - artist_name: The name of the reference artist (e.g., "BTS").

        Returns:
        A list of dictionaries, each with the artist's 'name' and 'url'.
        e.g., [{"name": "artist1", "url": "url_to_artist1"}, ...].
        """
        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        if not artist or not artist.strip():
            logger.warning("Empty artist provided to get_similar_artists")
            return []

        try:
            network = MusicUtils.get_network()
            artist_obj = network.get_artist(artist.strip())
            similar_artists = artist_obj.get_similar(limit=SimilarArtists._default_limit)
        except Exception as e:
            logger.error(f"Failed to fetch similar artists for '{artist}': {e}")
            return []

        results = []
        for wrapper in similar_artists:
            try:
                results.append({"artist": wrapper.item.get_name()})
            except Exception as e:
                logger.error(f"Error processing similar artist for '{artist}': {e}")
                continue

        return results
