#!/usr/bin/env bash
set -euo pipefail

echo "Creating virtualenv in .venv (if not present)"
python3 -m venv .venv || true
echo "Activating venv and installing requirements"
.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install -r requirements.txt
echo "Run the app: .venv/bin/python web_app.py"
