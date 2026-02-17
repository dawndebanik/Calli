# Video Editor - Audio Transcription Tool

A professional Python tool for extracting audio from video files and generating timed transcripts using OpenAI Whisper or faster-whisper.

## Features

- **Video Support**: Extract audio from common video formats (MP4, AVI, MKV, MOV, etc.)
- **Audio Support**: Direct transcription of audio files (MP3, WAV, M4A, etc.)
- **Whisper Integration**: Supports OpenAI's open-source Whisper and faster-whisper backends
- **Configurable Models**: Choose from tiny, base, small, medium, or large Whisper models
- **Multiple Output Formats**: Generate transcripts in JSON and SRT formats
- **Word-Level Timing**: Optional word timestamps and configurable subtitle granularity
- **SOLID Principles**: Clean, maintainable, and extensible code architecture
- **Reusable Library**: Can be imported and used in other Python applications

## Requirements

- Python 3.8+
- ffmpeg (for audio extraction from video files)

### Installing ffmpeg

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Or use: `choco install ffmpeg` (if Chocolatey is installed)

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg  # Debian/Ubuntu
sudo yum install ffmpeg       # CentOS/RHEL
```

## Installation

1. Clone or download this repository
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Basic usage:

```bash
python main.py input_video.mp4
```

This will:
1. Extract audio from the video (if needed)
2. Transcribe using the default "base" model
3. Generate both JSON and SRT transcript files

#### Options

```bash
python main.py input_video.mp4 --model large --format json --output-dir ./transcripts
```

**Available options:**

- `--model`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) - default: `base`
- `--backend`: Transcription backend (`openai`, `faster`) - default: `openai`
- `--word-timestamps`: Enable word-level timestamps (faster-whisper only)
- `--max-words`: Max words per subtitle segment (required with `--word-timestamps`)
- `--device`: Device for faster-whisper (`auto`, `cpu`, `cuda`) - default: `auto`
- `--compute-type`: Compute type for faster-whisper (`auto`, `float32`, `float16`, `int8`, `int8_float16`)
- `--disable-hf-symlink-warning`: Disable Hugging Face symlink cache warning on Windows
- `--output-dir`: Directory for output files - default: same as input file
- `--output-name`: Base name for output files - default: input file name
- `--format`: Output format(s) (`json`, `srt`) - default: both
- `--keep-audio`: Keep extracted audio file after transcription
- `--language`: Language code (e.g., `en`, `es`) - auto-detected if not specified

**Examples:**

```bash
# Use large model for better accuracy
python main.py video.mp4 --model large

# Generate only SRT file
python main.py audio.mp3 --format srt

# Specify output directory and name
python main.py video.mp4 --output-dir ./output --output-name transcript

# Transcribe in Spanish
python main.py video.mp4 --language es

# Word-level timestamps with faster-whisper (max 6 words per subtitle)
python main.py video.mp4 --backend faster --word-timestamps --max-words 6

# Use CPU and float32 to avoid float16 warnings on unsupported hardware
python main.py video.mp4 --backend faster --device cpu --compute-type float32
```

### Using as a Library

The package can be imported and used in other Python applications:

```python
from video_editor import AudioExtractor, Transcriber, TranscriptFormatter, OutputFormat

# Extract audio from video
extractor = AudioExtractor()
audio_path = extractor.extract_audio("video.mp4")

# Transcribe audio (openai backend)
transcriber = Transcriber(model_size="base")
result = transcriber.transcribe(audio_path)

# Transcribe with faster-whisper and word timestamps
transcriber = Transcriber(model_size="base", backend="faster", word_timestamps=True)
result = transcriber.transcribe(audio_path)

# Format and save transcript
from video_editor.models import Transcript, TranscriptSegment

segments = [
    TranscriptSegment(
        start=seg["start"],
        end=seg["end"],
        text=seg["text"].strip()
    )
    for seg in result.get("segments", [])
]

transcript = Transcript(segments=segments, language=result.get("language"))

# Save as JSON
TranscriptFormatter.save_to_file(
    transcript,
    "output.json",
    OutputFormat.JSON
)

# Save as SRT
TranscriptFormatter.save_to_file(
    transcript,
    "output.srt",
    OutputFormat.SRT
)
```

## Project Structure

```
VideoEditor/
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── video_editor/          # Main package
    ├── __init__.py        # Package initialization
    ├── models.py          # Data models (Transcript, TranscriptSegment)
    ├── audio_extractor.py # Audio extraction from video
    ├── transcriber.py     # Whisper transcription backends
    ├── segmenter.py       # Word-based segment splitting
    └── formatters.py      # Output formatting (JSON, SRT)
```

## Architecture

The project follows SOLID principles:

- **Single Responsibility**: Each module has a single, well-defined purpose
- **Open/Closed**: Extensible design for adding new formats or features
- **Liskov Substitution**: Proper use of interfaces and abstractions
- **Interface Segregation**: Focused, minimal interfaces
- **Dependency Inversion**: High-level modules depend on abstractions

## Output Formats

### JSON Format

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Hello, this is a transcript segment."
    }
  ]
}
```

### SRT Format

```
1
00:00:00,000 --> 00:00:05,200
Hello, this is a transcript segment.
```

## Model Sizes

- **tiny**: Fastest, least accurate (~39M parameters)
- **base**: Balanced speed/accuracy (~74M parameters) - **Recommended**
- **small**: Better accuracy (~244M parameters)
- **medium**: High accuracy (~769M parameters)
- **large**: Best accuracy, slowest (~1550M parameters)

## License

This project is open source and available for use in your projects.

## Contributing

Contributions are welcome! Please ensure code follows SOLID principles and includes appropriate tests.



