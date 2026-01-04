"""
transcripts.py

Handles fetching transcripts and translations using youtube-transcript-api.
"""
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)


def fetch_transcript_and_translation(video_id):
    """Fetch transcript for `video_id`.

    Returns a tuple: (original_text, translation_text)
    - If an English transcript is available, original_text will be the English text
      and translation_text will be an empty string.
    - If only a non-English transcript exists, original_text will be the original
      text and translation_text will contain the English translation if available.
    """
    try:
        # Try to get an English transcript first
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])  # may raise
        text = " ".join([s.get("text", "") for s in segments])
        return text, ""
    except Exception:
        # Fallback: get any available transcript and try translating it
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            # pick the first available transcript object
            transcript_obj = None
            for t in transcripts:
                transcript_obj = t
                break
            if transcript_obj is None:
                raise NoTranscriptFound(video_id)

            orig_segments = transcript_obj.fetch()
            original_text = " ".join([s.get("text", "") for s in orig_segments])

            translation_text = ""
            try:
                if getattr(transcript_obj, "is_translatable", False):
                    translated = transcript_obj.translate("en").fetch()
                    translation_text = " ".join([s.get("text", "") for s in translated])
            except Exception:
                translation_text = ""

            return original_text, translation_text

        except TranscriptsDisabled:
            raise
        except NoTranscriptFound:
            raise
        except CouldNotRetrieveTranscript:
            raise
        except Exception as e:
            # Re-raise as generic error for caller to handle
            raise e
