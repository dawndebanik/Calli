"""
Output formatters for transcript data.
"""

from enum import Enum
from typing import List, Dict
from video_editor.models import Transcript, TranscriptSegment


class OutputFormat(Enum):
    """Supported output formats."""
    JSON = "json"
    SRT = "srt"


class TranscriptFormatter:
    """
    Formats transcript data into various output formats.
    
    Supports JSON and SRT formats.
    """
    
    @staticmethod
    def format_json(transcript: Transcript) -> str:
        """
        Format transcript as JSON.
        
        Args:
            transcript: Transcript object to format
            
        Returns:
            JSON string representation
        """
        import json
        return json.dumps(transcript.to_dict(), indent=2, ensure_ascii=False)
    
    @staticmethod
    def format_srt(transcript: Transcript) -> str:
        """
        Format transcript as SRT (SubRip) subtitle format.
        
        Args:
            transcript: Transcript object to format
            
        Returns:
            SRT formatted string
        """
        srt_lines = []
        
        for index, segment in enumerate(transcript.segments, start=1):
            start_time = TranscriptFormatter._seconds_to_srt_time(segment.start)
            end_time = TranscriptFormatter._seconds_to_srt_time(segment.end)
            
            srt_lines.append(f"{index}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(segment.text)
            srt_lines.append("")  # Empty line between entries
        
        return "\n".join(srt_lines)
    
    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """
        Convert seconds to SRT time format (HH:MM:SS,mmm).
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    @staticmethod
    def format(transcript: Transcript, output_format: OutputFormat) -> str:
        """
        Format transcript in the specified format.
        
        Args:
            transcript: Transcript object to format
            output_format: Desired output format
            
        Returns:
            Formatted string
        """
        if output_format == OutputFormat.JSON:
            return TranscriptFormatter.format_json(transcript)
        elif output_format == OutputFormat.SRT:
            return TranscriptFormatter.format_srt(transcript)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    @staticmethod
    def save_to_file(
        transcript: Transcript,
        output_path: str,
        output_format: OutputFormat
    ) -> None:
        """
        Save transcript to a file in the specified format.
        
        Args:
            transcript: Transcript object to save
            output_path: Path to output file
            output_format: Desired output format
        """
        content = TranscriptFormatter.format(transcript, output_format)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)







