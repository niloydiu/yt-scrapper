#!/usr/bin/env bash
# start.sh — start the YouTube extractor web app using the local virtualenv
set -euo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"

PYTHON_BIN=".venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  echo "Virtualenv Python not found at $PYTHON_BIN"
  echo "Activate your virtualenv or create it with: python -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

# Kill any running instance started by this user on the same script (best-effort)
pkill -f "web_app.py" || true

# Run the app in the foreground so logs are visible. Use nohup or & to background it.
exec "$PYTHON_BIN" web_app.py
