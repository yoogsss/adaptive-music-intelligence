from __future__ import annotations

from dataclasses import dataclass
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

ZONE_TARGETS = {
    "Zone 1 - Recovery": {"bpm": 115, "energy": 0.35, "danceability": 0.55},
    "Zone 2 - Endurance": {"bpm": 128, "energy": 0.50, "danceability": 0.65},
    "Zone 3 - Tempo": {"bpm": 145, "energy": 0.68, "danceability": 0.72},
    "Zone 4 - Threshold": {"bpm": 160, "energy": 0.82, "danceability": 0.78},
    "Zone 5 - Peak": {"bpm": 175, "energy": 0.92, "danceability": 0.82},
}

MOOD_VALENCE_TARGETS = {
    "Focused": 0.52,
    "Happy": 0.82,
    "Aggressive": 0.35,
    "Calm": 0.65,
}

INTENSITY_ADJUSTMENTS = {
    "Low": {"bpm": -8, "energy": -0.12},
    "Moderate": {"bpm": 0, "energy": 0.0},
    "High": {"bpm": 10, "energy": 0.10},
}


@dataclass(frozen=True)
class WorkoutProfile:
    age: int = 30
    mood: str = "Focused"
    intensity: str = "Moderate"

    @property
    def max_hr(self) -> int:
        return 220 - self.age


def classify_hr_zone(heart_rate: float, max_hr: float) -> str:
    """Classify heart rate into common percentage-of-max training zones."""
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
    df["hr_zone"] = df["heart_rate"].apply(lambda hr: classify_hr_zone(float(hr), max_hr))
    df["hr_percent_max"] = df["heart_rate"] / max_hr
    return df


def dominant_zone(workout_df: pd.DataFrame) -> str:
    if "hr_zone" not in workout_df.columns:
        raise ValueError("Workout data must include an hr_zone column.")
    return workout_df["hr_zone"].mode().iloc[0]


def target_for_context(zone: str, mood: str, intensity: str) -> dict[str, float]:
    zone_target = ZONE_TARGETS.get(zone, ZONE_TARGETS["Zone 3 - Tempo"]).copy()
    mood_target = MOOD_VALENCE_TARGETS.get(mood, MOOD_VALENCE_TARGETS["Focused"])
    adjustment = INTENSITY_ADJUSTMENTS.get(intensity, INTENSITY_ADJUSTMENTS["Moderate"])

    return {
        "bpm": zone_target["bpm"] + adjustment["bpm"],
        "energy": float(np.clip(zone_target["energy"] + adjustment["energy"], 0, 1)),
        "danceability": zone_target["danceability"],
        "valence": mood_target,
    }


def _similarity(value: pd.Series, target: float, scale: float) -> pd.Series:
    return (1 - (value.astype(float) - target).abs() / scale).clip(0, 1)


def recommend_songs(
    songs_df: pd.DataFrame,
    zone: str,
    mood: str,
    intensity: str,
    top_n: int = 8,
) -> pd.DataFrame:
    required = {"track_name", "artist", "bpm", "energy", "danceability", "valence"}
    missing = required - set(songs_df.columns)
    if missing:
        raise ValueError(f"Song data is missing columns: {', '.join(sorted(missing))}")

    target = target_for_context(zone, mood, intensity)
    scored = songs_df.copy()
    scored["bpm_match"] = _similarity(scored["bpm"], target["bpm"], 45)
    scored["energy_match"] = _similarity(scored["energy"], target["energy"], 0.6)
    scored["danceability_match"] = _similarity(scored["danceability"], target["danceability"], 0.55)
    scored["mood_match"] = _similarity(scored["valence"], target["valence"], 0.65)
    scored["recommendation_score"] = (
        scored["bpm_match"] * 0.38
        + scored["energy_match"] * 0.28
        + scored["danceability_match"] * 0.16
        + scored["mood_match"] * 0.18
    ).round(3)
    scored["why_recommended"] = scored.apply(
        lambda row: explain_recommendation(row, target, zone, mood, intensity),
        axis=1,
    )
    return scored.sort_values("recommendation_score", ascending=False).head(top_n)


def explain_recommendation(
    song: pd.Series,
    target: dict[str, float],
    zone: str,
    mood: str,
    intensity: str,
) -> str:
    bpm_delta = abs(float(song["bpm"]) - target["bpm"])
    energy_delta = abs(float(song["energy"]) - target["energy"])
    valence_delta = abs(float(song["valence"]) - target["valence"])

    reasons: list[str] = []
    if bpm_delta <= 10:
        reasons.append("tempo closely matches the workout target")
    elif float(song["bpm"]) > target["bpm"]:
        reasons.append("tempo adds an extra push")
    else:
        reasons.append("tempo supports a steadier pace")

    if energy_delta <= 0.12:
        reasons.append("energy fits the selected intensity")
    elif float(song["energy"]) > target["energy"]:
        reasons.append("higher energy can lift effort")
    else:
        reasons.append("lower energy helps control effort")

    if valence_delta <= 0.18:
        reasons.append(f"mood profile fits {mood.lower()} training")

    return f"{zone}, {intensity.lower()} intensity: " + "; ".join(reasons) + "."


def coerce_numeric_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    clean = df.copy()
    for column in columns:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    return clean.dropna(subset=list(columns))
