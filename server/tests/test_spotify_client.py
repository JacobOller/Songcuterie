import pytest
from fastapi import HTTPException

from server.services.spotify_client import (
    _build_recommendation_query,
    _mood_search_query,
    _pick_genre_seed,
    _spotify_error_message,
)


def test_pick_genre_seed_matches_valid_spotify_genre():
    assert _pick_genre_seed(["indie pop", "made-up-genre"]) == "indie-pop"


def test_pick_genre_seed_returns_none_for_invalid():
    assert _pick_genre_seed(["not-a-real-spotify-genre-xyz"]) is None


def test_build_recommendation_query_uses_artist_seeds_and_audio_targets():
    params = {
        "valence": 0.3,
        "energy": 0.5,
        "target_genres": ["indie"],
    }
    query = _build_recommendation_query(
        params,
        top_artist_ids=["a1", "a2", "a3"],
        top_track_ids=["t1"],
    )

    assert query["limit"] == 10
    assert query["target_valence"] == 0.3
    assert query["target_energy"] == 0.5
    assert query["seed_artists"] == "a1,a2,a3"
    assert query["seed_tracks"] == "t1"
    assert query["seed_genres"] == "indie"


def test_build_recommendation_query_requires_at_least_one_seed():
    with pytest.raises(HTTPException) as exc_info:
        _build_recommendation_query({}, [], [])

    assert exc_info.value.status_code == 400


def test_mood_search_query_uses_genres_when_present():
    parsed = {"target_genres": ["ambient pop", "chill"]}
    assert _mood_search_query(parsed, "late night drive") == "ambient pop chill"


def test_mood_search_query_falls_back_to_raw_text():
    assert _mood_search_query({}, "rainy night") == "rainy night"


def test_spotify_error_message_from_json():
    class FakeResponse:
        status_code = 400

        def json(self):
            return {"error": {"message": "Invalid limit"}}

        text = ""

    assert _spotify_error_message(FakeResponse()) == "Invalid limit"
