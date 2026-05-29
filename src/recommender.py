from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


ZONE_LABELS = [
    "Zone 1 - Recovery",
    "Zone 2 - Endurance",
    "Zone 3 - Tempo",
    "Zone 4 - Threshold",
    "Zone 5 - Peak",
]

WORKOUT_TARGETS = {
    "treadmill walk": {"bpm": 118, "energy": 0.62, "danceability": 0.72},
    "treadmill steady walk": {"bpm": 116, "energy": 0.58, "danceability": 0.72},
    "treadmill incline walk": {"bpm": 128, "energy": 0.72, "danceability": 0.72},
    "treadmill run": {"bpm": 152, "energy": 0.86, "danceability": 0.72},
    "stairmaster": {"bpm": 130, "energy": 0.78, "danceability": 0.70},
    "cycling intervals": {"bpm": 142, "energy": 0.84, "danceability": 0.68},
    "cycling": {"bpm": 138, "energy": 0.80, "danceability": 0.68},
    "weight lifting": {"bpm": 112, "energy": 0.74, "danceability": 0.60},
    "strength training": {"bpm": 112, "energy": 0.72, "danceability": 0.60},
    "boxing": {"bpm": 148, "energy": 0.90, "danceability": 0.66},
    "pilates": {"bpm": 96, "energy": 0.42, "danceability": 0.55},
}

MOOD_TARGETS = {
    "sultry pop": {"energy": 0.62, "danceability": 0.76, "valence": 0.45, "acousticness": 0.18},
    "club walk": {"energy": 0.78, "danceability": 0.82, "valence": 0.60, "acousticness": 0.08},
    "dance-pop strut": {"energy": 0.76, "danceability": 0.84, "valence": 0.74, "acousticness": 0.10},
    "dark pop": {"energy": 0.70, "danceability": 0.72, "valence": 0.34, "acousticness": 0.12},
    "aggressive": {"energy": 0.90, "danceability": 0.62, "valence": 0.38, "acousticness": 0.06},
    "focused": {"energy": 0.58, "danceability": 0.60, "valence": 0.50, "acousticness": 0.24},
    "chill": {"energy": 0.36, "danceability": 0.52, "valence": 0.58, "acousticness": 0.48},
}

CORE_FEATURES = ["bpm", "energy", "danceability", "valence", "acousticness"]


def available_workout_types() -> list[str]:
    return [
        "treadmill steady walk",
        "treadmill incline walk",
        "stairmaster",
        "cycling intervals",
        "boxing",
        "strength training",
        "pilates",
    ]


def available_moods() -> list[str]:
    return list(MOOD_TARGETS)


def classify_hr_zone(heart_rate: float, max_hr: float) -> str:
    pct = heart_rate / max_hr
    if pct < 0.60:
        return ZONE_LABELS[0]
    if pct < 0.70:
        return ZONE_LABELS[1]
    if pct < 0.80:
        return ZONE_LABELS[2]
    if pct < 0.90:
        return ZONE_LABELS[3]
    return ZONE_LABELS[4]


def add_hr_zones(workout_df: pd.DataFrame, age: int) -> pd.DataFrame:
    required = {"heart_rate"}
    missing = required - set(workout_df.columns)
    if missing:
        raise ValueError(f"Workout data is missing columns: {', '.join(sorted(missing))}")

    max_hr = 220 - age
    df = workout_df.copy()
    df["heart_rate"] = pd.to_numeric(df["heart_rate"], errors="coerce")
    df = df.dropna(subset=["heart_rate"])
    df["hr_zone"] = df["heart_rate"].apply(lambda hr: classify_hr_zone(float(hr), max_hr))
    df["hr_percent_max"] = df["heart_rate"] / max_hr
    return df


def dominant_zone(workout_df: pd.DataFrame) -> str:
    if "hr_zone" not in workout_df.columns:
        raise ValueError("Workout data must include an hr_zone column.")
    return workout_df["hr_zone"].mode().iloc[0]


def heart_rate_context(workout_df: pd.DataFrame | None) -> dict[str, float] | None:
    if workout_df is None or workout_df.empty or "hr_percent_max" not in workout_df.columns:
        return None

    avg_pct = float(workout_df["hr_percent_max"].mean())
    if avg_pct < 0.65:
        return {"bpm": 105, "energy": 0.45, "intensity": 0.35}
    if avg_pct < 0.75:
        return {"bpm": 122, "energy": 0.62, "intensity": 0.55}
    if avg_pct < 0.85:
        return {"bpm": 140, "energy": 0.78, "intensity": 0.75}
    return {"bpm": 155, "energy": 0.90, "intensity": 0.90}


