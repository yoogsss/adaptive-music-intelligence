# Adaptive Workout Music Intelligence

A simple Python + Streamlit analytics MVP that recommends workout songs from heart-rate zones, workout intensity, mood, BPM, energy, danceability, and valence.

No Spotify OAuth, paid APIs, or backend services are required. The app ships with small realistic sample CSVs so it runs immediately.

## Features

- Upload or load sample heart-rate workout data.
- Load sample song/audio-feature data.
- Classify heart-rate zones using percent of estimated max heart rate.
- Recommend songs using BPM, energy, danceability, valence, mood, and intensity.
- Show charts for heart rate over time, heart-rate zones, BPM distribution, and recommendation scores.
- Explain why each song was recommended.

## Project Structure

```text
.
├── app.py
├── data/
│   ├── sample_songs.csv
│   └── sample_workout.csv
├── notebooks/
├── src/
│   ├── __init__.py
│   └── recommender.py
├── tests/
│   └── test_recommender.py
├── README.md
└── requirements.txt
```

## Local Run

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

## Expected CSV Formats

Workout CSV:

```csv
timestamp,heart_rate
00:00,102
00:01,108
```

Song feature CSV:

```csv
track_name,artist,bpm,energy,danceability,valence
Tempo Lock,Metro Signal,143,0.67,0.74,0.55
```

`energy`, `danceability`, and `valence` should be numeric values from 0 to 1. `bpm` should be numeric.

## Free Streamlit Community Cloud Deployment

1. Push this repository to GitHub.
2. Go to [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Create a new app from the GitHub repository.
4. Set the main file path to `app.py`.
5. Deploy. Streamlit installs dependencies from `requirements.txt`.

## Recommendation Logic

The app estimates max heart rate as `220 - age`, classifies each workout row into a zone, then uses the dominant zone as the workout context. Songs are scored against target BPM, energy, danceability, and mood valence. The highest scoring songs are displayed with a short recommendation explanation.

## Resume Bullet Suggestions

- Built a Streamlit analytics MVP that recommends workout music by combining heart-rate zones, audio features, mood, and intensity signals.
- Designed reusable Python recommendation logic with automated tests for zone classification and song scoring behavior.
- Created a deployable data app using free sample datasets, CSV upload flows, pandas transformations, and interactive charts.
- Implemented explainable recommendation output so users can see how BPM, energy, and mood alignment affected each song ranking.
