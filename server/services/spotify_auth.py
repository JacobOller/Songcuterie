# File that handles the authentication of the user

import os
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

# Scopes for current + planned PLAN.md features (re-login required after changes).
SPOTIFY_SCOPES = " ".join(
    [
        "user-read-private",
        "user-read-email",
        "user-top-read",
        "user-read-recently-played",
        "playlist-modify-public",
        "playlist-modify-private",
    ]
)

# Function to build the Spotify authorization URL
# @return auth_url: The Spotify authorization URL
# @return state: The OAuth state
async def build_spotify_auth_url():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    state = secrets.token_hex(16)
    # Build the query string for the authorization URL
    # Includes everything we need for the callback
    query = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": SPOTIFY_SCOPES,
            "state": state,
        }
    )
    auth_url = f"https://accounts.spotify.com/authorize?{query}"
    return auth_url, state

# Handle the Spotify callback
# Builds token data, makes request to token URL, and returns the token data
# @param code: The authorization code
# @return token_data: The token data (access_token, refresh_token, expires_in, token_type, scope)
async def handle_spotify_callback(code: str):
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    # Check for credentials
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=500, detail="Missing Spotify credentials")

    # Build the token URL and data
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }

    # Make the request to the token URL
    # Use httpx to make the request asynchronously
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=data,
            auth=(client_id, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    # Check if the request was successful
    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange authorization code for access token: {response.text}",
        )

    # Parse the response
    token_data = response.json()

    # Return the token data
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data["expires_in"],
        "token_type": token_data["token_type"],
        "scope": token_data.get("scope"),
    }


async def handle_spotify_refresh(refresh_token: str):
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Missing Spotify credentials")
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    # Make the request to the token URL
    # Use httpx to make the request asynchronously
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=data,
            auth=(client_id, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to refresh access token: {response.text}",
        )

    # Parse the response
    token_data = response.json()

    # Return the token data as a dictionary
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data["expires_in"],
        "token_type": token_data["token_type"],
        "scope": token_data.get("scope"),
    }
