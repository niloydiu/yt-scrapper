# Niloy Kumar Mohonta — YouTube Data Extractor

Niloy Kumar Mohonta curates this simple web app that extracts YouTube video metadata, fetches transcripts (with optional translation), highlights structured items, and saves results to JSON/CSV/TXT/DOCX.

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
-- The app uses `yt-dlp` to list videos from a channel and `youtube-transcript-api` to fetch transcripts.

Contact & branding

- Portfolio: https://niloykm.vercel.app
- Email: niloykumarmohonta@gmail.com
- GitHub: https://github.com/niloydiu

Deploying to Render (free tier)

1. Push your repo to GitHub (already done).
2. Sign in to https://render.com and create a new **Web Service**.
3. Connect the service to the `main` branch of this repository.
4. Set the **Build Command** to:

```
pip install -r requirements.txt
```

and the **Start Command** to:

```
gunicorn web_app:app --bind 0.0.0.0:$PORT --workers 2
```

5. Choose the **Free** plan and create the service — Render will build and run the app. Add a custom domain under the service settings if desired; Render will guide you through DNS records and provide a free TLS certificate.

Notes: Free Render instances may idle and cold-start after inactivity. If you want a site that doesn't sleep, consider a paid plan or other providers.
