from .guardrails import moderation_tool
from .tag_tracks import TagTracks
from .global_tracks import GlobalTracks
from .country_tracks import CountryTracks
from .artist_tracks import ArtistTracks
# from .similar_artists import SimilarArtists
# from .similar_tracks import SimilarTracks

TOOLS = [
    moderation_tool,
    TagTracks.get_tracks_by_tag,
    GlobalTracks.get_global_top_tracks,
    CountryTracks.get_top_tracks_by_country,
    ArtistTracks.get_top_tracks_by_artist,
    # SimilarArtists.get_similar_artists,
    # SimilarTracks.get_similar_tracks,
]

__all__ = ["TOOLS"]
