"""
Router for the user endpoints
Endpoints:
- /user/me: Get the user's profile
- /user/top-tracks: Get the user's top tracks
"""

from fastapi import APIRouter, HTTPException, Request

from server.services.spotify_client import get_user_profile, get_user_top_tracks

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me")
async def me(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await get_user_profile(access_token)


@router.get("/top-tracks")
async def top_tracks(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await get_user_top_tracks(access_token)
