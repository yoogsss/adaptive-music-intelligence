from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ["track_name", "artist", "bpm", "energy", "danceability", "valence", "acousticness", "genre"]

COLUMN_ALIASES = {
    "track_name": ["track_name", "track", "name", "song_name", "title"],
    "artist": ["artist", "artists", "artist_name", "artist_names"],
    "bpm": ["bpm", "tempo"],
    "energy": ["energy", "energy_%", "energy_percent"],
    "danceability": ["danceability", "danceability_%", "danceability_percent"],
    "valence": ["valence", "valence_%", "valence_percent"],
    "acousticness": ["acousticness", "acousticness_%", "acousticness_percent"],
    "genre": ["genre", "genres", "track_genre", "playlist_genre"],
}

NUMERIC_COLUMNS = ["bpm", "energy", "danceability", "valence", "acousticness"]


def load_song_dataset(source) -> pd.DataFrame:
    df = pd.read_csv(source)
    return normalize_song_dataset(df)


def load_song_dataset_from_path(path: str | Path) -> pd.DataFrame:
    return load_song_dataset(path)


def normalize_song_dataset(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]

    rename_map: dict[str, str] = {}
    lower_columns = {column.lower(): column for column in normalized.columns}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower_columns:
                rename_map[lower_columns[alias.lower()]] = canonical
                break

    normalized = normalized.rename(columns=rename_map)
    missing = set(REQUIRED_COLUMNS) - set(normalized.columns)
    if missing:
        raise ValueError(
            "Song dataset is missing required columns after normalization: "
            + ", ".join(sorted(missing))
        )

    normalized = normalized[REQUIRED_COLUMNS + [column for column in normalized.columns if column not in REQUIRED_COLUMNS]]
    for column in NUMERIC_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    normalized = normalized.dropna(subset=REQUIRED_COLUMNS)
    normalized["track_name"] = normalized["track_name"].astype(str)
    normalized["artist"] = normalized["artist"].astype(str).str.replace(";", ", ", regex=False)
    normalized["genre"] = normalized["genre"].astype(str).str.lower()

    for column in ["energy", "danceability", "valence", "acousticness"]:
        if normalized[column].max() > 1:
            normalized[column] = normalized[column] / 100
        normalized[column] = normalized[column].clip(0, 1)

    normalized = normalized[(normalized["bpm"] >= 40) & (normalized["bpm"] <= 240)]
    return normalized.drop_duplicates(subset=["track_name", "artist"]).reset_index(drop=True)
