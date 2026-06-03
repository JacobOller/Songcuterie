import json
import os
from pathlib import Path

from google import genai

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "brain" / "prompts" / "mood_to_params.txt"

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


async def parse_mood(vibe_text: str, top_artists: list[str]):
    artist_block = ", ".join(top_artists) if top_artists else "none available"
    prompt = PROMPT_PATH.read_text(encoding="utf-8").replace("{top_artists}", artist_block)
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    response = client.models.generate_content(
        model=model,
        contents=f"{prompt}\n\nUser vibe: {vibe_text}",
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())
