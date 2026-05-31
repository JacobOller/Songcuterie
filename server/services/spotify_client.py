from pathlib import Path

import httpx
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENRE_SEEDS_PATH = PROJECT_ROOT / "brain" / "data" / "spotify_genre_seeds.txt"

# Audio target keys for the recommendations API
_AUDIO_TARGET_KEYS = (
    ("valence", "target_valence"),
    ("energy", "target_energy"),
    ("acousticness", "target_acousticness"),
    ("danceability", "target_danceability"),
    ("instrumentalness", "target_instrumentalness"),
    ("tempo", "target_tempo"),
)


"""
Helper function to load the valid genre seeds from the file 
@return valid_genre_seeds: A set of valid genre seeds
@return lines: The lines of the file
@return frozenset(line.strip() for line in lines if line.strip() and not line.startswith("#")): A set of valid genre seeds
"""
def _load_valid_genre_seeds() -> frozenset[str]:
    lines = GENRE_SEEDS_PATH.read_text(encoding="utf-8").splitlines()
    return frozenset(
        line.strip()
        for line in lines
        if line.strip() and not line.startswith("#")
    )

_VALID_GENRE_SEEDS = _load_valid_genre_seeds()

class RecommendationsUnavailable(Exception):
    """Spotify blocked /recommendations for this app (common for new dev apps since Nov 2024)."""


"""
Helper function to build the authentication headers
@param access_token: The access token
@return headers: The authentication headers
"""
def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


"""
Helper function to make a GET request to the Spotify API
@param access_token: The access token
@param url: The URL to make the request to
@param params: The parameters for the request
@return response: The response from the Spotify API
@return client.get(url, headers=_auth_headers(access_token), params=params): The response from the Spotify API
"""
async def _spotify_get(
    access_token: str, url: str, params: dict | None = None
) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.get(
            url, headers=_auth_headers(access_token), params=params
        )


"""
Helper function to get the error message from the Spotify API response
@param response: The response from the Spotify API
@return err.get("message") or response.text or f"HTTP {response.status_code}": The error message
@return response.text or f"HTTP {response.status_code}": The error message
"""
def _spotify_error_message(response: httpx.Response) -> str:
    try:
        err = response.json().get("error", {})
        return err.get("message") or response.text or f"HTTP {response.status_code}"
    except Exception:
        return response.text or f"HTTP {response.status_code}"


"""
Helper function to raise an HTTP exception with the error message from the Spotify API response
@param response: The response from the Spotify API
@return HTTPException(status_code=400, detail=_spotify_error_message(response)): The HTTP exception
"""
def _raise_spotify_error(response: httpx.Response) -> None:
    raise HTTPException(status_code=400, detail=_spotify_error_message(response))


"""
Helper function to pick a genre seed from the list of genres
@param genres: The list of genres
@return candidate: The genre seed
@return None: If no genre seed is found
"""
def _pick_genre_seed(genres: list) -> str | None:
    for raw in genres:
        if not isinstance(raw, str):
            continue
        normalized = raw.lower().strip()
        for candidate in (
            normalized.replace(" ", "-"),
            normalized.split()[0],
            normalized.split("-")[0],
        ):
            if candidate in _VALID_GENRE_SEEDS:
                return candidate
    return None


"""
Helper function to build the recommendation query
@param params: The parameters for the recommendations
@param top_artist_ids: The IDs of the top artists
@param top_track_ids: The IDs of the top tracks
@return query: The query for the recommendations
"""
def _build_recommendation_query(
    params: dict, top_artist_ids: list[str], top_track_ids: list[str]) -> dict:
    query: dict = {"limit": 10}

    for key, spotify_key in _AUDIO_TARGET_KEYS:
        value = params.get(key)
        if value is not None:
            query[spotify_key] = value

    genre_seed = _pick_genre_seed(params.get("target_genres") or [])
    if genre_seed:
        query["seed_genres"] = genre_seed
    if top_artist_ids:
        query["seed_artists"] = ",".join(top_artist_ids[:2])
    if top_track_ids:
        query["seed_tracks"] = ",".join(top_track_ids[:2])

    if not any(k in query for k in ("seed_genres", "seed_artists", "seed_tracks")):
        raise HTTPException(
            status_code=400,
            detail="Need at least one seed for recommendations.",
        )
    return query


"""
Helper function to build the mood search query
@param parsed_params: The parsed mood parameters from the LLM
@param raw_text: The original mood text from the user
@return query_parts: The query parts for the mood search
@return " ".join(query_parts) if query_parts else raw_text.strip(): The mood search query
"""
def _mood_search_query(parsed_params: dict, raw_text: str) -> str:
    genres = parsed_params.get("target_genres") or []
    query_parts = [
        genre.strip()
        for genre in genres[:2]
        if isinstance(genre, str) and genre.strip()
    ]
    return " ".join(query_parts) if query_parts else raw_text.strip()


# Get the user's profile
# @param access_token: The access token
# @return user_profile: The user's profile
async def get_user_profile(access_token: str):
    response = await _spotify_get(access_token, "https://api.spotify.com/v1/me")
    return response.json()


# Get the user's top tracks
# @param access_token: The access token
# @param time_range: The time range of the top tracks (short_term, medium_term, long_term)
# @param limit: The number of top tracks to return
# @return top_tracks: The user's top tracks
async def get_user_top_tracks(
    access_token: str, time_range: str = "short_term", limit: int = 20
):
    response = await _spotify_get(
        access_token,
        "https://api.spotify.com/v1/me/top/tracks",
        params={"time_range": time_range, "limit": limit},
    )
    return response.json()


# Get the recommendations for the user
# @param access_token: The access token
# @param params: The parameters for the recommendations
# @param top_artist_ids: The IDs of the top artists
# @param top_track_ids: The IDs of the top tracks
# @return recommendations: The recommendations
async def get_recommendations(
    access_token: str,
    params: dict,
    top_artist_ids: list[str],
    top_track_ids: list[str],
):
    query = _build_recommendation_query(params, top_artist_ids, top_track_ids)
    response = await _spotify_get(
        access_token,
        "https://api.spotify.com/v1/recommendations",
        params=query,
    )

    if response.status_code == 404:
        raise RecommendationsUnavailable(
            "Spotify Recommendations API is not available for this app. "
            "New developer apps lost access in Nov 2024; using search fallback."
        )

    if response.status_code != 200:
        _raise_spotify_error(response)

    return response.json()


# Search for tracks matching a mood (fallback when recommendations are unavailable)
# @param access_token: The access token
# @param parsed_params: The parsed mood parameters from the LLM
# @param raw_text: The original mood text from the user
# @param limit: The number of tracks to return
# @return tracks: A list of track objects from the Search API
async def search_tracks_for_mood(
    access_token: str,
    parsed_params: dict,
    raw_text: str,
    limit: int = 10,
) -> list[dict]:
    response = await _spotify_get(
        access_token,
        "https://api.spotify.com/v1/search",
        params={"q": _mood_search_query(parsed_params, raw_text), "type": "track", "limit": limit},
    )

    if response.status_code != 200:
        _raise_spotify_error(response)

    data = response.json()
    return data.get("tracks", {}).get("items", [])
