# app/main.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from app.core.config import settings
from app.models.video import ExtractionRequest
from app.services.ingestion import VideoExtractor
from app.services.vector_store import VectorService

app = FastAPI(title=settings.PROJECT_NAME)

# Initialize our services
extractor = VideoExtractor()
vector_db = VectorService()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "pgvector_ready"}

@app.post("/api/extract")
async def extract_videos(request: ExtractionRequest, background_tasks: BackgroundTasks):
    try:
        def process_url(url: str):
            if "youtube.com" in url or "youtu.be" in url:
                return extractor.extract_youtube(url)
            elif "instagram.com" in url:
                return extractor.extract_instagram(url)
            else:
                raise ValueError(f"Unsupported URL: {url}")

        # 1. Extract raw data and transcripts
        video_a_data = process_url(request.url_a)
        video_b_data = process_url(request.url_b)

        # 2. Run vectorization as a background task so the API responds instantly
        # (This is a top 1% engineering trick to prevent HTTP timeouts!)
        background_tasks.add_task(vector_db.process_and_store, video_a_data)
        background_tasks.add_task(vector_db.process_and_store, video_b_data)

        return {
            "status": "success",
            "message": "Videos extracted. Transcripts are currently being vectorized in the background.",
            "data": {
                "video_a": video_a_data.model_dump(),
                "video_b": video_b_data.model_dump()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))