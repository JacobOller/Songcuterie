import httpx


# Function to get the user's top tracks# @param access_token: The access token for the user
# @param time_range: The time range for the top tracks (short_term is 4 weeks, medium_term is 6 months, long_term is all time)
# @param limit: The number of tracks to return
# @return top_tracks: A list of the user's top tracks
async def get_user_top_tracks(access_token: str, time_range: str = "short_term", limit: int = 20):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.spotify.com/v1/me/top/tracks",
            headers=headers,
            params={"time_range": time_range, "limit": limit}
        )
        return response.json()
