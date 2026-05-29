from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.recommender import (
    ZONE_LABELS,
    add_hr_zones,
    coerce_numeric_columns,
    dominant_zone,
    recommend_songs,
)


DATA_DIR = Path(__file__).parent / "data"
SAMPLE_WORKOUT = DATA_DIR / "sample_workout.csv"
SAMPLE_SONGS = DATA_DIR / "sample_songs.csv"


st.set_page_config(
    page_title="Adaptive Workout Music Intelligence",
    layout="wide",
)


@st.cache_data
def load_sample_workout() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_WORKOUT)


@st.cache_data
def load_sample_songs() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_SONGS)


def load_uploaded_or_sample(uploaded_file, fallback_loader):
    if uploaded_file is None:
        return fallback_loader()
    return pd.read_csv(uploaded_file)


st.title("Adaptive Workout Music Intelligence")
st.caption("Workout-aware music recommendations using heart-rate zones and audio features.")

with st.sidebar:
    st.header("Workout Context")
    age = st.slider("Age", min_value=16, max_value=75, value=30)
    mood = st.selectbox("Mood", ["Focused", "Happy", "Aggressive", "Calm"])
    intensity = st.selectbox("Target intensity", ["Low", "Moderate", "High"], index=1)
    top_n = st.slider("Recommendations", min_value=3, max_value=15, value=8)

    st.header("Data")
    workout_upload = st.file_uploader(
        "Upload workout CSV",
        type=["csv"],
        help="Expected columns: timestamp, heart_rate.",
    )
    song_upload = st.file_uploader(
        "Upload song feature CSV",
        type=["csv"],
        help="Expected columns: track_name, artist, bpm, energy, danceability, valence.",
    )


try:
    workout_df = load_uploaded_or_sample(workout_upload, load_sample_workout)
    song_df = load_uploaded_or_sample(song_upload, load_sample_songs)

    workout_df = coerce_numeric_columns(workout_df, ["heart_rate"])
    song_df = coerce_numeric_columns(song_df, ["bpm", "energy", "danceability", "valence"])
    workout_with_zones = add_hr_zones(workout_df, age)
    active_zone = dominant_zone(workout_with_zones)
    recommendations = recommend_songs(song_df, active_zone, mood, intensity, top_n=top_n)
except Exception as exc:
    st.error(f"Could not load or process the data: {exc}")
    st.stop()


metric_cols = st.columns(4)
metric_cols[0].metric("Avg heart rate", f"{workout_with_zones['heart_rate'].mean():.0f} bpm")
metric_cols[1].metric("Max heart rate", f"{workout_with_zones['heart_rate'].max():.0f} bpm")
metric_cols[2].metric("Dominant zone", active_zone.replace(" - ", "\n"))
metric_cols[3].metric("Songs scored", f"{len(song_df):,}")

st.subheader("Workout Analysis")
chart_cols = st.columns(2)

with chart_cols[0]:
    st.write("Heart rate over time")
    if "timestamp" in workout_with_zones.columns:
        hr_chart = workout_with_zones.set_index("timestamp")["heart_rate"]
    else:
        hr_chart = workout_with_zones["heart_rate"]
    st.line_chart(hr_chart)

with chart_cols[1]:
    st.write("Heart-rate zone distribution")
    zone_counts = (
        workout_with_zones["hr_zone"]
        .value_counts()
        .reindex(ZONE_LABELS, fill_value=0)
        .rename("minutes")
    )
    st.bar_chart(zone_counts)

st.subheader("Music Library")
music_cols = st.columns(2)

with music_cols[0]:
    st.write("Song BPM distribution")
    bpm_bins = pd.cut(song_df["bpm"], bins=[80, 110, 125, 140, 155, 170, 190])
    bpm_distribution = bpm_bins.value_counts().sort_index()
    bpm_distribution.index = bpm_distribution.index.astype(str)
    st.bar_chart(bpm_distribution)

with music_cols[1]:
    st.write("Recommendation scores")
    score_chart = recommendations.set_index("track_name")["recommendation_score"]
    st.bar_chart(score_chart)

st.subheader("Recommended Songs")
display_columns = [
    "track_name",
    "artist",
    "bpm",
    "energy",
    "danceability",
    "valence",
    "recommendation_score",
    "why_recommended",
]
st.dataframe(
    recommendations[display_columns],
    width="stretch",
    hide_index=True,
)

with st.expander("Preview processed workout data"):
    st.dataframe(workout_with_zones, width="stretch", hide_index=True)

with st.expander("Preview song library"):
    st.dataframe(song_df, width="stretch", hide_index=True)
