"""
Audio extraction module for extracting audio from video files.
"""

import os
from pathlib import Path
from typing import Optional
import subprocess
import tempfile


class AudioExtractor:
    """
    Extracts audio from video files using ffmpeg.
    
    Supports common video formats (mp4, avi, mkv, mov, etc.)
    and audio formats (mp3, wav, m4a, etc.).
    """
    
    # Common video extensions
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    
    # Common audio extensions
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma'}
    
    def __init__(self, output_format: str = "wav"):
        """
        Initialize the audio extractor.
        
        Args:
            output_format: Output audio format (default: 'wav')
        """
        self.output_format = output_format
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> None:
        """Check if ffmpeg is available in the system."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "ffmpeg is not installed or not found in PATH. "
                "Please install ffmpeg to use audio extraction functionality."
            )
    
    def is_video_file(self, file_path: str) -> bool:
        """
        Check if the file is a video file based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file appears to be a video file
        """
        extension = Path(file_path).suffix.lower()
        return extension in self.VIDEO_EXTENSIONS
    
    def is_audio_file(self, file_path: str) -> bool:
        """
        Check if the file is an audio file based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file appears to be an audio file
        """
        extension = Path(file_path).suffix.lower()
        return extension in self.AUDIO_EXTENSIONS
    
    def extract_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        keep_temp: bool = False
    ) -> str:
        """
        Extract audio from a video file or return the path if already audio.
        
        Args:
            input_path: Path to input video or audio file
            output_path: Optional output path for extracted audio.
                        If None, creates a temporary file.
            keep_temp: If True, keep temporary files (default: False)
            
        Returns:
            Path to the audio file
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # If it's already an audio file, return the path
        if self.is_audio_file(input_path):
            return input_path
        
        # If it's not a video file, raise an error
        if not self.is_video_file(input_path):
            raise ValueError(
                f"Unsupported file format: {input_path}. "
                f"Expected video or audio file."
            )
        
        # Generate output path if not provided
        if output_path is None:
            suffix = f".{self.output_format}"
            output_path = tempfile.mktemp(suffix=suffix)
            if not keep_temp:
                # Register for cleanup if not keeping temp
                import atexit
                atexit.register(lambda: self._cleanup_temp(output_path))
        
        # Extract audio using ffmpeg
        self._extract_with_ffmpeg(input_path, output_path)
        
        return output_path
    
    def _extract_with_ffmpeg(self, input_path: str, output_path: str) -> None:
        """
        Extract audio using ffmpeg command.
        
        Args:
            input_path: Path to input video file
            output_path: Path to output audio file
        """
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le" if self.output_format == "wav" else "copy",
            "-ar", "16000",  # Sample rate for Whisper (16kHz recommended)
            "-ac", "1",  # Mono
            "-y",  # Overwrite output file
            output_path
        ]
        
        try:
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown error"
            raise RuntimeError(f"Failed to extract audio: {error_msg}")
    
    @staticmethod
    def _cleanup_temp(file_path: str) -> None:
        """Clean up temporary file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass  # Ignore cleanup errors







