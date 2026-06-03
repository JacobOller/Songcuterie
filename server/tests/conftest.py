import pytest

from server.services.personalization import TasteProfile


@pytest.fixture
def sample_top_artists():
    return [
        {"id": "artist-1", "name": "Radiohead"},
        {"id": "artist-2", "name": "Bon Iver"},
    ]


@pytest.fixture
def sample_top_tracks():
    return {
        "items": [
            {
                "id": "track-known",
                "name": "Creep",
                "artists": [{"id": "artist-1", "name": "Radiohead"}],
            },
            {
                "id": "track-2",
                "name": "Holocene",
                "artists": [{"id": "artist-2", "name": "Bon Iver"}],
            },
        ]
    }


@pytest.fixture
def taste_profile(sample_top_artists, sample_top_tracks):
    from server.services.personalization import build_taste_profile

    return build_taste_profile(sample_top_artists, sample_top_tracks)


def make_track(track_id: str, name: str, artist_id: str, artist_name: str) -> dict:
    return {
        "id": track_id,
        "name": name,
        "artists": [{"id": artist_id, "name": artist_name}],
    }
