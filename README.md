# YouTube Extractor

Simple app that extracts video URLs from a YouTube channel, fetches transcripts, optionally translates them to English, extracts structured items from transcripts, and saves results to a JSON file.

Setup

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

This repository now runs as a Flask web app. To try locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python web_app.py
```

Notes
- Item extraction uses simple heuristics in `parser.py`. For improved accuracy, integrate a better NLP model.
- The app uses `yt-dlp` to list videos from a channel and `youtube-transcript-api` to fetch transcripts.
