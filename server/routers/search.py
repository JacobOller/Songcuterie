"""
Router for the search endpoints

Endpoints:
- /search/mood: Search for music based on the mood provided by the user
- /search/discover: Discovery flow with vibe, optional similar artists, and newness
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from server.services.discovery_search import search_discover
from server.services.mood_search import search_by_mood

router = APIRouter(prefix="/search", tags=["search"])


class MoodRequest(BaseModel):
    raw_text: str = Field(..., min_length=1, max_length=500)


class MoodResponse(BaseModel):
    raw_text: str
    parsed_params: dict
    tracks: list[dict] = []
    track_source: str = "recommendations"


class DiscoverRequest(BaseModel):
    vibe: str = Field(..., min_length=1, max_length=500)
    similar_to: str | None = Field(None, max_length=200)
    newness: int = Field(3, ge=1, le=5)


class DiscoverTrack(BaseModel):
    id: str
    name: str
    artists: list[dict]
    album: dict | None = None
    similarity: int = Field(..., ge=1, le=10)
    reason: str | None = None


class DiscoverResponse(BaseModel):
    tracks: list[DiscoverTrack]


@router.post("/mood", response_model=MoodResponse)
async def search_mood(body: MoodRequest, request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await search_by_mood(access_token, body.raw_text)
    return MoodResponse(**result)


@router.post("/discover", response_model=DiscoverResponse)
async def discover(body: DiscoverRequest, request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await search_discover(
        access_token,
        body.vibe,
        similar_to=body.similar_to,
        newness=body.newness,
    )
    return DiscoverResponse(**result)
