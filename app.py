from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_loader import load_song_dataset_from_path
from src.recommender import (
    ZONE_LABELS,
    add_hr_zones,
    available_moods,
    available_workout_types,
    recommend_for_workout_segments,
    segment_workout_session,
)


DATA_DIR = Path(__file__).parent / "data"
DEMO_SONGS = DATA_DIR / "demo_songs.csv"
REAL_SONGS = DATA_DIR / "real_spotify_tracks.csv"
DEMO_WORKOUT_SESSIONS = DATA_DIR / "demo_workout_sessions.csv"

st.set_page_config(page_title="Adaptive Workout Music Intelligence", layout="wide")


@st.cache_data
def load_packaged_songs() -> tuple[pd.DataFrame, str]:
    if REAL_SONGS.exists():
        return load_song_dataset_from_path(REAL_SONGS), "data/real_spotify_tracks.csv"
    return load_song_dataset_from_path(DEMO_SONGS), "data/demo_songs.csv"


@st.cache_data
def load_workout_sessions() -> pd.DataFrame:
    return pd.read_csv(DEMO_WORKOUT_SESSIONS)


def parse_seed_text(seed_text: str) -> list[str]:
    return [line.strip() for line in seed_text.splitlines() if line.strip()]


st.title("Adaptive Workout Music Intelligence")
st.caption("Seed-song playlists adapted to simulated wearable heart-rate timelines.")
st.info(
    "MVP uses static workout sessions to simulate real-time wearable data. "
    "Future version will connect to live sensor streams."
)

try:
    song_df, song_source = load_packaged_songs()
    sessions_df = load_workout_sessions()
except Exception as exc:
    st.error(f"Could not load packaged data: {exc}")
    st.stop()

session_names = available_workout_types()
genres = sorted(song_df["genre"].dropna().astype(str).str.lower().unique().tolist())

with st.sidebar:
    st.header("Workout Session")
    selected_session = st.selectbox("Session", session_names, index=0)
    age = st.slider("Age", min_value=16, max_value=75, value=30)

    st.header("Music Preferences")
    mood = st.selectbox("Mood", available_moods(), index=1)
    target_bpm = st.slider("Preferred BPM range", min_value=70, max_value=190, value=(105, 135))
    preferred_genres = st.multiselect(
        "Preferred genres",
        options=genres,
        default=[genre for genre in ["pop", "dance pop"] if genre in genres],
    )

    st.header("Filters")
    min_score = st.slider("Exclude songs below score", 0.0, 1.0, 0.55, 0.05)
    songs_per_segment = st.slider("Songs per segment", min_value=1, max_value=4, value=2)

session_df = sessions_df[sessions_df["session_name"] == selected_session].copy()
if session_df.empty:
    st.error(f"No packaged workout session found for: {selected_session}")
    st.stop()

workout_with_zones = add_hr_zones(session_df, age)
segments_df = segment_workout_session(session_df, age)

st.subheader("Seed Songs")
seed_col, profile_col = st.columns([2, 1])
with seed_col:
    seed_text = st.text_area(
        "Enter 2-3 seed songs, one per line",
        value="São Paulo - The Weeknd\nLike JENNIE - JENNIE\nPromiscuous - Nelly Furtado",
        help="Use 'Track - Artist' or 'Track by Artist'. Seeds must exist in the packaged song dataset.",
        height=110,
    )

try:
    playlist_df, seed_df, seed_profile = recommend_for_workout_segments(
        song_df,
        segments_df=segments_df,
        seed_inputs=parse_seed_text(seed_text),
        bpm_min=target_bpm[0],
        bpm_max=target_bpm[1],
        workout_type=selected_session,
        mood=mood,
        preferred_genres=preferred_genres,
        min_score=min_score,
        songs_per_segment=songs_per_segment,
    )
except Exception as exc:
    st.error(f"Could not generate session playlist: {exc}")
    st.stop()

with profile_col:
    st.metric("Song dataset", song_source)
    st.metric("Matched seeds", len(seed_df))
    st.metric("Seed BPM", f"{seed_profile['bpm']:.0f}")
    st.metric("Segments", len(segments_df))

st.write("Matched seed-song profile")
seed_display = ["track_name", "artist", "bpm", "energy", "danceability", "valence", "acousticness", "genre"]
st.dataframe(seed_df[seed_display], width="stretch", hide_index=True)

st.subheader("Workout Timeline")
timeline_cols = st.columns(2)
with timeline_cols[0]:
    st.write("Heart-rate timeline")
    st.line_chart(workout_with_zones.set_index("minute")["heart_rate"])
with timeline_cols[1]:
    st.write("HR zone distribution")
    zone_counts = workout_with_zones["hr_zone"].value_counts().reindex(ZONE_LABELS, fill_value=0)
    st.bar_chart(zone_counts)

st.subheader("Session Segments")
segments_display = [
    "segment_name",
    "start_minute",
    "end_minute",
    "avg_heart_rate",
    "avg_hr_percent_max",
    "hr_zone",
]
st.dataframe(segments_df[segments_display], width="stretch", hide_index=True)

st.subheader("Ordered Session Playlist")
if playlist_df.empty:
    st.warning("No songs passed the score filter for the simulated workout segments. Lower the minimum score or widen the BPM range.")
else:
    playlist_columns = [
        "segment_number",
        "segment_name",
        "track_name",
        "artist",
        "bpm",
        "genre",
        "recommendation_score",
        "bpm_fit",
        "seed_similarity",
        "workout_fit",
        "mood_genre_fit",
        "heart_rate_fit",
        "segment_target_bpm",
        "segment_target_energy",
        "why_recommended",
    ]
    st.dataframe(playlist_df[playlist_columns], width="stretch", hide_index=True)

    st.write("Score breakdown by playlist order")
    breakdown = playlist_df.copy()
    breakdown["playlist_item"] = breakdown.apply(
        lambda row: f"S{int(row['segment_number'])}: {row['track_name']}",
        axis=1,
    )
    st.bar_chart(
        breakdown.set_index("playlist_item")[
            ["bpm_fit", "seed_similarity", "workout_fit", "mood_genre_fit", "heart_rate_fit"]
        ]
    )

with st.expander("Packaged song dataset preview"):
    st.write(f"{len(song_df):,} usable tracks loaded from {song_source}")
    st.dataframe(song_df.head(100), width="stretch", hide_index=True)

with st.expander("Packaged heart-rate timeline"):
    st.dataframe(workout_with_zones, width="stretch", hide_index=True)
