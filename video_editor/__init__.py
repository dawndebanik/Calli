"""
Video Editor - A professional video/audio transcription tool.

This package provides functionality to extract audio from video files
and generate timed transcripts using OpenAI Whisper.
"""

from video_editor.audio_extractor import AudioExtractor
from video_editor.transcriber import Transcriber
from video_editor.formatters import TranscriptFormatter, OutputFormat
from video_editor.models import TranscriptSegment, Transcript, WordTimestamp
from video_editor.segmenter import split_segments_by_max_words

__version__ = "1.0.0"
__all__ = [
    "AudioExtractor",
    "Transcriber",
    "TranscriptFormatter",
    "OutputFormat",
    "TranscriptSegment",
    "Transcript",
    "WordTimestamp",
    "split_segments_by_max_words",
]