def segment_workout_session(workout_df: pd.DataFrame, age: int) -> pd.DataFrame:
    zoned = add_hr_zones(workout_df, age)
    if "minute" not in zoned.columns:
        zoned = zoned.reset_index().rename(columns={"index": "minute"})

    zoned["segment_id"] = (zoned["hr_zone"] != zoned["hr_zone"].shift()).cumsum()
    segments = (
        zoned.groupby("segment_id")
        .agg(
            start_minute=("minute", "min"),
            end_minute=("minute", "max"),
            avg_heart_rate=("heart_rate", "mean"),
            avg_hr_percent_max=("hr_percent_max", "mean"),
            hr_zone=("hr_zone", "first"),
        )
        .reset_index(drop=True)
    )
    segments["segment_name"] = segments.apply(
        lambda row: f"{int(row['start_minute'])}-{int(row['end_minute'])} min: {row['hr_zone']}",
        axis=1,
    )
    return segments


def segment_target(segment: pd.Series) -> dict[str, float]:
    pct = float(segment["avg_hr_percent_max"])
    if pct < 0.65:
        return {"bpm": 105, "energy": 0.45, "intensity": 0.35}
    if pct < 0.75:
        return {"bpm": 122, "energy": 0.62, "intensity": 0.55}
    if pct < 0.85:
        return {"bpm": 140, "energy": 0.78, "intensity": 0.75}
    return {"bpm": 155, "energy": 0.90, "intensity": 0.90}


def coerce_numeric_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    clean = df.copy()
    for column in columns:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    return clean.dropna(subset=list(columns))


def song_options(songs_df: pd.DataFrame) -> list[str]:
    required = {"track_name", "artist"}
    missing = required - set(songs_df.columns)
    if missing:
        raise ValueError(f"Song data is missing columns: {', '.join(sorted(missing))}")
    return [_song_key(row) for _, row in songs_df.iterrows()]


def find_seed_songs(songs_df: pd.DataFrame, seed_inputs: Iterable[str]) -> pd.DataFrame:
    matches: list[int] = []
    lookup = {_song_key(row).lower(): index for index, row in songs_df.iterrows()}

    for seed in seed_inputs:
        normalized = seed.strip().lower()
        if not normalized:
            continue

        normalized = normalized.replace(" by ", " - ")
        if normalized in lookup:
            matches.append(lookup[normalized])
            continue

        for index, row in songs_df.iterrows():
            track = str(row["track_name"]).lower()
            artist = str(row["artist"]).lower()
            if normalized == track or (track in normalized and artist in normalized):
                matches.append(index)
                break

    return songs_df.loc[sorted(set(matches))].copy()


def seed_feature_profile(seed_df: pd.DataFrame) -> dict[str, float]:
    if seed_df.empty:
        raise ValueError("At least one seed song must match the loaded dataset.")
    return {feature: float(seed_df[feature].mean()) for feature in CORE_FEATURES}


