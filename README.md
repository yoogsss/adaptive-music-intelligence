# Adaptive Workout Music Intelligence

Adaptive Workout Music Intelligence is a Streamlit MVP for real-data seed-song + workout-context music recommendations. It is built for public Spotify/audio-feature CSV datasets and does not use Spotify OAuth, Spotify Recommendations, Spotify Audio Features, Spotify Audio Analysis, paid APIs, or a backend service.

The app is seed-song first: enter 2-3 songs you want to match, choose workout context, mood, genres, and BPM range, then review ranked recommendations with score breakdowns and explanations.

## What It Does

- Loads a real public Spotify/audio-feature CSV by upload or public CSV URL.
- Includes a tiny `data/demo_songs.csv` only so the app runs immediately.
- Matches seed songs from the loaded dataset.
- Builds a seed-song profile from BPM, energy, danceability, valence, and acousticness.
- Scores recommendations by:
  - BPM fit
  - seed-song similarity
  - workout type fit
  - mood/genre fit
  - optional heart-rate fit
- Lets users exclude low-score songs.
- Shows why each song was recommended.
- Keeps heart-rate upload optional and secondary.

## App Inputs

- Workout type:
  - treadmill walk
  - treadmill run
  - stairmaster
  - cycling
  - weight lifting
  - boxing
  - pilates
- Mood:
  - sultry pop
  - club walk
  - dance-pop strut
  - dark pop
  - aggressive
  - focused
  - chill
- Preferred genres from the loaded dataset.
- 2-3 seed songs, one per line.
- Target BPM range.
- Optional heart-rate/workout CSV.

## Data

See [data/README.md](data/README.md) for dataset links and schema details.

Recommended public datasets:

- Hugging Face `maharshipandya/spotify-tracks-dataset`
- Hugging Face `engels/spotify-tracks-lite`
- Kaggle Spotify Tracks Dataset

Required normalized columns:

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

The loader accepts common alternatives such as `tempo` for `bpm`, `artists` for `artist`, and `track_genre` for `genre`.

## Data Flow

```text
Real Spotify/audio-feature CSV
        |
        v
Normalize column names and clean numeric features
        |
        v
Match 2-3 seed songs in the dataset
        |
        v
Build seed-song feature profile
        |
        v
Apply workout, mood, genre, BPM, and optional HR context
        |
        v
Rank recommendations and show score breakdown
```

Optional workout flow:

```text
Workout CSV: timestamp, heart_rate
        |
        v
Estimate max heart rate from age
        |
        v
Classify HR zones
        |
        v
Adjust recommendations with heart-rate fit
```

## Recommendation Logic

The core logic lives in `src/recommender.py`.

Without heart-rate data, the score is:

- Seed similarity: 38%
- BPM fit: 27%
- Mood/genre fit: 20%
- Workout fit: 15%

With heart-rate data, the score is:

- Seed similarity: 35%
- BPM fit: 25%
- Mood/genre fit: 18%
- Workout fit: 14%
- Heart-rate fit: 8%

Seed similarity compares BPM, energy, danceability, valence, and acousticness against the matched seed-song profile. Selected seed songs are excluded from the final recommendations.

The app intentionally raises an error if no seed songs match the loaded dataset. This prevents the recommender from returning random high-BPM tracks without seed context.

## Project Structure

```text
.
|-- app.py
|-- data/
|   |-- README.md
|   |-- demo_songs.csv
|   `-- sample_workout.csv
|-- notebooks/
|   `-- README.md
|-- src/
|   |-- __init__.py
|   |-- data_loader.py
|   `-- recommender.py
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

No secrets are required. For the best deployed experience, upload a real dataset in the app or host a CSV publicly and paste its raw URL.

## Future Extensions

- Add fuzzy seed-song search for typos and alternate artist spellings.
- Add playlist export to CSV.
- Add user-adjustable scoring weights.
- Add workout phase presets such as warmup, steady state, intervals, cooldown.
- Add filters for explicit content, release year, popularity, language, and artist exclusion.
- Add cached loading for a specific public dataset mirror.
- Add a notebook for validating scoring weights against known workout playlists.
- Add feedback controls such as "more like this" and "too intense."

## Resume-Friendly Summary

- Built a Streamlit music recommendation MVP using real-data-ready Spotify/audio-feature CSV ingestion, seed-song similarity, workout context, and explainable score breakdowns.
- Implemented reusable pandas scoring logic for BPM fit, seed similarity, workout fit, mood/genre fit, and optional heart-rate intensity adjustment.
- Added dataset normalization for common public Spotify CSV schemas without relying on Spotify OAuth or restricted/deprecated Spotify recommendation APIs.
- Wrote automated tests covering dataset normalization, seed matching, score breakdowns, seed exclusion, and heart-rate zone helpers.

## Limitations

- The bundled demo CSV is only for interface testing; real recommendations require uploading a real public dataset.
- Seed songs must exist in the loaded dataset.
- Scoring is transparent and rule-based, not machine learning.
- The app recommends tracks but does not stream music or create playlists inside Spotify.
