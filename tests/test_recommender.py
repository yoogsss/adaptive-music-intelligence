import pandas as pd

from src.data_loader import normalize_song_dataset
from src.recommender import (
    add_hr_zones,
    classify_hr_zone,
    dominant_zone,
    find_seed_songs,
    recommend_for_workout_segments,
    recommend_songs,
    segment_workout_session,
)
from src.spotify_matching import match_spotify_tracks_to_audio_features, scoring_ready_tracks


def song_rows():
    return pd.DataFrame(
        [
            {
                "track_name": "Seed",
                "artist": "A",
                "bpm": 126,
                "energy": 0.82,
                "danceability": 0.80,
                "valence": 0.50,
                "acousticness": 0.08,
                "genre": "pop",
            },
            {
                "track_name": "Best Candidate",
                "artist": "B",
                "bpm": 124,
                "energy": 0.80,
                "danceability": 0.82,
                "valence": 0.52,
                "acousticness": 0.07,
                "genre": "dance pop",
            },
            {
                "track_name": "High BPM Wrong Vibe",
                "artist": "C",
                "bpm": 168,
                "energy": 0.95,
                "danceability": 0.42,
                "valence": 0.18,
                "acousticness": 0.75,
                "genre": "metal",
            },
        ]
    )


def test_normalize_song_dataset_accepts_common_public_dataset_columns():
    raw = pd.DataFrame(
        {
            "track_name": ["Song"],
            "artists": ["Artist"],
            "tempo": [120],
            "energy": [0.8],
            "danceability": [0.7],
            "valence": [0.6],
            "acousticness": [0.1],
            "track_genre": ["pop"],
        }
    )

    result = normalize_song_dataset(raw)

    assert result.loc[0, "artist"] == "Artist"
    assert result.loc[0, "bpm"] == 120
    assert result.loc[0, "genre"] == "pop"


def test_classify_hr_zone_uses_percent_of_max_hr():
    assert classify_hr_zone(105, 190) == "Zone 1 - Recovery"
    assert classify_hr_zone(125, 190) == "Zone 2 - Endurance"
    assert classify_hr_zone(145, 190) == "Zone 3 - Tempo"
    assert classify_hr_zone(165, 190) == "Zone 4 - Threshold"
    assert classify_hr_zone(175, 190) == "Zone 5 - Peak"


def test_add_hr_zones_and_dominant_zone():
    workout = pd.DataFrame({"heart_rate": [124, 126, 130, 150]})

    result = add_hr_zones(workout, age=30)

    assert "hr_zone" in result.columns
    assert dominant_zone(result) == "Zone 2 - Endurance"


def test_find_seed_songs_matches_track_artist_input():
    result = find_seed_songs(song_rows(), ["Seed - A"])

    assert len(result) == 1
    assert result.iloc[0]["track_name"] == "Seed"


def test_recommendations_exclude_seed_and_rank_similar_candidate_first():
    result, seed_df, seed_profile = recommend_songs(
        song_rows(),
        seed_inputs=["Seed - A"],
        bpm_min=115,
        bpm_max=132,
        workout_type="treadmill walk",
        mood="club walk",
        preferred_genres=["dance pop"],
        top_n=2,
    )

    assert seed_df.iloc[0]["track_name"] == "Seed"
    assert seed_profile["bpm"] == 126
    assert result.iloc[0]["track_name"] == "Best Candidate"
    assert "Seed" not in result["track_name"].tolist()
    assert result.iloc[0]["recommendation_score"] > result.iloc[1]["recommendation_score"]
    assert {"bpm_fit", "seed_similarity", "workout_fit", "mood_genre_fit", "heart_rate_fit"}.issubset(result.columns)
    assert "why_recommended" in result.columns


def test_no_seed_match_raises_instead_of_random_recommendations():
    try:
        recommend_songs(
            song_rows(),
            seed_inputs=["Missing Song - Nobody"],
            bpm_min=115,
            bpm_max=132,
            workout_type="treadmill walk",
            mood="club walk",
        )
    except ValueError as exc:
        assert "seed song" in str(exc)
    else:
        raise AssertionError("Expected missing seed songs to raise ValueError")


def test_segment_workout_session_groups_contiguous_hr_zones():
    workout = pd.DataFrame(
            {
                "minute": [0, 1, 2, 3, 4],
                "heart_rate": [105, 124, 128, 145, 150],
            }
        )

    segments = segment_workout_session(workout, age=30)

    assert len(segments) == 3
    assert segments.iloc[0]["hr_zone"] == "Zone 1 - Recovery"
    assert segments.iloc[1]["start_minute"] == 1
    assert segments.iloc[1]["end_minute"] == 2


def test_recommend_for_workout_segments_returns_ordered_playlist():
    workout = pd.DataFrame(
        {
            "minute": [0, 1, 2, 3],
            "heart_rate": [124, 128, 150, 152],
        }
    )
    segments = segment_workout_session(workout, age=30)

    playlist, seed_df, seed_profile = recommend_for_workout_segments(
        song_rows(),
        segments_df=segments,
        seed_inputs=["Seed - A"],
        bpm_min=115,
        bpm_max=132,
        workout_type="treadmill steady walk",
        mood="club walk",
        preferred_genres=["dance pop"],
        songs_per_segment=1,
    )

    assert not playlist.empty
    assert playlist["segment_number"].is_monotonic_increasing
    assert "segment_name" in playlist.columns
    assert "heart_rate_fit" in playlist.columns
    assert seed_df.iloc[0]["track_name"] == "Seed"
    assert seed_profile["bpm"] == 126


def test_spotify_metadata_match_marks_unavailable_features():
    spotify_tracks = pd.DataFrame(
        [
            {
                "spotify_track_id": "abc",
                "track_name": "Best Candidate",
                "artist": "B",
                "album": "Album",
                "popularity": 80,
            },
            {
                "spotify_track_id": "missing",
                "track_name": "Not In Dataset",
                "artist": "Nobody",
                "album": "Unknown",
                "popularity": 10,
            },
        ]
    )

    matched = match_spotify_tracks_to_audio_features(spotify_tracks, song_rows())
    ready = scoring_ready_tracks(matched)

    assert matched.loc[matched["spotify_track_id"] == "abc", "audio_features_available"].iloc[0]
    assert not matched.loc[matched["spotify_track_id"] == "missing", "audio_features_available"].iloc[0]
    assert ready["spotify_track_id"].tolist() == ["abc"]
