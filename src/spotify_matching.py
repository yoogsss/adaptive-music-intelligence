from __future__ import annotations

import re

import pandas as pd


SPOTIFY_METADATA_COLUMNS = ["spotify_track_id", "track_name", "artist", "album", "popularity"]
AUDIO_FEATURE_COLUMNS = ["bpm", "energy", "danceability", "valence", "acousticness", "genre"]


def normalize_track_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value).lower()
    text = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def match_spotify_tracks_to_audio_features(
    spotify_tracks: pd.DataFrame,
    audio_features: pd.DataFrame,
) -> pd.DataFrame:
    """Attach local/public audio features to Spotify playlist metadata.

    Spotify is treated as a metadata source only. Rows that cannot be matched
    by normalized track name + artist are marked unavailable and excluded from
    scoring by callers.
    """
    required_spotify = {"track_name", "artist"}
    required_features = {"track_name", "artist", *AUDIO_FEATURE_COLUMNS}
    missing_spotify = required_spotify - set(spotify_tracks.columns)
    missing_features = required_features - set(audio_features.columns)
    if missing_spotify:
        raise ValueError(f"Spotify metadata is missing columns: {', '.join(sorted(missing_spotify))}")
    if missing_features:
        raise ValueError(f"Audio feature data is missing columns: {', '.join(sorted(missing_features))}")

    spotify = spotify_tracks.copy()
    features = audio_features.copy()
    spotify["_match_key"] = spotify.apply(match_key, axis=1)
    features["_match_key"] = features.apply(match_key, axis=1)

    feature_cols = ["_match_key", *AUDIO_FEATURE_COLUMNS]
    matched = spotify.merge(features[feature_cols].drop_duplicates("_match_key"), on="_match_key", how="left")
    matched["audio_features_available"] = matched[AUDIO_FEATURE_COLUMNS].notna().all(axis=1)
    return matched.drop(columns=["_match_key"])


def scoring_ready_tracks(matched_tracks: pd.DataFrame) -> pd.DataFrame:
    return matched_tracks[matched_tracks["audio_features_available"]].copy()


def match_key(row: pd.Series) -> str:
    return f"{normalize_track_text(row['track_name'])}::{normalize_track_text(row['artist'])}"
