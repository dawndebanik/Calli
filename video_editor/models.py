"""
Data models for transcript representation.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WordTimestamp:
    """Represents a single word with timing information."""

    start: float
    """Start time in seconds."""

    end: float
    """End time in seconds."""

    word: str
    """Word text."""

    def to_dict(self) -> dict:
        """Convert word timestamp to dictionary."""
        return {
            "start": self.start,
            "end": self.end,
            "word": self.word,
        }


@dataclass
class TranscriptSegment:
    """Represents a single segment of a transcript with timing information."""
    
    start: float
    """Start time in seconds."""
    
    end: float
    """End time in seconds."""
    
    text: str
    """Transcribed text for this segment."""

    words: Optional[List[WordTimestamp]] = None
    """Optional word-level timestamps for this segment."""
    
    def to_dict(self) -> dict:
        """Convert segment to dictionary."""
        data = {
            "start": self.start,
            "end": self.end,
            "text": self.text,
        }
        if self.words is not None:
            data["words"] = [word.to_dict() for word in self.words]
        return data


@dataclass
class Transcript:
    """Represents a complete transcript with multiple segments."""
    
    segments: List[TranscriptSegment]
    """List of transcript segments."""
    
    language: Optional[str] = None
    """Detected language code (e.g., 'en', 'es')."""
    
    def to_dict(self) -> dict:
        """Convert transcript to dictionary."""
        return {
            "language": self.language,
            "segments": [segment.to_dict() for segment in self.segments],
        }



