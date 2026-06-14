from server.services.discovery_search import (
    _attach_similarity,
    _combined_score,
    _novelty_score,
)
from server.services.personalization import build_taste_profile


def test_novelty_score_penalizes_known_artists(taste_profile, sample_top_tracks):
    known = sample_top_tracks["items"][0]
    unknown = {
        "id": "brand-new",
        "name": "New Song",
        "artists": [{"id": "artist-99", "name": "New Artist"}],
    }

    assert _novelty_score(known, taste_profile) < 0
    assert _novelty_score(unknown, taste_profile) > _novelty_score(
        {
            "id": "semi-known",
            "name": "Semi",
            "artists": [{"id": "artist-1", "name": "Radiohead"}],
        },
        taste_profile,
    )


def test_combined_score_shifts_with_newness(taste_profile):
    familiar = {
        "id": "familiar-track",
        "name": "Familiar",
        "artists": [{"id": "artist-1", "name": "Radiohead"}],
    }
    fresh = {
        "id": "fresh-track",
        "name": "Fresh",
        "artists": [{"id": "artist-99", "name": "New Artist"}],
    }

    low_newness_familiar = _combined_score(familiar, taste_profile, newness=1)
    high_newness_familiar = _combined_score(familiar, taste_profile, newness=5)
    low_newness_fresh = _combined_score(fresh, taste_profile, newness=1)
    high_newness_fresh = _combined_score(fresh, taste_profile, newness=5)

    assert low_newness_familiar > low_newness_fresh
    assert high_newness_fresh > high_newness_familiar


def test_attach_similarity_maps_to_one_through_ten(taste_profile):
    tracks = [
        (10, {"id": "a", "name": "A", "artists": []}),
        (50, {"id": "b", "name": "B", "artists": []}),
        (90, {"id": "c", "name": "C", "artists": []}),
    ]

    results = _attach_similarity(tracks, taste_profile, newness=3)

    assert [track["similarity"] for track in results] == [1, 6, 10]
    assert all(1 <= track["similarity"] <= 10 for track in results)


def test_build_taste_profile_from_fixtures(sample_top_artists, sample_top_tracks):
    profile = build_taste_profile(sample_top_artists, sample_top_tracks)

    assert "artist-1" in profile.top_artist_ids
    assert "track-known" in profile.top_track_ids
