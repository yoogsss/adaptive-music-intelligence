import pandas as pd

from src.recommender import add_hr_zones, classify_hr_zone, dominant_zone, recommend_songs


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


def test_recommend_songs_ranks_contextual_match_first():
    songs = pd.DataFrame(
        [
            {
                "track_name": "Best Match",
                "artist": "A",
                "bpm": 160,
                "energy": 0.84,
                "danceability": 0.78,
                "valence": 0.52,
            },
            {
                "track_name": "Too Slow",
                "artist": "B",
                "bpm": 105,
                "energy": 0.25,
                "danceability": 0.45,
                "valence": 0.90,
            },
        ]
    )

    result = recommend_songs(
        songs,
        zone="Zone 4 - Threshold",
        mood="Focused",
        intensity="Moderate",
        top_n=2,
    )

    assert result.iloc[0]["track_name"] == "Best Match"
    assert result.iloc[0]["recommendation_score"] > result.iloc[1]["recommendation_score"]
    assert "why_recommended" in result.columns
