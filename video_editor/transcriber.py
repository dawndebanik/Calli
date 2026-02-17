"""
Transcription module using OpenAI Whisper or faster-whisper.
"""

import os
from typing import Optional, List, Dict, Any

# #region agent log
def _debug_log(payload: Dict[str, Any]) -> None:
    try:
        import json
        from time import time
        payload.setdefault("timestamp", int(time() * 1000))
        with open(r"c:\Users\Debanik\PycharmProjects\VideoEditor\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# #endregion


class Transcriber:
    """
    Transcribes audio files using OpenAI Whisper or faster-whisper.

    Supports configurable model sizes: tiny, base, small, medium, large.
    """

    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    AVAILABLE_BACKENDS = ["openai", "faster"]

    def __init__(
        self,
        model_size: str = "base",
        backend: str = "openai",
        word_timestamps: bool = False,
        device: Optional[str] = None,
        compute_type: Optional[str] = None
    ):
        """
        Initialize the transcriber with a selected backend.

        Args:
            model_size: Size of the Whisper model to use.
                       Options: 'tiny', 'base', 'small', 'medium', 'large'
                       Default: 'base'
            backend: Backend to use ('openai' or 'faster')
            word_timestamps: Enable word-level timestamps (faster-whisper only)
        """
        if model_size not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model size: {model_size}. "
                f"Available options: {', '.join(self.AVAILABLE_MODELS)}"
            )
        if backend not in self.AVAILABLE_BACKENDS:
            raise ValueError(
                f"Invalid backend: {backend}. "
                f"Available options: {', '.join(self.AVAILABLE_BACKENDS)}"
            )
        if word_timestamps and backend != "faster":
            raise ValueError(
                "Word-level timestamps are only supported with backend='faster'."
            )

        self.model_size = model_size
        self.backend = backend
        self.word_timestamps = word_timestamps
        self.device = device
        self.compute_type = compute_type
        self._model = None
    
    def load_model(self) -> None:
        """Load the transcription model (lazy loading)."""
        if self._model is not None:
            return

        if self.backend == "openai":
            import whisper  # Local import to avoid hard dependency
            self._model = whisper.load_model(self.model_size)
        else:
            # #region agent log
            _debug_log({
                "sessionId": "debug-session",
                "runId": "pre-fix",
                "hypothesisId": "H1",
                "location": "transcriber.py:load_model",
                "message": "Preparing faster-whisper import",
                "data": {
                    "hf_symlink_warning_disabled": bool(
                        os.environ.get("HF_HUB_DISABLE_SYMLINKS_WARNING")
                    ),
                },
            })
            # #endregion
            try:
                from faster_whisper import WhisperModel  # Local import
            except ModuleNotFoundError as e:
                raise
            # #region agent log
            cuda_count = None
            ctranslate2_error = None
            try:
                import ctranslate2
                getter = getattr(ctranslate2, "get_cuda_device_count", None)
                cuda_count = getter() if callable(getter) else None
            except Exception as exc:
                ctranslate2_error = str(exc)
            _debug_log({
                "sessionId": "debug-session",
                "runId": "pre-fix",
                "hypothesisId": "H2",
                "location": "transcriber.py:load_model",
                "message": "CTranslate2 environment info",
                "data": {
                    "cuda_device_count": cuda_count,
                    "ctranslate2_error": ctranslate2_error,
                },
            })
            # #endregion
            # #region agent log
            _debug_log({
                "sessionId": "debug-session",
                "runId": "pre-fix",
                "hypothesisId": "H3",
                "location": "transcriber.py:load_model",
                "message": "Initializing WhisperModel with defaults",
                "data": {
                    "model_size": self.model_size,
                    "device": self.device,
                    "compute_type": self.compute_type,
                    "word_timestamps": self.word_timestamps,
                },
            })
            # #endregion
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file
            language: Optional language code (e.g., 'en', 'es').
                     If None, language will be auto-detected.
            task: Task type - 'transcribe' or 'translate' (default: 'transcribe')
            
        Returns:
            Dictionary containing transcription results with segments
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        self.load_model()

        if self.backend == "openai":
            result = self._model.transcribe(
                audio_path,
                language=language,
                task=task,
                verbose=False
            )
            return result

        segments, info = self._model.transcribe(
            audio_path,
            language=language,
            task=task,
            word_timestamps=self.word_timestamps
        )

        formatted_segments: List[Dict[str, Any]] = []
        for segment in segments:
            seg_data: Dict[str, Any] = {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment.text.strip(),
            }
            if self.word_timestamps and segment.words:
                seg_data["words"] = [
                    {
                        "start": float(word.start),
                        "end": float(word.end),
                        "word": word.word.strip(),
                    }
                    for word in segment.words
                    if word.word.strip()
                ]
            formatted_segments.append(seg_data)

        return {
            "language": getattr(info, "language", None),
            "segments": formatted_segments,
        }
    
    def transcribe_to_segments(self, audio_path: str) -> list:
        """
        Transcribe audio and return structured segments.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            List of dictionaries with 'start', 'end', and 'text' keys
        """
        result = self.transcribe(audio_path)

        segments = []
        for segment in result.get("segments", []):
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "words": segment.get("words"),
            })

        return segments



