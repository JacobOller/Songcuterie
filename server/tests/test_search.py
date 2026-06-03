from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.services.spotify_client import RecommendationsUnavailable
from server.tests.conftest import make_track


@pytest.fixture
def client():
    return TestClient(app)


def test_search_mood_requires_auth(client):
    response = client.post("/search/mood", json={"raw_text": "chill evening"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_search_discover_not_implemented(client):
    response = client.post("/search/discover")

    assert response.status_code == 501


@patch("server.routers.search.personalize_tracks")
@patch("server.routers.search.get_recommendations", new_callable=AsyncMock)
@patch("server.routers.search.parse_mood", new_callable=AsyncMock)
@patch("server.routers.search.get_user_top_tracks", new_callable=AsyncMock)
@patch("server.routers.search.get_user_top_artists", new_callable=AsyncMock)
def test_search_mood_returns_tracks_with_cookie(
    mock_top_artists,
    mock_top_tracks,
    mock_parse_mood,
    mock_get_recommendations,
    mock_personalize,
    client,
    sample_top_artists,
    sample_top_tracks,
):
    mock_top_artists.return_value = sample_top_artists
    mock_top_tracks.return_value = sample_top_tracks
    mock_parse_mood.return_value = {
        "valence": 0.4,
        "energy": 0.3,
        "target_genres": ["indie"],
    }
    candidate = make_track("rec-1", "Recommended", "artist-1", "Radiohead")
    mock_get_recommendations.return_value = {"tracks": [candidate]}
    mock_personalize.return_value = [candidate]

    response = client.post(
        "/search/mood",
        json={"raw_text": "late night drive"},
        cookies={"access_token": "test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["raw_text"] == "late night drive"
    assert data["parsed_params"]["valence"] == 0.4
    assert data["track_source"] == "recommendations"
    assert len(data["tracks"]) == 1
    mock_parse_mood.assert_awaited_once_with(
        "late night drive",
        ["Radiohead", "Bon Iver"],
    )


@patch("server.routers.search.personalize_tracks")
@patch("server.routers.search.search_tracks_for_mood", new_callable=AsyncMock)
@patch("server.routers.search.get_recommendations", new_callable=AsyncMock)
@patch("server.routers.search.parse_mood", new_callable=AsyncMock)
@patch("server.routers.search.get_user_top_tracks", new_callable=AsyncMock)
@patch("server.routers.search.get_user_top_artists", new_callable=AsyncMock)
def test_search_mood_uses_search_fallback_when_recommendations_unavailable(
    mock_top_artists,
    mock_top_tracks,
    mock_parse_mood,
    mock_get_recommendations,
    mock_search_tracks,
    mock_personalize,
    client,
    sample_top_artists,
    sample_top_tracks,
):
    mock_top_artists.return_value = sample_top_artists
    mock_top_tracks.return_value = sample_top_tracks
    mock_parse_mood.return_value = {"valence": 0.5, "target_genres": ["rock"]}
    mock_get_recommendations.side_effect = RecommendationsUnavailable()
    search_hit = make_track("search-1", "From Search", "artist-2", "Bon Iver")
    mock_search_tracks.return_value = [search_hit]
    mock_personalize.return_value = [search_hit]

    response = client.post(
        "/search/mood",
        json={"raw_text": "road trip"},
        cookies={"access_token": "test-token"},
    )

    assert response.status_code == 200
    assert response.json()["track_source"] == "search"
    mock_search_tracks.assert_awaited_once()


def test_seed_ids_from_top_tracks(sample_top_tracks):
    from server.routers.search import _seed_ids_from_top_tracks

    artist_ids, track_ids = _seed_ids_from_top_tracks(sample_top_tracks)

    assert track_ids == ["track-known"]
    assert set(artist_ids) == {"artist-1", "artist-2"}