def recommend_songs(
    songs_df: pd.DataFrame,
    seed_inputs: Iterable[str],
    bpm_min: int,
    bpm_max: int,
    workout_type: str,
    mood: str,
    preferred_genres: Iterable[str] | None = None,
    workout_df: pd.DataFrame | None = None,
    min_score: float = 0.0,
    top_n: int = 20,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    required = {"track_name", "artist", "bpm", "energy", "danceability", "valence", "acousticness", "genre"}
    missing = required - set(songs_df.columns)
    if missing:
        raise ValueError(f"Song data is missing columns: {', '.join(sorted(missing))}")
    if bpm_min > bpm_max:
        raise ValueError("Minimum BPM cannot be greater than maximum BPM.")

    seed_df = find_seed_songs(songs_df, seed_inputs)
    seed_profile = seed_feature_profile(seed_df)
    workout_target = WORKOUT_TARGETS.get(workout_type, WORKOUT_TARGETS["treadmill walk"])
    mood_target = MOOD_TARGETS.get(mood, MOOD_TARGETS["club walk"])
    hr_target = heart_rate_context(workout_df)
    genre_set = {genre.strip().lower() for genre in preferred_genres or [] if genre.strip()}

    scored = songs_df.copy()
    scored["bpm_fit"] = bpm_range_fit(scored["bpm"], bpm_min, bpm_max)
    scored["seed_similarity"] = seed_similarity(scored, seed_profile)
    scored["workout_fit"] = workout_fit(scored, workout_target)
    scored["mood_genre_fit"] = mood_genre_fit(scored, mood_target, mood, genre_set)
    scored["heart_rate_fit"] = heart_rate_fit(scored, hr_target)

    if hr_target is None:
        scored["recommendation_score"] = (
            scored["seed_similarity"] * 0.38
            + scored["bpm_fit"] * 0.27
            + scored["mood_genre_fit"] * 0.20
            + scored["workout_fit"] * 0.15
        )
    else:
        scored["recommendation_score"] = (
            scored["seed_similarity"] * 0.35
            + scored["bpm_fit"] * 0.25
            + scored["mood_genre_fit"] * 0.18
            + scored["workout_fit"] * 0.14
            + scored["heart_rate_fit"] * 0.08
        )

    scored["recommendation_score"] = scored["recommendation_score"].round(3)
    seed_keys = {_song_key(row).lower() for _, row in seed_df.iterrows()}
    scored["_song_key"] = scored.apply(_song_key, axis=1).str.lower()
    scored = scored[~scored["_song_key"].isin(seed_keys)]
    scored = scored[scored["recommendation_score"] >= min_score]
    scored["why_recommended"] = scored.apply(
        lambda row: explain_recommendation(row, bpm_min, bpm_max, workout_type, mood, genre_set, hr_target),
        axis=1,
    )

    breakdown_cols = ["bpm_fit", "seed_similarity", "workout_fit", "mood_genre_fit", "heart_rate_fit"]
    scored[breakdown_cols] = scored[breakdown_cols].round(3)
    return (
        scored.sort_values("recommendation_score", ascending=False).head(top_n).drop(columns=["_song_key"]),
        seed_df,
        seed_profile,
    )


def recommend_for_workout_segments(
    songs_df: pd.DataFrame,
    segments_df: pd.DataFrame,
    seed_inputs: Iterable[str],
    bpm_min: int,
    bpm_max: int,
    workout_type: str,
    mood: str,
    preferred_genres: Iterable[str] | None = None,
    min_score: float = 0.0,
    songs_per_segment: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    playlists: list[pd.DataFrame] = []
    seed_df: pd.DataFrame | None = None
    seed_profile: dict[str, float] | None = None
    used_song_keys: set[str] = set()

    for segment_number, (_, segment) in enumerate(segments_df.iterrows(), start=1):
        hr_target = segment_target(segment)
        segment_df = pd.DataFrame(
            {
                "hr_percent_max": [segment["avg_hr_percent_max"]],
                "heart_rate": [segment["avg_heart_rate"]],
            }
        )
        segment_recs, seed_df, seed_profile = recommend_songs(
            songs_df,
            seed_inputs=seed_inputs,
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            workout_type=workout_type,
            mood=mood,
            preferred_genres=preferred_genres,
            workout_df=segment_df,
            min_score=min_score,
            top_n=max(songs_per_segment * 4, songs_per_segment),
        )
        if segment_recs.empty:
            continue

        segment_recs["_song_key"] = segment_recs.apply(_song_key, axis=1).str.lower()
        segment_recs = segment_recs[~segment_recs["_song_key"].isin(used_song_keys)].head(songs_per_segment)
        used_song_keys.update(segment_recs["_song_key"].tolist())
        segment_recs = segment_recs.drop(columns=["_song_key"])

        segment_recs.insert(0, "segment_number", segment_number)
        segment_recs.insert(1, "segment_name", segment["segment_name"])
        segment_recs.insert(2, "start_minute", segment["start_minute"])
        segment_recs.insert(3, "end_minute", segment["end_minute"])
        segment_recs.insert(4, "hr_zone", segment["hr_zone"])
        segment_recs.insert(5, "segment_target_bpm", hr_target["bpm"])
        segment_recs.insert(6, "segment_target_energy", hr_target["energy"])
        playlists.append(segment_recs)

    if not playlists:
        empty = pd.DataFrame()
        if seed_df is None:
            seed_df = find_seed_songs(songs_df, seed_inputs)
        if seed_profile is None:
            seed_profile = seed_feature_profile(seed_df)
        return empty, seed_df, seed_profile

    return pd.concat(playlists, ignore_index=True), seed_df, seed_profile


def bpm_range_fit(bpm: pd.Series, bpm_min: int, bpm_max: int) -> pd.Series:
    midpoint = (bpm_min + bpm_max) / 2
    half_width = max((bpm_max - bpm_min) / 2, 1)
    distance_outside_range = (bpm.astype(float) - midpoint).abs() - half_width
    return (1 - distance_outside_range.clip(lower=0) / 35).clip(0, 1)


def seed_similarity(songs_df: pd.DataFrame, seed_profile: dict[str, float]) -> pd.Series:
    return (
        _similarity(songs_df["bpm"], seed_profile["bpm"], 35) * 0.30
        + _similarity(songs_df["energy"], seed_profile["energy"], 0.45) * 0.22
        + _similarity(songs_df["danceability"], seed_profile["danceability"], 0.40) * 0.22
        + _similarity(songs_df["valence"], seed_profile["valence"], 0.45) * 0.16
        + _similarity(songs_df["acousticness"], seed_profile["acousticness"], 0.50) * 0.10
    ).clip(0, 1)


def workout_fit(songs_df: pd.DataFrame, workout_target: dict[str, float]) -> pd.Series:
    return (
        _similarity(songs_df["bpm"], workout_target["bpm"], 45) * 0.40
        + _similarity(songs_df["energy"], workout_target["energy"], 0.45) * 0.40
        + _similarity(songs_df["danceability"], workout_target["danceability"], 0.45) * 0.20
    ).clip(0, 1)


def mood_genre_fit(
    songs_df: pd.DataFrame,
    mood_target: dict[str, float],
    mood: str,
    preferred_genres: set[str],
) -> pd.Series:
    feature_fit = (
        _similarity(songs_df["energy"], mood_target["energy"], 0.50) * 0.25
        + _similarity(songs_df["danceability"], mood_target["danceability"], 0.45) * 0.25
        + _similarity(songs_df["valence"], mood_target["valence"], 0.50) * 0.25
        + _similarity(songs_df["acousticness"], mood_target["acousticness"], 0.55) * 0.15
    )
    tag_fit = songs_df.apply(lambda row: tag_match(row, mood, preferred_genres), axis=1)
    return (feature_fit + tag_fit * 0.10).clip(0, 1)


def heart_rate_fit(songs_df: pd.DataFrame, hr_target: dict[str, float] | None) -> pd.Series:
    if hr_target is None:
        return pd.Series(0.0, index=songs_df.index)
    return (
        _similarity(songs_df["bpm"], hr_target["bpm"], 45) * 0.45
        + _similarity(songs_df["energy"], hr_target["energy"], 0.45) * 0.55
    ).clip(0, 1)


def tag_match(row: pd.Series, mood: str, preferred_genres: set[str]) -> float:
    tokens = _tokenize(row.get("genre", "")) | _tokenize(row.get("track_genre", "")) | _tokenize(row.get("tags", ""))
    mood_tokens = _tokenize(mood)
    genre_score = 1.0 if preferred_genres and tokens & preferred_genres else 0.0
    mood_score = 1.0 if tokens & mood_tokens else 0.0
    if preferred_genres:
        return max(genre_score, mood_score * 0.7)
    return mood_score


def explain_recommendation(
    row: pd.Series,
    bpm_min: int,
    bpm_max: int,
    workout_type: str,
    mood: str,
    preferred_genres: set[str],
    hr_target: dict[str, float] | None,
) -> str:
    reasons: list[str] = []
    if row["bpm_fit"] >= 0.95:
        reasons.append(f"{row['bpm']:.0f} BPM is inside your target range")
    elif row["bpm_fit"] >= 0.70:
        reasons.append(f"{row['bpm']:.0f} BPM is close to your target range")

    if row["seed_similarity"] >= 0.80:
        reasons.append("audio features are close to the matched seed-song profile")
    elif row["seed_similarity"] >= 0.65:
        reasons.append("audio features are moderately similar to the seed songs")

    if row["workout_fit"] >= 0.75:
        reasons.append(f"energy and tempo fit {workout_type}")

    if row["mood_genre_fit"] >= 0.75:
        reasons.append(f"feature profile fits {mood}")
    if preferred_genres and _tokenize(row.get("genre", "")) & preferred_genres:
        reasons.append("genre matches your preference")

    if hr_target is not None and row["heart_rate_fit"] >= 0.70:
        reasons.append("fits the simulated wearable heart-rate intensity")

    if not reasons:
        reasons.append("balanced score across seed similarity, BPM, workout, and mood")
    return "; ".join(reasons) + "."


def _similarity(value: pd.Series, target: float, scale: float) -> pd.Series:
    return (1 - (value.astype(float) - target).abs() / scale).clip(0, 1)


def _song_key(row: pd.Series) -> str:
    return f"{row['track_name']} - {row['artist']}"


def _tokenize(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    text = str(value).lower().replace(",", ";").replace("|", ";").replace("/", ";")
    return {token.strip() for token in text.split(";") if token.strip()}
