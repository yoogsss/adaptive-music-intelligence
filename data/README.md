# Data

The app runs from packaged datasets in this directory. Users do not upload CSVs in the normal MVP flow.

## Song Data

The app loads song features in this order:

1. `data/real_spotify_tracks.csv` if present.
2. `data/demo_songs.csv` as a tiny fallback.

`real_spotify_tracks.csv` is intentionally not required for the repo to run. Add it when you want to test against a larger public Spotify/audio-feature dataset.

Recommended public datasets:

- Hugging Face: `maharshipandya/spotify-tracks-dataset`
  - https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset
- Hugging Face: `engels/spotify-tracks-lite`
  - https://huggingface.co/datasets/engels/spotify-tracks-lite
- Kaggle: Spotify Tracks Dataset
  - https://www.kaggle.com/datasets/yashdev01/spotify-tracks-dataset

The app does not call Spotify APIs, does not use OAuth, and does not depend on Spotify Recommendations, Audio Features, or Audio Analysis endpoints.

## Optional Spotify Metadata Import

A future integration may use Spotify only to read user playlist metadata:

```text
spotify_track_id
track_name
artist
album
popularity
```

Spotify will not be used for BPM, energy, danceability, valence, acousticness, recommendations, or audio analysis.

Imported Spotify playlist tracks must be matched to this local/public audio-feature dataset by normalized `track_name + artist`. If no match exists, the track should be marked:

```text
audio_features_available = false
```

Tracks without local/public audio features are excluded from scoring.

Required normalized song columns:

```text
track_name
artist
bpm
energy
danceability
valence
acousticness
genre
```

The internal loader accepts common alternatives:

```text
tempo -> bpm
artists -> artist
name -> track_name
track_genre -> genre
playlist_genre -> genre
```

## Workout Session Data

`data/demo_workout_sessions.csv` simulates real-time wearable/app heart-rate streams.

Required columns:

```text
session_name
minute
heart_rate
```

Packaged sessions:

- treadmill steady walk
- treadmill incline walk
- stairmaster
- cycling intervals
- boxing
- strength training
- pilates

The app segments each session by heart-rate zone and recommends music for each segment. A future product version would replace this static CSV with live wearable sensor events.
