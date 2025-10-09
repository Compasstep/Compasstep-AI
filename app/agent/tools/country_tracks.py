from typing import List, Dict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils

logger = get_logger("app.agent.tools.country_tracks")

class CountryTracks:
    _default_limit = 5

    @staticmethod
    @tool
    def get_top_tracks_by_country(country: str) -> List[Dict[str, str]]:
        """
        Retrieves the top popular tracks for a specific country.

        Parameters:
        - country: The English name of the country (e.g., "South Korea", "Japan", "Brazil").

        Returns:
        A list of track information [{"artist": "artist_name", "title": "track_title", "url": "link"}, ...].
        """
        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        if not country or not country.strip():
            logger.warning("Empty country provided to get_top_tracks_by_country")
            return []

        try:
            top_tracks = MusicUtils._network.get_geo_top_tracks(country=country.strip(), limit=CountryTracks._default_limit)
        except Exception as e:
            logger.error(f"Failed to fetch top tracks for country '{country}': {e}")
            return []

        results = []
        for wrapper in top_tracks:
            try:
                track_info = MusicUtils.format_track_info(wrapper.item)
                results.append(track_info)
            except Exception as e:
                logger.error(f"Error processing track for country '{country}': {e}")
                continue

        return results
