#!/usr/bin/env python3
"""
run_headless.py

Run the core extractor without GUI. Usage:
  python run_headless.py <youtube_channel_url> [output.json]
"""
import sys
import time
from urllib.parse import urlparse, parse_qs

from scraper import get_video_urls
from transcripts import fetch_transcript_and_translation
from parser import extract_ingredients
from utils import save_records_to_json


def extract_video_id(vurl):
    parsed = urlparse(vurl)
    q = parse_qs(parsed.query)
    vid = q.get("v", [None])[0]
    if not vid:
        vid = parsed.path.split("/")[-1]
    return vid


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_headless.py <youtube_channel_url> [output.json]")
        sys.exit(1)

    channel = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else "data.json"

    print(f"Extracting video list from: {channel}")
    video_urls = get_video_urls(channel)
    total = len(video_urls)
    print(f"Found {total} videos")

    results = []
    for idx, vurl in enumerate(video_urls, start=1):
        print(f"[{idx}/{total}] {vurl}")
        vid = extract_video_id(vurl)
        try:
            transcript_text, translation_text = fetch_transcript_and_translation(vid)
        except Exception as e:
            print(f"  No transcript for {vid}: {e}")
            transcript_text = ""
            translation_text = ""

        ingredients = extract_ingredients(translation_text or transcript_text)

        record = {
            "id": idx,
            "youtubeVideoLink": vurl,
            "transcript": transcript_text,
            "translation": translation_text,
            "ingredients": ingredients,
        }
        results.append(record)

        try:
            save_records_to_json(results, out_file)
        except Exception as e:
            print(f"  Failed saving JSON so far: {e}")

        # small pause to be polite
        time.sleep(0.2)

    print(f"Finished. Saved {len(results)} records to {out_file}")


if __name__ == "__main__":
    main()
