from typing import List, Dict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils

# logger 설정
logger = get_logger("app.agent.tools.tag_tracks")


class TagTracks:
    _default_limit = 4

    @staticmethod
    @tool("get_tracks_by_tag")
    def get_tracks_by_tag(tag: str) -> List[Dict[str, str]]:
        """
        Recommends tracks corresponding to a given music tag.

        Examples:
        - "Recommend some exciting music" -> get_tracks_by_tag("upbeat")
        - "Recommend some sad music" -> get_tracks_by_tag("sad")

        Parameters:
        - tag: The music tag (e.g., "upbeat"). Only one tag should be entered.

        Returns:
        A list of track information [{"artist": "artist_name", "title": "track_title", "url": "link"}, ...].
        """

        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        if not tag or not tag.strip():
            logger.warning("Empty tag provided to get_tracks_by_tag")
            return []

        try:
            network = MusicUtils.get_network()
            tag_obj = network.get_tag(tag.strip())
            top_tracks = tag_obj.get_top_tracks(limit=TagTracks._default_limit)
        except Exception as e:
            logger.error(f"Failed to fetch tracks for tag '{tag}': {e}")
            return []

        results = []
        for wrapper in top_tracks:
            try:
                track_info = MusicUtils.format_track_info(wrapper.item)
                if track_info["artist"] != "Unknown":
                    results.append(track_info)
            except Exception as e:
                logger.error(f"Error processing track for tag '{tag}': {e}")
                continue

        return results
