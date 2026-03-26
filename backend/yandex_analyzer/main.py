import os
import shutil
import tempfile
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any

# Import local components
from .yandex_client import YandexMusicClient
from .downloader import AudioDownloader
from .converter import AudioConverter
from .analyzer import AudioAnalyzer

app = FastAPI(title="Yandex Music Analysis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize components
yandex_client = YandexMusicClient()
downloader = AudioDownloader()
converter = AudioConverter()
analyzer = AudioAnalyzer()

class AnalysisRequest(BaseModel):
    url: str

class AnalysisResponse(BaseModel):
    artist: Optional[str]
    track: Optional[str]
    analysis: Optional[Dict[str, Any]]
    error: Optional[str] = None

def cleanup_files(*paths):
    """Cleanup temporary files after the request is finished."""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error cleaning up {path}: {e}")

@app.get("/")
async def root():
    return {"message": "Yandex Music Analysis API is running"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_track(request: AnalysisRequest, background_tasks: BackgroundTasks):
    url = str(request.url)
    
    # 1. Parse Yandex Music Link
    artist, track_title = yandex_client.parse_url(url)
    if not artist or not track_title:
        raise HTTPException(status_code=400, detail="Could not extract track info from the provided URL")

    download_path = None
    wav_path = None

    try:
        # 2. Search and Download
        download_path = downloader.download_by_search(artist, track_title)
        if not download_path:
            return AnalysisResponse(
                artist=artist,
                track=track_title,
                analysis=None,
                error="Failed to download audio from alternative sources"
            )

        # 3. Convert to WAV
        wav_path = converter.convert_to_wav(download_path)
        if not wav_path:
            return AnalysisResponse(
                artist=artist,
                track=track_title,
                analysis=None,
                error="Failed to convert audio to WAV"
            )

        # 4. Analyze with Librosa
        analysis_results = analyzer.analyze(wav_path)
        if not analysis_results:
            return AnalysisResponse(
                artist=artist,
                track=track_title,
                analysis=None,
                error="Audio analysis failed"
            )

        # Schedule cleanup in background
        background_tasks.add_task(cleanup_files, download_path, wav_path)

        return AnalysisResponse(
            artist=artist,
            track=track_title,
            analysis=analysis_results
        )

    except Exception as e:
        # Emergency cleanup if something crashes before background task
        cleanup_files(download_path, wav_path)
        return AnalysisResponse(
            artist=artist,
            track=track_title,
            analysis=None,
            error=f"Unexpected server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
