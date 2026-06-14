"""
Discovery search — vibe-based track surfacing with tunable newness.

Reuses mood parsing and Spotify fetching, then ranks candidates by blending
familiarity (low newness) vs novelty (high newness) and maps scores to 1–10.
"""

import json

import httpx
from fastapi import HTTPException

from server.services.mood_parser import parse_mood
from server.services.mood_search import seed_ids_from_top_tracks
from server.services.personalization import (
    TasteProfile,
    _dedupe_tracks,
    _score_track,
    _track_artist_ids,
    build_taste_profile,
)
from server.services.spotify_client import (
    RecommendationsUnavailable,
    get_recommendations,
    get_user_top_artists,
    get_user_top_tracks,
    search_tracks,
    search_tracks_for_mood,
)

_DEFAULT_LIMIT = 20


def _novelty_score(track: dict, profile: TasteProfile) -> int:
    if track.get("id") in profile.top_track_ids:
        return -1000

    penalty = 0
    for aid in _track_artist_ids(track):
        if aid in profile.top_artist_ids:
            penalty += 40

    for artist in track.get("artists") or []:
        name = (artist.get("name") or "").lower()
        if name in profile.top_artist_names:
            penalty += 25

    return max(0, 100 - penalty)


def _combined_score(track: dict, profile: TasteProfile, newness: int) -> int:
    familiarity = max(0, _score_track(track, profile))
    novelty = _novelty_score(track, profile)
    if novelty < 0:
        return -1000

    weight = (newness - 1) / 4.0
    return round((1 - weight) * familiarity + weight * novelty)


def _rough_reason(track: dict, profile: TasteProfile, newness: int) -> str:
    known_names = [
        artist["name"]
        for artist in track.get("artists") or []
        if artist.get("id") in profile.top_artist_ids and artist.get("name")
    ]

    if newness >= 4 and not known_names:
        return "A fresh pick outside your usual rotation"
    if known_names:
        label = ", ".join(known_names[:2])
        return f"Connected to artists you already love ({label})"
    return "Matches the vibe you described"


def _attach_similarity(
    scored: list[tuple[int, dict]],
    profile: TasteProfile,
    newness: int,
) -> list[dict]:
    if not scored:
        return []

    scores = [score for score, _ in scored]
    min_score = min(scores)
    max_score = max(scores)

    results: list[dict] = []
    for score, track in scored:
        if max_score == min_score:
            similarity = 7
        else:
            normalized = (score - min_score) / (max_score - min_score)
            similarity = max(1, min(10, round(1 + normalized * 9)))

        results.append(
            {
                "id": track["id"],
                "name": track["name"],
                "artists": track.get("artists") or [],
                "album": track.get("album"),
                "similarity": similarity,
                "reason": _rough_reason(track, profile, newness),
            }
        )

    return results


async def _fetch_similar_to_candidates(
    access_token: str, similar_to: str
) -> list[dict]:
    names = [name.strip() for name in similar_to.split(",") if name.strip()]
    pool: list[dict] = []
    for name in names[:3]:
        pool.extend(await search_tracks(access_token, f'artist:"{name}"', 10))
    return pool


async def search_discover(
    access_token: str,
    vibe: str,
    *,
    similar_to: str | None = None,
    newness: int = 3,
    limit: int = _DEFAULT_LIMIT,
) -> dict:
    """Parse a vibe, fetch candidates, rank by newness, return scored tracks."""
    try:
        top_artists = await get_user_top_artists(access_token, limit=10)
        top_data = await get_user_top_tracks(access_token, limit=20)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load listening profile: {exc}",
        ) from exc

    artist_names = [artist["name"] for artist in top_artists]
    taste = build_taste_profile(top_artists, top_data)
    top_artist_ids = [artist["id"] for artist in top_artists[:3]]
    _, track_ids = seed_ids_from_top_tracks(top_data)

    if not top_artist_ids and not track_ids:
        raise HTTPException(
            status_code=400,
            detail="No top tracks or artists found. Listen on Spotify and try again.",
        )

    try:
        parsed_params = await parse_mood(vibe, artist_names)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM returned invalid JSON: {exc}",
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Mood prompt template not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse vibe: {exc}",
        ) from exc

    try:
        try:
            recommendations = await get_recommendations(
                access_token,
                parsed_params,
                top_artist_ids,
                track_ids,
            )
            candidates = recommendations.get("tracks") or []
        except RecommendationsUnavailable:
            candidates = await search_tracks_for_mood(
                access_token,
                parsed_params,
                vibe,
                top_artists,
            )

        if similar_to:
            candidates.extend(
                await _fetch_similar_to_candidates(access_token, similar_to)
            )

        unique = _dedupe_tracks(candidates)
        scored = [
            (score, track)
            for track in unique
            if (score := _combined_score(track, taste, newness)) >= 0
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        tracks = _attach_similarity(scored[:limit], taste, newness)

        if not tracks:
            raise HTTPException(
                status_code=404,
                detail="No tracks matched your search. Try a different vibe or lower newness.",
            )
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Spotify API error: {exc.response.text}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to get tracks: {exc}",
        ) from exc

    return {"tracks": tracks}
