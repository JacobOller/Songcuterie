import os

from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi import Response, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from server.routers.auth import build_spotify_auth_url, handle_spotify_callback, get_user_profile, handle_spotify_refresh
from server.routers import search
from server.services.spotify_client import get_user_top_tracks

# Load environment variables
load_dotenv()

app = FastAPI()

app.include_router(search.router)

# CORS middleware, used to allow the frontend to make requests to the backend
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Login endpoint
# This endpoint builds the Spotify authorization URL and sets the OAuth state cookie
# The OAuth state is used to prevent CSRF attacks and is used in callback endpoint
# @param response: The response object
# @return RedirectResponse: A redirect response to the Spotify authorization URL
@app.get("/auth/login")
async def login(response: Response): 
    auth_url, state = build_spotify_auth_url()
    # Redirect the user to the Spotify authorization URL
    redirect = RedirectResponse(url=auth_url, status_code=302)
    # Set the OAuth state cookie
    redirect.set_cookie(
        key="oauth_state",
        value=state,
        max_age=600,
        secure=False, #TODO: Change to True in production
        httponly=True,
        samesite="lax",
    )
    # Return the redirect response which sends the user to the Spotify authorization page
    return redirect


# Callback endpoint
# This endpoint handles the Spotify authorization callback
# It validates the OAuth state and exchanges the authorization code for an access token and refresh token
# @param request: The request object
# @param code: The authorization code
# @param state: The OAuth state
# @return token_data: The token data (access_token, refresh_token, expires_in, token_type, scope)
@app.get("/auth/callback")
async def callback(request: Request, code: str, state: str):
    # Validate the OAuth state by comparing the saved state to the state in the request
    saved_state = request.cookies.get("oauth_state")
    if not saved_state or state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid state")
    # Exchange the authorization code for an access token and refresh token
    token_data = await handle_spotify_callback(code)
    frontend_url = os.getenv("FRONTEND_PROFILE_URL", "http://127.0.0.1:3000/profile")
    redirect = RedirectResponse(url=frontend_url, status_code=302)
    # Set the access token
    redirect.set_cookie(
        key="access_token",
        value=token_data["access_token"],
        secure=False, #TODO: Change to True in production
        httponly=True,
        samesite="lax",
    )
    # Set the refresh token
    redirect.set_cookie(
        key="refresh_token",
        value=token_data["refresh_token"],
        max_age=30 * 24 * 3600,
        secure=False, #TODO: Change to True in production
        httponly=True,
        samesite="lax",
    )
    # Delete the OAuth state cookie
    redirect.delete_cookie("oauth_state")
    return redirect


# Me endpoint
# This endpoint returns the user's profile
# @param request: The request object
# @return user_profile: The user's profile
@app.get("/auth/me")
async def me(request: Request):
    # Get the access token from the request cookies
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_profile = await get_user_profile(access_token)
    return user_profile


# Refresh endpoint
# This endpoint refreshes the access token
# @param request: The request object
# @param response: The response object
# @return access_token: The new access token
# @return new_refresh_token: The new refresh token
# @return message: A message indicating that the token was refreshed
@app.get("/auth/refresh")
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    token_data = await handle_spotify_refresh(refresh_token)
    
    response.set_cookie(
        key="access_token",
        value=token_data["access_token"],
        secure=False,  # TODO: Change to True in production
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=token_data["refresh_token"],
        max_age=30 * 24 * 3600,
        secure=False,  # TODO: Change to True in production
        httponly=True,
        samesite="lax",
    )
    return {"message": "Token refreshed"}


# Top tracks endpoint
# This endpoint returns the user's top tracks
# @param request: The request object
# @return top_tracks: A list of the user's top tracks
@app.get("/user/top-tracks")
async def top_tracks(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    top_tracks = await get_user_top_tracks(access_token)
    return top_tracks