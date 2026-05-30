import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from server.services.mood_parser import parse_mood

# Create the search router
router = APIRouter(prefix="/search", tags=["search"])


# Create the request model for the mood endpoint
class MoodRequest(BaseModel):
    # The raw text of the vibe
    raw_text: str = Field(..., min_length=1, max_length=500)


# Create the response model for the mood endpoint
class MoodResponse(BaseModel):
    raw_text: str
    parsed_params: dict


# Function to search for music by mood
# @param body: The request body containing the raw text of the vibe
# @return MoodResponse: The response containing the raw text of the vibe and the parsed audio feature parameters
@router.post("/mood", response_model=MoodResponse)
async def search_mood(body: MoodRequest):
    """Parse a vibe string into Spotify audio feature targets via Gemini."""
    # Parse the vibe text into audio feature parameters
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

    # Return the response containing the raw text of the vibe and the parsed audio feature parameters
    return MoodResponse(raw_text=body.raw_text, parsed_params=parsed_params)


# Function to search for new music
# @return DiscoverResponse: The response containing the new music
# TODO: Implement this later.
@router.post("/discover")
async def search_discover():
    """Placeholder for Week 3 discovery flow."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
