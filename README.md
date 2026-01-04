# YouTube Recipe Ingredient Extractor

Simple PyQt6 desktop app that extracts video URLs from a YouTube channel, fetches transcripts, optionally translates them to English, extracts ingredient lists, and saves results to a JSON file.

Setup

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

PyQt6 (may require system GL libraries):

```bash
python app.py
```

Tkinter (lighter-weight alternative, recommended if PyQt6 fails):

```bash
python app_tk.py
```

Notes
- Ingredient extraction uses a simple heuristic by default. For better accuracy, enable `openai` usage in `parser.py` and provide an API key.
- If you encounter errors importing PyQt6 (for example `libGL.so.1` missing), prefer running the Tkinter UI via `app_tk.py` which avoids those system dependencies.
- The app uses `yt-dlp` (Python library) to list videos from a channel and `youtube-transcript-api` to fetch transcripts.
