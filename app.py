from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_loader import load_song_dataset, load_song_dataset_from_path
from src.recommender import (
    ZONE_LABELS,
    add_hr_zones,
    available_moods,
    available_workout_types,
    dominant_zone,
    recommend_songs,
)


DATA_DIR = Path(__file__).parent / "data"
DEMO_SONGS = DATA_DIR / "demo_songs.csv"
SAMPLE_WORKOUT = DATA_DIR / "sample_workout.csv"

st.set_page_config(page_title="Adaptive Workout Music Intelligence", layout="wide")


@st.cache_data
def load_demo_songs() -> pd.DataFrame:
    return load_song_dataset_from_path(DEMO_SONGS)


@st.cache_data
def load_songs_from_url(url: str) -> pd.DataFrame:
    return load_song_dataset(url)


@st.cache_data
def load_sample_workout() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_WORKOUT)


def parse_seed_text(seed_text: str) -> list[str]:
    return [line.strip() for line in seed_text.splitlines() if line.strip()]


def load_workout(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return load_sample_workout()
    return pd.read_csv(uploaded_file)


st.title("Adaptive Workout Music Intelligence")
st.caption("Real-data-ready seed-song + workout-context music recommendations. No Spotify OAuth or API calls.")

with st.sidebar:
    st.header("Dataset")
    data_source = st.radio("Song data source", ["Demo CSV", "Upload CSV", "CSV URL"], index=0)
    uploaded_songs = st.file_uploader(
        "Upload real Spotify/audio-feature CSV",
        type=["csv"],
        help="Required after normalization: track_name, artist, bpm/tempo, energy, danceability, valence, acousticness, genre.",
    )
    dataset_url = st.text_input(
        "Public CSV URL",
        placeholder="https://.../spotify_tracks.csv",
        help="Use a raw CSV URL from a public dataset mirror or hosted file.",
    )

    st.header("Workout")
    workout_type = st.selectbox("Workout type", available_workout_types(), index=0)
    mood = st.selectbox("Mood", available_moods(), index=1)
    target_bpm = st.slider("Target BPM range", min_value=70, max_value=190, value=(105, 135))

    st.header("Filters")
    min_score = st.slider("Exclude songs below score", 0.0, 1.0, 0.55, 0.05)
    top_n = st.slider("Max recommendations", min_value=5, max_value=50, value=15)

    st.header("Optional Heart Rate")
    use_workout_csv = st.checkbox("Use heart-rate CSV", value=False)
    age = st.slider("Age", min_value=16, max_value=75, value=30, disabled=not use_workout_csv)
    workout_upload = st.file_uploader(
        "Upload workout CSV",
        type=["csv"],
        help="Expected columns: timestamp, heart_rate.",
        disabled=not use_workout_csv,
    )

try:
    if data_source == "Upload CSV":
        if uploaded_songs is None:
            st.info("Upload a real Spotify/audio-feature CSV to use this mode.")
            st.stop()
        song_df = load_song_dataset(uploaded_songs)
        demo_mode = False
    elif data_source == "CSV URL":
        if not dataset_url.strip():
            st.info("Paste a public raw CSV URL to use this mode.")
            st.stop()
        song_df = load_songs_from_url(dataset_url.strip())
        demo_mode = False
    else:
        song_df = load_demo_songs()
        demo_mode = True
except Exception as exc:
    st.error(f"Could not load song dataset: {exc}")
    st.stop()

if demo_mode:
    st.warning(
        "Demo mode uses a tiny bundled CSV so the app runs immediately. "
        "For real recommendations, upload a public Spotify/audio-feature dataset."
    )

genres = sorted(song_df["genre"].dropna().astype(str).str.lower().unique().tolist())

st.subheader("Seed Songs")
seed_col, profile_col = st.columns([2, 1])
with seed_col:
    seed_text = st.text_area(
        "Enter 2-3 seed songs, one per line",
        value="São Paulo - The Weeknd\nLike JENNIE - JENNIE\nPromiscuous - Nelly Furtado",
        help="Use 'Track - Artist' or 'Track by Artist'. Seeds must exist in the loaded dataset.",
        height=110,
    )
    preferred_genres = st.multiselect(
        "Preferred genres",
        options=genres,
        default=[genre for genre in ["pop", "dance pop"] if genre in genres],
    )

workout_with_zones = None
active_zone = None
if use_workout_csv:
    try:
        workout_df = load_workout(workout_upload)
        workout_with_zones = add_hr_zones(workout_df, age)
        active_zone = dominant_zone(workout_with_zones)
    except Exception as exc:
        st.error(f"Could not load workout data: {exc}")
        st.stop()

try:
    recommendations, seed_df, seed_profile = recommend_songs(
        song_df,
        seed_inputs=parse_seed_text(seed_text),
        bpm_min=target_bpm[0],
        bpm_max=target_bpm[1],
        workout_type=workout_type,
        mood=mood,
        preferred_genres=preferred_genres,
        workout_df=workout_with_zones,
        min_score=min_score,
        top_n=top_n,
    )
except Exception as exc:
    st.error(f"Could not generate recommendations: {exc}")
    st.stop()

with profile_col:
    st.metric("Matched seeds", len(seed_df))
    st.metric("Seed BPM", f"{seed_profile['bpm']:.0f}")
    st.metric("Seed energy", f"{seed_profile['energy']:.2f}")
    st.metric("Songs after filter", len(recommendations))

st.write("Matched seed-song profile")
seed_display = ["track_name", "artist", "bpm", "energy", "danceability", "valence", "acousticness", "genre"]
st.dataframe(seed_df[seed_display], width="stretch", hide_index=True)

st.subheader("Recommendations")
if recommendations.empty:
    st.warning("No songs passed the score filter. Lower the minimum score or widen the BPM range.")
else:
    display_columns = [
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
        "energy",
        "danceability",
        "valence",
        "acousticness",
        "why_recommended",
    ]
    st.dataframe(recommendations[display_columns], width="stretch", hide_index=True)

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.write("Recommendation scores")
        st.bar_chart(recommendations.set_index("track_name")["recommendation_score"])
    with chart_cols[1]:
        st.write("Score breakdown")
        breakdown = recommendations.set_index("track_name")[
            ["bpm_fit", "seed_similarity", "workout_fit", "mood_genre_fit", "heart_rate_fit"]
        ]
        st.bar_chart(breakdown)

with st.expander("Dataset preview"):
    st.write(f"{len(song_df):,} usable tracks loaded")
    st.dataframe(song_df.head(100), width="stretch", hide_index=True)

if use_workout_csv and workout_with_zones is not None:
    st.subheader("Optional Heart-Rate Context")
    metric_cols = st.columns(3)
    metric_cols[0].metric("Avg heart rate", f"{workout_with_zones['heart_rate'].mean():.0f} bpm")
    metric_cols[1].metric("Max heart rate", f"{workout_with_zones['heart_rate'].max():.0f} bpm")
    metric_cols[2].metric("Dominant zone", active_zone.replace(" - ", "\n"))

    workout_cols = st.columns(2)
    with workout_cols[0]:
        st.write("Heart rate over time")
        if "timestamp" in workout_with_zones.columns:
            st.line_chart(workout_with_zones.set_index("timestamp")["heart_rate"])
        else:
            st.line_chart(workout_with_zones["heart_rate"])
    with workout_cols[1]:
        st.write("Heart-rate zone distribution")
        zone_counts = workout_with_zones["hr_zone"].value_counts().reindex(ZONE_LABELS, fill_value=0)
        st.bar_chart(zone_counts)
