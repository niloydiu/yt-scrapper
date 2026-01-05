"""
scraper.py

Uses yt-dlp to list all video URLs from a YouTube channel/playlist URL.
Now extracts complete metadata: title, duration, thumbnail, and video link.
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


def get_video_metadata(channel_url):
    """Return list of video metadata dicts with ALL available information.
    
    Returns:
        List of dicts with all possible metadata fields from yt-dlp
    """
    # Force /videos tab if user just provides channel URL
    if '@' in channel_url and '/videos' not in channel_url and '/shorts' not in channel_url:
        if not channel_url.endswith('/'):
            channel_url += '/videos'
        else:
            channel_url += 'videos'
    
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "no_warnings": True,
        "playlistend": None,  # No limit - get ALL videos
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    entries = info.get("entries") or []
    results = []
    
    for e in entries:
        vid = e.get("id") or e.get("url")
        if not vid:
            continue
        
        # Build proper video URL
        if vid.startswith("http"):
            video_url = vid
            # Extract video ID from URL if needed
            if "v=" in vid:
                vid = vid.split("v=")[1].split("&")[0]
            elif "youtu.be/" in vid:
                vid = vid.split("youtu.be/")[1].split("?")[0]
        else:
            video_url = f"https://www.youtube.com/watch?v={vid}"
        
        # Extract ALL available metadata
        title = e.get("title") or e.get("url") or "Untitled"
        duration = e.get("duration") or 0  # in seconds
        
        # Format duration as MM:SS or HH:MM:SS
        if duration:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "N/A"
        
        # Thumbnail URL (high quality)
        thumbnail = e.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        
        # Build comprehensive metadata dict with ALL available fields
        video_data = {
            # Core identifiers
            "videoId": vid,
            "youtubeVideoLink": video_url,
            
            # Basic info
            "title": title,
            "description": e.get("description") or "",
            "duration": duration_str,
            "durationSeconds": duration,
            
            # Media
            "thumbnail": thumbnail,
            "thumbnails": e.get("thumbnails") or [],
            
            # Stats
            "viewCount": e.get("view_count") or 0,
            "likeCount": e.get("like_count") or 0,
            "commentCount": e.get("comment_count") or 0,
            
            # Channel info
            "channel": e.get("channel") or "",
            "channelId": e.get("channel_id") or "",
            "channelUrl": e.get("channel_url") or "",
            "uploader": e.get("uploader") or "",
            "uploaderId": e.get("uploader_id") or "",
            "uploaderUrl": e.get("uploader_url") or "",
            
            # Dates
            "uploadDate": e.get("upload_date") or "",
            "timestamp": e.get("timestamp") or 0,
            "releaseDate": e.get("release_date") or "",
            "releaseTimestamp": e.get("release_timestamp") or 0,
            
            # Content classification
            "categories": e.get("categories") or [],
            "tags": e.get("tags") or [],
            "ageLimit": e.get("age_limit") or 0,
            "availability": e.get("availability") or "",
            "liveStatus": e.get("live_status") or "",
            "isLive": e.get("is_live") or False,
            
            # Quality info
            "resolution": e.get("resolution") or "",
            "width": e.get("width") or 0,
            "height": e.get("height") or 0,
            "fps": e.get("fps") or 0,
            "vcodec": e.get("vcodec") or "",
            "acodec": e.get("acodec") or "",
            
            # Additional metadata
            "playlist": e.get("playlist") or "",
            "playlistId": e.get("playlist_id") or "",
            "playlistIndex": e.get("playlist_index") or 0,
            "language": e.get("language") or "",
            "subtitles": list(e.get("subtitles", {}).keys()) if e.get("subtitles") else [],
            "automaticCaptions": list(e.get("automatic_captions", {}).keys()) if e.get("automatic_captions") else [],
            
            # Engagement
            "averageRating": e.get("average_rating") or 0,
            "dislikeCount": e.get("dislike_count") or 0,
            
            # URLs
            "webpage_url": e.get("webpage_url") or video_url,
            "originalUrl": e.get("original_url") or "",
            
            # Format info
            "ext": e.get("ext") or "",
            "format": e.get("format") or "",
            "formatId": e.get("format_id") or "",
        }
        
        results.append(video_data)
    
    return results
