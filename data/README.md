# Data

The app is designed to work with real public Spotify/audio-feature CSV datasets. It does not call Spotify APIs, does not use Spotify OAuth, and does not depend on Spotify Recommendations, Audio Features, or Audio Analysis endpoints.

## Recommended Public Datasets

Use one of these public datasets, then upload the CSV in the Streamlit app:

- Hugging Face: `maharshipandya/spotify-tracks-dataset`
  - https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset
  - Includes track metadata and audio features such as danceability, energy, valence, tempo, acousticness, and track genre.
- Hugging Face: `engels/spotify-tracks-lite`
  - https://huggingface.co/datasets/engels/spotify-tracks-lite
  - Smaller CSV-format dataset with Spotify-style audio features and `track_genre`.
- Kaggle: Spotify Tracks Dataset
  - https://www.kaggle.com/datasets/yashdev01/spotify-tracks-dataset
  - Includes track names, artists, genre labels, tempo, danceability, energy, acousticness, valence, and related features.

Kaggle may require a free account. Hugging Face datasets are often easier to use for quick prototyping because they provide web-hosted dataset pages and file previews.

## Required Columns

After normalization, the app needs:

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

The loader accepts common alternatives:

```text
tempo -> bpm
artists -> artist
name -> track_name
track_genre -> genre
playlist_genre -> genre
```

`energy`, `danceability`, `valence`, and `acousticness` should be values from `0` to `1`. If a dataset stores them as percentages from `0` to `100`, the loader scales them down automatically.

## Demo CSV

`demo_songs.csv` is a tiny bundled fallback so the app runs immediately. It is not a replacement for a real dataset and should only be used to test the interface.

For credible recommendations, upload a real public dataset with thousands of tracks.
