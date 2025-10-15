from typing import List, Dict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils

logger = get_logger("app.agent.tools.country_tracks")

class CountryTracks:
    _default_limit = 4

    @staticmethod
    @tool
    def get_top_tracks_by_country(country: str) -> List[Dict[str, str]]:
        """
        Retrieves the top popular tracks for a specific country.

        Assumption
        - The caller extracts the country from the user's query and normalizes it to an
          ISO 3166-1 official English short name (e.g., "Korea, Republic of", "United States")
          BEFORE calling this function.

        Parameters
        - country (str): ISO 3166-1 official English short name.
          Examples: "Korea, Republic of", "United States", "United Kingdom", "Viet Nam".
        Returns:
        [
          {"videoId","title","channelName","thumbnailUrl","youtubeUrl"},
          ...
        ]
        """
        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        if not country or not country.strip():
            logger.warning("Empty country provided to get_top_tracks_by_country")
            return []

        try:
            network = MusicUtils.get_network()
            top_tracks = network.get_geo_top_tracks(
                country=country.strip(),
                limit=CountryTracks._default_limit
            )
        except Exception as e:
            logger.error(f"Failed to fetch top tracks for country '{country}': {e}")
            return []

        results: List[Dict[str, str]] = []
        for wrapper in top_tracks:
            try:
                results.append(MusicUtils.format_track_info(wrapper.item))
            except Exception as e:
                logger.error(f"Error processing track for country '{country}': {e}")
        return results
