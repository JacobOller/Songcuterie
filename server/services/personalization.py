"""Re-rank and filter Spotify tracks using the user's listening profile."""

from dataclasses import dataclass, field


@dataclass
class TasteProfile:
    top_artist_ids: set[str] = field(default_factory=set)
    top_artist_names: set[str] = field(default_factory=set)
    top_track_ids: set[str] = field(default_factory=set)


"""
Function to build a taste profile from Spotify top artists + top tracks payloads.
@param top_artists: The list of top artists
@param top_tracks_data: The data from the top tracks endpoint
@return TasteProfile: The taste profile
"""
def build_taste_profile(
    top_artists: list[dict],
    top_tracks_data: dict,
) -> TasteProfile:
    """Build a taste profile from Spotify top artists + top tracks payloads."""
    artist_ids: set[str] = set()
    artist_names: set[str] = set()
    for artist in top_artists:
        if aid := artist.get("id"):
            artist_ids.add(aid)
        if name := artist.get("name"):
            artist_names.add(name.lower())

    track_ids: set[str] = set()
    for item in top_tracks_data.get("items") or []:
        if tid := item.get("id"):
            track_ids.add(tid)
        for artist in item.get("artists") or []:
            if aid := artist.get("id"):
                artist_ids.add(aid)
            if name := artist.get("name"):
                artist_names.add(name.lower())

    return TasteProfile(
        top_artist_ids=artist_ids,
        top_artist_names=artist_names,
        top_track_ids=track_ids,
    )


"""
Helper function to get the artist IDs from a track
@param track: The track
@return [a["id"] for a in track.get("artists") or [] if a.get("id")]: The list of artist IDs
"""
def _track_artist_ids(track: dict) -> list[str]:
    return [a["id"] for a in track.get("artists") or [] if a.get("id")]


"""
Helper function to get the primary artist ID from a track
@param track: The track
@return artists[0].get("id") if artists else None: The primary artist ID
"""
def _primary_artist_id(track: dict) -> str | None:
    artists = track.get("artists") or []
    return artists[0].get("id") if artists else None


"""
Helper function to score a track
@param track: The track
@param profile: The taste profile
@return score: The score of the track
"""
def _score_track(track: dict, profile: TasteProfile) -> int:
    if not track.get("id"):
        return -1000

    if track["id"] in profile.top_track_ids:
        return -100

    score = 0
    for aid in _track_artist_ids(track):
        if aid in profile.top_artist_ids:
            score += 20

    for artist in track.get("artists") or []:
        name = (artist.get("name") or "").lower()
        if name in profile.top_artist_names:
            score += 10

    return score


"""
Helper function to deduplicate tracks
@param tracks: The list of tracks
@return unique: The list of unique tracks
"""
def _dedupe_tracks(tracks: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for track in tracks:
        tid = track.get("id")
        if not tid or tid in seen:
            continue
        seen.add(tid)
        unique.append(track)
    return unique


"""
Function to personalize tracks
Does this by:
- Sorting the tracks by taste score
- Skipping songs already in top tracks
- Preferring familiar artists
- Falling back to lower-scored picks if strict rules return too few tracks
@param tracks: The list of tracks
@param profile: The taste profile
@param limit: The number of tracks to return
@param one_per_artist: Whether to enforce one track per artist
@param min_taste_score: The minimum taste score
@return picked: The list of personalized tracks
"""
def personalize_tracks(
    tracks: list[dict],
    profile: TasteProfile,
    limit: int = 10,
    *,
    one_per_artist: bool = True,
    min_taste_score: int = 0,
) -> list[dict]:
    """
    Sort by taste score, skip songs already in top tracks, prefer familiar artists.
    Falls back to lower-scored picks if strict rules return too few tracks.
    """
    unique = _dedupe_tracks(tracks)
    scored = sorted(
        ((_score_track(t, profile), t) for t in unique),
        key=lambda pair: pair[0],
        reverse=True,
    )

    def pick(
        enforce_one_per_artist: bool,
        require_min_score: bool,
    ) -> list[dict]:
        result: list[dict] = []
        used_artists: set[str] = set()
        for score, track in scored:
            if require_min_score and score < min_taste_score:
                continue
            if score < 0:
                continue
            primary = _primary_artist_id(track)
            if enforce_one_per_artist and primary and primary in used_artists:
                continue
            if primary:
                used_artists.add(primary)
            result.append(track)
            if len(result) >= limit:
                break
        return result

    picked = pick(enforce_one_per_artist=True, require_min_score=True)
    if len(picked) >= limit // 2:
        return picked

    picked = pick(enforce_one_per_artist=True, require_min_score=False)
    if len(picked) >= limit // 2:
        return picked

    return pick(enforce_one_per_artist=False, require_min_score=False)[:limit]
