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
    """
    api = YouTubeTranscriptApi()
    
    def extract_text(segments):
        if not segments:
            return ""
        # Handle both dict (old API) and object (new API)
        if isinstance(segments[0], dict):
            return " ".join([s.get("text", "") for s in segments])
        return " ".join([getattr(s, "text", "") for s in segments])

    try:
        # Try to get an English transcript first
        if hasattr(api, 'fetch'):
            segments = api.fetch(video_id, languages=["en"])
        else:
            segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            
        return extract_text(segments), ""
    except Exception:
        # Fallback: get any available transcript and try translating it
        try:
            if hasattr(api, 'list'):
                transcripts = api.list(video_id)
            else:
                transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
                
            transcript_obj = None
            for t in transcripts:
                transcript_obj = t
                break
            if transcript_obj is None:
                raise NoTranscriptFound(video_id)

            orig_segments = transcript_obj.fetch()
            original_text = extract_text(orig_segments)

            translation_text = ""
            try:
                # Check if translation is possible
                # In some versions it's a property, in others a method or attribute
                is_translatable = False
                if hasattr(transcript_obj, 'is_translatable'):
                    is_translatable = transcript_obj.is_translatable
                
                if is_translatable:
                    translated = transcript_obj.translate("en").fetch()
                    translation_text = extract_text(translated)
            except Exception:
                translation_text = ""

            return original_text, translation_text

        except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript):
            raise
        except Exception as e:
            raise e
