# Adaptive Workout Music Intelligence

Adaptive Workout Music Intelligence is a lightweight Python + Streamlit MVP that recommends workout songs using heart-rate zone context and audio features. It is designed as a small analytics product, not a production music platform: no Spotify OAuth, no paid APIs, no database, and no complex backend.

The app runs immediately with bundled sample CSVs, while still allowing users to upload their own workout and song-feature data.

## What It Does

- Loads sample or uploaded heart-rate workout data.
- Loads sample or uploaded song/audio-feature data.
- Estimates max heart rate from age using `220 - age`.
- Classifies each workout record into a heart-rate training zone.
- Finds the dominant workout zone for the session.
- Scores songs against the workout context using BPM, energy, danceability, mood, and target intensity.
- Displays charts for heart rate over time, zone distribution, song BPM distribution, and recommendation scores.
- Shows a plain-English explanation for why each song was recommended.

## Data Flow

```text
Workout CSV              Song Feature CSV
timestamp, heart_rate    track_name, artist, bpm, energy, danceability, valence
        |                         |
        v                         v
Clean numeric fields      Clean numeric fields
        |                         |
        v                         v
Classify HR zones         Keep audio features
        |                         |
        v                         |
Find dominant zone        |
        +-------------+-----------+
                      v
       Score songs for zone + mood + intensity
                      |
                      v
      Ranked recommendations with explanations
```

## Recommendation Logic

The scoring logic lives in `src/recommender.py` so it can be tested separately from the Streamlit UI.

1. The app estimates max heart rate as `220 - age`.
2. Each heart-rate row is assigned to a training zone:
   - Zone 1: recovery
   - Zone 2: endurance
   - Zone 3: tempo
   - Zone 4: threshold
   - Zone 5: peak
3. The dominant zone becomes the workout context.
4. The selected mood maps to a target valence value.
5. The selected intensity adjusts target BPM and energy.
6. Each song receives a weighted recommendation score:
   - BPM match: 38%
   - Energy match: 28%
   - Danceability match: 16%
   - Mood/valence match: 18%

The explanation text is rule-based and describes whether a song fits the target tempo, energy, and mood profile. This is intentionally simple and transparent for an MVP.

## Project Structure

```text
.
|-- app.py
|-- data/
|   |-- sample_songs.csv
|   `-- sample_workout.csv
|-- notebooks/
|   `-- README.md
|-- src/
|   |-- __init__.py
|   `-- recommender.py
|-- tests/
|   `-- test_recommender.py
|-- .gitignore
|-- pytest.ini
|-- README.md
`-- requirements.txt
```

## Sample Data

The project includes free, synthetic sample data so the app works without external accounts or downloads.

Workout data format:

```csv
timestamp,heart_rate
00:00,102
00:01,108
```

Song feature data format:

```csv
track_name,artist,bpm,energy,danceability,valence
Tempo Lock,Metro Signal,143,0.67,0.74,0.55
```

`energy`, `danceability`, and `valence` should be numeric values from `0` to `1`. `bpm` and `heart_rate` should be numeric.

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the app:

```bash
streamlit run app.py
```

Run tests:

```bash
pytest
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Create a new app from the GitHub repository.
4. Set the main file path to `app.py`.
5. Deploy the app.

Streamlit Community Cloud will install packages from `requirements.txt`. No secrets are required because the project does not use OAuth, private APIs, or paid services.

## Future Extensions

Practical next steps that would build on the current MVP:

- Add user-adjustable scoring weights for BPM, energy, danceability, and valence.
- Support longer workout files with lap, segment, or interval labels.
- Recommend songs by workout phase, such as warmup, endurance block, intervals, and cooldown.
- Add playlist export to CSV.
- Add better validation messages for malformed uploaded files.
- Compare recommendation quality across multiple workouts.
- Integrate a free public audio-feature dataset if licensing allows redistribution.
- Add a notebook for exploratory analysis of workout zones and song-feature distributions.

## Resume-Friendly Summary

Honest project bullets:

- Built a Streamlit analytics MVP that recommends workout music from heart-rate zones, workout intensity, mood, and song audio features.
- Implemented reusable pandas-based recommendation logic with automated tests for heart-rate zone classification and song scoring.
- Created a deployable no-API data app with bundled sample CSVs, upload workflows, interactive charts, and explainable recommendations.
- Structured the project for Streamlit Community Cloud deployment with a simple `app.py`, tested core logic, and clear setup documentation.

## Limitations

- Uses synthetic sample data by default.
- Uses estimated max heart rate, not a medically personalized threshold model.
- Uses rule-based scoring rather than machine learning.
- Does not stream music or connect to Spotify.
