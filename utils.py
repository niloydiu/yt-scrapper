"""
utils.py

Utility helpers for saving JSON and small helpers.
"""
import json


def save_records_to_json(records, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
