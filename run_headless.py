#!/usr/bin/env python3
"""
run_headless.py

Run the core extractor without GUI. Usage:
  python run_headless.py <youtube_channel_url> [output.json]
"""
import sys
import time
from urllib.parse import urlparse, parse_qs

from scraper import get_video_metadata
from transcripts import fetch_transcript_and_translation
from parser import extract_ingredients
from utils import save_records_to_json


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_headless.py <youtube_channel_url> [output.json]")
        sys.exit(1)

    channel = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else "data.json"

    print(f"Extracting video metadata from: {channel}")
    videos = get_video_metadata(channel)
    total = len(videos)
    print(f"Found {total} videos")

    results = []
    for idx, video in enumerate(videos, start=1):
        vurl = video['youtubeVideoLink']
        vid = video['videoId']
        print(f"[{idx}/{total}] {video['title']}")
        
        try:
            transcript_text, translation_text = fetch_transcript_and_translation(vid)
        except Exception as e:
            print(f"  No transcript for {vid}: {e}")
            transcript_text = ""
            translation_text = ""

        ingredients = extract_ingredients(translation_text or transcript_text)

        video.update({
            "id": idx,
            "transcript": transcript_text,
            "translation": translation_text,
            "ingredients": ingredients,
        })
        results.append(video)

        try:
            save_records_to_json(results, out_file)
        except Exception as e:
            print(f"  Failed saving JSON so far: {e}")

        # small pause to be polite
        time.sleep(0.1)

    print(f"Finished. Saved {len(results)} records to {out_file}")


if __name__ == "__main__":
    main()
