# Adaptive Workout Music Intelligence

Adaptive Workout Music Intelligence is a Streamlit MVP that prototypes a real-time wearable music recommender. Users enter seed songs and choose mood/genre preferences; the app uses packaged heart-rate session timelines to simulate sensor data and builds an ordered playlist across the workout.

The MVP does not expose CSV uploads to normal users. It runs from packaged datasets in `data/` and is ready to swap in a larger internal `data/real_spotify_tracks.csv` dataset.

## Product Model

In the real product, heart-rate data would come from a wearable or fitness app in real time. In this MVP, static packaged workout sessions simulate that stream:

```text
Packaged workout HR timeline
        |
        v
Segment by HR zone/intensity
        |
        v
Use seed-song vibe + segment intensity
        |
        v
Recommend songs per segment
        |
        v
Ordered session playlist
```

UI note shown in the app:

```text
MVP uses static workout sessions to simulate real-time wearable data.
Future version will connect to live sensor streams.
```

## What It Does

- Loads packaged song data from `data/real_spotify_tracks.csv` if available, otherwise `data/demo_songs.csv`.
- Loads packaged workout sessions from `data/demo_workout_sessions.csv`.
- Lets users choose a simulated workout session:
  - treadmill steady walk
  - treadmill incline walk
  - stairmaster
  - cycling intervals
  - boxing
  - strength training
  - pilates
- Keeps seed songs central: the user enters 2-3 seed songs that define the musical vibe.
- Keeps mood and genre preferences as user controls.
- Segments the workout by heart-rate zone and intensity.
- Recommends songs for each workout segment.
- Shows the workout timeline, HR zones, session segments, ordered playlist, and score breakdown.

## Data

See [data/README.md](data/README.md) for packaged data details and real dataset options.

Song dataset load order:

1. `data/real_spotify_tracks.csv`
2. `data/demo_songs.csv`

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

Workout session columns:

```text
session_name
minute
heart_rate
```

The app does not use Spotify OAuth, paid APIs, Spotify Recommendations, Spotify Audio Features, or Spotify Audio Analysis endpoints.

## Optional Spotify Playlist Integration Design

Spotify integration is a future/import layer, not the MVP default.

Allowed Spotify API use:

- User authentication.
- Reading the user's playlists and saved playlist tracks.
- Fetching track metadata:
  - track name
  - artist
  - album
  - Spotify track ID
  - popularity, when available

Disallowed Spotify API use:

- Spotify Recommendations API.
- Spotify Audio Features API.
- Spotify Audio Analysis API.
- Any Spotify-derived BPM, energy, danceability, valence, or acousticness lookup.

How the integration would work:

```text
Spotify playlist tracks
        |
        v
Track name + artist + album + Spotify ID
        |
        v
Match track name + artist against local/public audio-feature dataset
        |
        v
Only matched rows receive BPM/energy/danceability/valence/acousticness
        |
        v
Unmatched tracks are marked audio_features_available = false
        |
        v
Only matched tracks can be scored or recommended
```

This keeps the core recommender unchanged:

- Seed songs define vibe.
- HR zones drive workout progression.
- Local/public audio-feature data provides tempo, energy, danceability, valence, and acousticness.
- Spotify can enrich library access, but it does not generate recommendations or provide audio features.

The matching helper lives in `src/spotify_matching.py`. It is intentionally small and testable so a future OAuth layer can call it after reading playlist metadata.

## Recommendation Logic

The core logic lives in `src/recommender.py`.

For each workout segment, the recommender:

1. Matches the entered seed songs in the packaged song dataset.
2. Builds a seed-song profile from BPM, energy, danceability, valence, and acousticness.
3. Converts the segment heart-rate zone into an intensity target.
4. Scores songs by:
   - BPM fit
   - seed-song similarity
   - workout fit
   - mood/genre fit
   - heart-rate fit
5. Excludes seed songs from the final playlist.
6. Avoids reusing the same recommendation across segments when possible.

The app intentionally raises an error if no seed songs match the packaged dataset. That prevents random high-BPM recommendations without seed context.

## Project Structure

```text
.
|-- app.py
|-- data/
|   |-- README.md
|   |-- demo_songs.csv
|   |-- demo_workout_sessions.csv
|   `-- sample_workout.csv
|-- notebooks/
|   `-- README.md
|-- src/
|   |-- __init__.py
|   |-- data_loader.py
|   |-- recommender.py
|   `-- spotify_matching.py
|-- tests/
|   `-- test_recommender.py
|-- .gitignore
|-- pytest.ini
|-- README.md
`-- requirements.txt
```

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run tests:

```bash
pytest
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Create a new app from this repository.
4. Set the main file path to `app.py`.
5. Deploy.

No secrets are required. To use a larger dataset, add `data/real_spotify_tracks.csv` to the repo or deployment artifact before deploying.

## Future Extensions

- Replace static workout sessions with live wearable or fitness-app sensor streams.
- Add real-time playlist updates as heart-rate intensity changes.
- Add optional Spotify OAuth for playlist import/export while continuing to score only against local/public audio-feature data.
- Add fuzzy seed-song search and autocomplete.
- Add larger packaged public audio-feature dataset support.
- Add workout phase controls such as warmup, steady state, intervals, cooldown.
- Add user feedback controls such as "more like this", "too intense", and "too slow".
- Add playlist export.

## Resume-Friendly Summary

- Built a Streamlit prototype for adaptive workout music recommendations using seed-song similarity and simulated wearable heart-rate timelines.
- Implemented session segmentation by heart-rate zone and generated ordered per-segment playlists with score breakdowns.
- Designed reusable pandas recommendation logic for BPM fit, seed similarity, workout fit, mood/genre fit, and heart-rate intensity fit.
- Kept the MVP deployable without OAuth, paid APIs, external services, or user-facing CSV uploads, while documenting an optional Spotify metadata-only integration path.

## Limitations

- The MVP uses static packaged workout sessions instead of live wearable data.
- `data/demo_songs.csv` is a tiny fallback; a larger `data/real_spotify_tracks.csv` dataset is needed for credible real-world coverage.
- Seed songs must exist in the packaged song dataset.
- Future Spotify playlist integration would still exclude tracks that cannot be matched to local/public audio features.
- Scoring is transparent and rule-based, not machine learning.
