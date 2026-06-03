from server.services.personalization import (
    TasteProfile,
    build_taste_profile,
    personalize_tracks,
)
from server.tests.conftest import make_track


def test_build_taste_profile_collects_artists_and_tracks(
    sample_top_artists, sample_top_tracks
):
    profile = build_taste_profile(sample_top_artists, sample_top_tracks)

    assert profile.top_artist_ids == {"artist-1", "artist-2"}
    assert profile.top_artist_names == {"radiohead", "bon iver"}
    assert profile.top_track_ids == {"track-known", "track-2"}


def test_personalize_prefers_familiar_artists(taste_profile):
    tracks = [
        make_track("unknown-1", "Random Hit", "artist-x", "Stranger"),
        make_track("known-1", "In Rainbows", "artist-1", "Radiohead"),
    ]

    result = personalize_tracks(tracks, taste_profile, limit=2)

    assert len(result) == 2
    assert result[0]["id"] == "known-1"


def test_personalize_excludes_top_tracks(taste_profile):
    tracks = [
        make_track("track-known", "Creep", "artist-1", "Radiohead"),
        make_track("new-1", "New Song", "artist-1", "Radiohead"),
    ]

    result = personalize_tracks(tracks, taste_profile, limit=5)

    assert all(t["id"] != "track-known" for t in result)
    assert result[0]["id"] == "new-1"


def test_personalize_dedupes_by_track_id(taste_profile):
    tracks = [
        make_track("dup", "Song A", "artist-1", "Radiohead"),
        make_track("dup", "Song A duplicate", "artist-1", "Radiohead"),
    ]

    result = personalize_tracks(tracks, taste_profile, limit=10)

    assert len(result) == 1
    assert result[0]["id"] == "dup"


def test_personalize_one_track_per_artist(taste_profile):
    tracks = [
        make_track("t1", "Song A", "artist-1", "Radiohead"),
        make_track("t2", "Song B", "artist-1", "Radiohead"),
        make_track("t3", "Song C", "artist-2", "Bon Iver"),
    ]

    result = personalize_tracks(tracks, taste_profile, limit=2)

    assert len(result) == 2
    assert result[0]["artists"][0]["id"] == "artist-1"
    assert result[1]["artists"][0]["id"] == "artist-2"


def test_personalize_empty_input(taste_profile):
    assert personalize_tracks([], taste_profile) == []
