"""
scraper.py

Uses yt-dlp to list all video URLs from a YouTube channel/playlist URL.
The function returns a list of full YouTube watch URLs.
"""
from yt_dlp import YoutubeDL


def get_video_urls(channel_url):
    """Return list of video watch URLs extracted from the provided channel URL.

    Uses yt-dlp with `extract_flat` to avoid downloading video data.
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        # Use extract_flat to get entries quickly without downloading
        "extract_flat": "in_playlist",
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    entries = info.get("entries") or []
    urls = []
    for e in entries:
        vid = e.get("id") or e.get("url")
        if not vid:
            continue
        if vid.startswith("http"):
            urls.append(vid)
        else:
            urls.append(f"https://www.youtube.com/watch?v={vid}")

    return urls
