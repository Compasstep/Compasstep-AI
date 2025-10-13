from typing import List, Dict
from langchain_core.tools import tool
from app.core.logger import get_logger
from app.agent.utils import MusicUtils
from app.agent.tools.artist_tracks import ArtistTracks

logger = get_logger("app.agent.tools.similar_artists")

class SimilarArtists:
    _default_similar_limit = 4
    _default_tracks_per_artist = 1

    @staticmethod
    @tool("get_similar_artists")
    def get_similar_artists(
        artist: str,
        similar_limit: int = _default_similar_limit,
        tracks_per_artist: int = _default_tracks_per_artist,
    ) -> List[Dict[str, str]]:
        """
        Finds artists similar to a specific artist and (optionally) recommends their top tracks.

        Examples:
        - "Find artists similar to BTS" -> get_similar_artists("BTS")
        - "Find songs by artists similar to IU" -> get_similar_artists("IU", tracks_per_artist=1)

        Parameters:
        - artist: The seed artist name (e.g., "BTS").
        - similar_limit: How many similar artists to fetch (default: 4).
        - tracks_per_artist: How many top tracks per similar artist to include.
          If 0, only similar artist names are returned.

        Returns:
        [
          {"videoId","title","channelName","thumbnailUrl","youtubeUrl"},
          ...
        ]
        """
        MusicUtils.initialize_lastfm()
        MusicUtils.rate_limit()

        if not artist or not artist.strip():
            logger.warning("Empty artist provided to get_similar_artists")
            return []

        seed = artist.strip()
        k = max(1, int(tracks_per_artist))  # 스키마 통일을 위해 최소 1로 강제

        # 1) 유사 아티스트 조회
        try:
            network = MusicUtils.get_network()
            artist_obj = network.get_artist(seed)
            similar_wrappers = artist_obj.get_similar(limit=max(1, int(similar_limit)))
        except Exception as e:
            logger.error(f"Failed to fetch similar artists for '{seed}': {e}")
            return []

        # 2) 각 유사 아티스트별 상위 트랙 수집 (ArtistTracks의 순수 함수 재사용)
        results: List[Dict[str, str]] = []
        seen = set()  # (videoId) 중복 제거

        for w in similar_wrappers:
            try:
                sim_name = w.item.get_name()
            except Exception as e:
                logger.error(f"Error reading similar artist name for '{seed}': {e}")
                continue

            try:
                MusicUtils.rate_limit()
                tracks = ArtistTracks.fetch_top_tracks_by_artist(sim_name, limit=k)
            except Exception as e:
                logger.error(f"Failed to get tracks for similar artist '{sim_name}': {e}")
                continue

            for t in tracks:
                try:
                    vid = t.get("videoId", "")
                    if not vid or vid in seen:
                        continue
                    seen.add(vid)
                    results.append(t)  # 이미 통일 스키마
                except Exception as e:
                    logger.error(f"Error processing track for '{sim_name}': {e}")
        return results
