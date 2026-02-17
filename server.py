"""
FastAPI server for video transcription web interface.
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Optional
from enum import Enum

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from video_editor import (
    AudioExtractor,
    Transcriber,
    TranscriptFormatter,
    OutputFormat,
    Transcript,
    TranscriptSegment,
    WordTimestamp,
)


# Job status tracking
jobs: Dict[str, Dict] = {}

# Configuration
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Default model configuration
DEFAULT_MODEL = "base"
DEFAULT_BACKEND = "openai"

app = FastAPI(title="Video Transcription API")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


def update_job_status(job_id: str, status: str, progress: int = 0, error: Optional[str] = None):
    """Update job status."""
    if job_id not in jobs:
        jobs[job_id] = {}
    
    jobs[job_id]["status"] = status
    jobs[job_id]["progress"] = progress
    if error:
        jobs[job_id]["error"] = error


def _process_transcription_sync(job_id: str, file_path: str):
    """Synchronous transcription processing (runs in thread pool)."""
    try:
        update_job_status(job_id, JobStatus.PROCESSING, progress=10)
        
        # Step 1: Extract audio (if video)
        extractor = AudioExtractor()
        
        if extractor.is_video_file(file_path):
            update_job_status(job_id, JobStatus.PROCESSING, progress=20)
            audio_path = extractor.extract_audio(file_path, keep_temp=True)
        else:
            audio_path = file_path
        
        update_job_status(job_id, JobStatus.PROCESSING, progress=30)
        
        # Step 2: Transcribe audio
        transcriber = Transcriber(
            model_size=DEFAULT_MODEL,
            backend=DEFAULT_BACKEND,
        )
        
        update_job_status(job_id, JobStatus.PROCESSING, progress=40)
        result = transcriber.transcribe(audio_path)
        
        update_job_status(job_id, JobStatus.PROCESSING, progress=70)
        
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
        
        transcript = Transcript(
            segments=segments,
            language=result.get("language")
        )
        
        update_job_status(job_id, JobStatus.PROCESSING, progress=85)
        
        # Step 3: Generate SRT file
        srt_path = TEMP_DIR / f"{job_id}.srt"
        TranscriptFormatter.save_to_file(transcript, str(srt_path), OutputFormat.SRT)
        
        update_job_status(job_id, JobStatus.COMPLETED, progress=100)
        jobs[job_id]["srt_path"] = str(srt_path)
        jobs[job_id]["filename"] = Path(file_path).stem + ".srt"
        
        # Cleanup audio file if it was temporary
        if extractor.is_video_file(file_path) and audio_path != file_path:
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except OSError:
                pass
        
        # Cleanup uploaded video file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
            
    except Exception as e:
        update_job_status(job_id, JobStatus.ERROR, error=str(e))
        
        # Cleanup on error
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass


async def process_transcription(job_id: str, file_path: str):
    """Background task to process video transcription (async wrapper)."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _process_transcription_sync, job_id, file_path)


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file and start transcription."""
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_path = TEMP_DIR / f"{job_id}_{file.filename}"
    
    try:
        update_job_status(job_id, JobStatus.UPLOADING, progress=0)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Start background task
        asyncio.create_task(process_transcription(job_id, str(file_path)))
        
        return {"job_id": job_id, "status": "uploaded", "message": "File uploaded successfully"}
    
    except Exception as e:
        update_job_status(job_id, JobStatus.ERROR, error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get the status of a transcription job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    response = {
        "status": job.get("status", JobStatus.PENDING),
        "progress": job.get("progress", 0),
    }
    
    if job.get("error"):
        response["error"] = job["error"]
    
    if job.get("status") == JobStatus.COMPLETED:
        response["filename"] = job.get("filename", "transcript.srt")
    
    return response


@app.get("/download/{job_id}")
async def download_srt(job_id: str):
    """Download the SRT file for a completed job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job.get("status") != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    srt_path = job.get("srt_path")
    if not srt_path or not os.path.exists(srt_path):
        raise HTTPException(status_code=404, detail="SRT file not found")
    
    filename = job.get("filename", "transcript.srt")
    
    return FileResponse(
        srt_path,
        media_type="text/plain",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/")
async def root():
    """Root endpoint - redirect to static index if available."""
    index_path = Path("static/index.html")
    if index_path.exists():
        return FileResponse("static/index.html")
    return {"message": "Video Transcription API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

