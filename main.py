#!/usr/bin/env python3
"""
Main CLI script for video/audio transcription.

Usage:
    python main.py <input_file> [options]
"""

import argparse
import os
import sys
from pathlib import Path
from video_editor import (
    AudioExtractor,
    Transcriber,
    TranscriptFormatter,
    OutputFormat,
    Transcript,
    TranscriptSegment,
    WordTimestamp,
    split_segments_by_max_words,
)

# #region agent log
def _debug_log(payload):
    try:
        import json
        from time import time
        payload.setdefault("timestamp", int(time() * 1000))
        with open(r"c:\Users\Debanik\PycharmProjects\VideoEditor\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# #endregion


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract audio from video and generate timed transcript using Whisper"
    )
    
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to input video or audio file"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )

    parser.add_argument(
        "--backend",
        type=str,
        default="openai",
        choices=["openai", "faster"],
        help="Transcription backend to use (default: openai)"
    )

    parser.add_argument(
        "--word-timestamps",
        action="store_true",
        help="Enable word-level timestamps (faster-whisper only)"
    )

    parser.add_argument(
        "--max-words",
        type=int,
        default=None,
        help="Max words per subtitle segment (required with --word-timestamps)"
    )

    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["auto", "cpu", "cuda"],
        help="Device for faster-whisper backend (default: auto)"
    )

    parser.add_argument(
        "--compute-type",
        type=str,
        default=None,
        choices=["auto", "float32", "float16", "int8", "int8_float16"],
        help="Compute type for faster-whisper backend (default: auto)"
    )

    parser.add_argument(
        "--disable-hf-symlink-warning",
        action="store_true",
        help="Disable Hugging Face symlink cache warning on Windows"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for transcript files (default: same as input file)"
    )
    
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Base name for output files (default: input file name without extension)"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        nargs="+",
        choices=["json", "srt"],
        default=["json", "srt"],
        help="Output format(s) (default: json srt)"  
    )
    
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep extracted audio file after transcription"
    )
    
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language code for transcription (e.g., 'en', 'es'). Auto-detected if not specified."
    )
    
    return parser.parse_args()


def get_output_paths(input_file: str, output_dir: str = None, output_name: str = None) -> dict:
    """
    Generate output file paths.
    
    Args:
        input_file: Path to input file
        output_dir: Optional output directory
        output_name: Optional base name for output files
        
    Returns:
        Dictionary with format keys and file paths
    """
    input_path = Path(input_file)
    
    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_name is None:
        output_name = input_path.stem
    
    return {
        "json": str(output_dir / f"{output_name}.json"),
        "srt": str(output_dir / f"{output_name}.srt"),
    }


def main():
    """Main entry point."""
    # #region agent log
    _debug_log({
        "sessionId": "debug-session",
        "runId": "pre-fix",
        "hypothesisId": "H1",
        "location": "main.py:main",
        "message": "Program start",
        "data": {"executable": sys.executable},
    })
    # #endregion
    args = parse_arguments()
    # #region agent log
    _debug_log({
        "sessionId": "debug-session",
        "runId": "pre-fix",
        "hypothesisId": "H1",
        "location": "main.py:main",
        "message": "Parsed args",
        "data": {
            "backend": args.backend,
            "word_timestamps": args.word_timestamps,
            "max_words": args.max_words,
            "device": args.device,
            "compute_type": args.compute_type,
            "disable_hf_symlink_warning": args.disable_hf_symlink_warning,
        },
    })
    # #endregion
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        if args.word_timestamps and args.backend != "faster":
            raise ValueError(
                "Word-level timestamps are only supported with --backend faster."
            )
        if args.word_timestamps and args.max_words is None:
            raise ValueError(
                "--max-words is required when --word-timestamps is enabled."
            )
        if args.disable_hf_symlink_warning:
            os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

        # Step 1: Extract audio (if video) or use audio directly
        print("Step 1: Processing audio...")
        extractor = AudioExtractor()
        
        if extractor.is_video_file(args.input_file):
            print(f"  Extracting audio from video: {args.input_file}")
            audio_path = extractor.extract_audio(
                args.input_file,
                keep_temp=args.keep_audio
            )
            if args.keep_audio:
                print(f"  Audio extracted to: {audio_path}")
        else:
            print(f"  Using audio file directly: {args.input_file}")
            audio_path = args.input_file
        
        # Step 2: Transcribe audio
        print(
            f"\nStep 2: Transcribing audio "
            f"(model: {args.model}, backend: {args.backend})..."
        )
        transcriber = Transcriber(
            model_size=args.model,
            backend=args.backend,
            word_timestamps=args.word_timestamps,
            device=args.device,
            compute_type=args.compute_type,
        )
        result = transcriber.transcribe(audio_path, language=args.language)
        
        # Convert to Transcript object
        segments = []
        for seg in result.get("segments", []):
            words = None
            if seg.get("words"):
                words = [
                    WordTimestamp(
                        start=w["start"],
                        end=w["end"],
                        word=w["word"]
                    )
                    for w in seg["words"]
                ]
            segments.append(
                TranscriptSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                    words=words
                )
            )

        if args.word_timestamps:
            segments = split_segments_by_max_words(segments, args.max_words)
        
        transcript = Transcript(
            segments=segments,
            language=result.get("language")
        )
        
        print(f"  Transcription complete. Language: {transcript.language or 'auto-detected'}")
        print(f"  Found {len(segments)} segments")
        
        # Step 3: Save output files
        print(f"\nStep 3: Saving transcript files...")
        output_paths = get_output_paths(
            args.input_file,
            args.output_dir,
            args.output_name
        )
        
        for fmt in args.format:
            output_format = OutputFormat.JSON if fmt == "json" else OutputFormat.SRT
            output_path = output_paths[fmt]
            
            TranscriptFormatter.save_to_file(transcript, output_path, output_format)
            print(f"  Saved {fmt.upper()}: {output_path}")
        
        print("\n✓ Transcription completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()



