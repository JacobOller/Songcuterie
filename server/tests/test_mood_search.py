from server.services.mood_search import seed_ids_from_top_tracks


def test_seed_ids_from_top_tracks(sample_top_tracks):
    artist_ids, track_ids = seed_ids_from_top_tracks(sample_top_tracks)

    assert track_ids == ["track-known"]
    assert set(artist_ids) == {"artist-1", "artist-2"}
