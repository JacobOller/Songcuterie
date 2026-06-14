"""
Module for parsing the mood text into audio feature parameters
Functions:
- parse_mood: Parse the mood text into audio feature parameters
- _load_valid_genre_seeds: Load the valid genre seeds from the file
- _load_prompt: Load the prompt from the file
- _generate_response: Generate a response from the model
- _parse_response: Parse the response from the model
- _save_response: Save the response to the file
- _load_response: Load the response from the file
- _delete_response: Delete the response from the file
"""

import json
import os
from pathlib import Path

from google import genai

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "brain" / "prompts" / "mood_to_params.txt"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    return _client


async def parse_mood(vibe_text: str, top_artists: list[str]):
    artist_block = ", ".join(top_artists) if top_artists else "none available"
    prompt = PROMPT_PATH.read_text(encoding="utf-8").replace("{top_artists}", artist_block)
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    response = _get_client().models.generate_content(
        model=model,
        contents=f"{prompt}\n\nUser vibe: {vibe_text}",
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())
