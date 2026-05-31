import json

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from server.services.mood_parser import parse_mood
from server.services.spotify_client import (
    RecommendationsUnavailable,
    get_recommendations,
    get_user_top_tracks,
    search_tracks_for_mood,
)

router = APIRouter(prefix="/search", tags=["search"])


# Create the request model for the mood endpoint
class MoodRequest(BaseModel):
    # The raw text of the vibe
    raw_text: str = Field(..., min_length=1, max_length=500)


# Create the response model for the mood endpoint
class MoodResponse(BaseModel):
    raw_text: str
    parsed_params: dict
    tracks: list[dict] = []
    track_source: str = "recommendations"


# Helper function to seed IDs from top tracks as this is used in mood endpoint
# @param top_tracks_data: The data from the top tracks endpoint
# @return artist_ids: The list of artist IDs
# @return track_ids: The list of track IDs
def _seed_ids_from_top_tracks(top_tracks_data: dict) -> tuple[list[str], list[str]]:
    """Up to 2 track IDs and 2 artist IDs for Spotify recommendation seeds."""
    items = top_tracks_data.get("items") or []
    track_ids: list[str] = []
    artist_ids: list[str] = []
    seen_artists: set[str] = set()

    for item in items:
        track_id = item.get("id")
        if track_id and len(track_ids) < 2:
            track_ids.append(track_id)

        for artist in item.get("artists") or []:
            artist_id = artist.get("id")
            if artist_id and artist_id not in seen_artists and len(artist_ids) < 2:
                seen_artists.add(artist_id)
                artist_ids.append(artist_id)

        if len(track_ids) >= 2 and len(artist_ids) >= 2:
            break

    return artist_ids, track_ids


# Endpoint to search for music based on the mood provided by the user
# @param body: The request body containing the mood text
# @param request: The request object
# @return MoodResponse: The response containing the mood text, parsed parameters, and tracks
@router.post("/mood", response_model=MoodResponse)
async def search_mood(body: MoodRequest, request: Request):
    """Parse a vibe via Gemini, then fetch ~10 personalized tracks from Spotify."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        parsed_params = await parse_mood(body.raw_text)
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
            detail=f"Failed to parse mood: {exc}",
        ) from exc

    # Get the user's top tracks and seed IDs from them
    try:
        top_data = await get_user_top_tracks(access_token, limit=10)
        artist_ids, track_ids = _seed_ids_from_top_tracks(top_data)

        if not artist_ids and not track_ids:
            raise HTTPException(
                status_code=400,
                detail="No top tracks found to seed recommendations. Listen on Spotify and try again.",
            )

        track_source = "recommendations"
        try:
            recommendations = await get_recommendations(
                access_token,
                parsed_params,
                artist_ids,
                track_ids,
            )
            tracks = recommendations.get("tracks") or []
        except RecommendationsUnavailable:
            tracks = await search_tracks_for_mood(
                access_token, parsed_params, body.raw_text
            )
            track_source = "search"

        if not tracks:
            raise HTTPException(
                status_code=404,
                detail="No tracks found for this mood. Try a different description.",
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

    return MoodResponse(
        raw_text=body.raw_text,
        parsed_params=parsed_params,
        tracks=tracks,
        track_source=track_source,
    )


@router.post("/discover")
async def search_discover():
    """Placeholder for Week 3 discovery flow."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
