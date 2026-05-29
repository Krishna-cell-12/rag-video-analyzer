from fastapi import FastAPI, HTTPException
from app.core.config import settings
from app.models.video import ExtractionRequest
from app.services.ingestion import VideoExtractor

app = FastAPI(title=settings.PROJECT_NAME)
extractor = VideoExtractor()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "pgvector_ready"}

@app.post("/api/extract")
async def extract_videos(request: ExtractionRequest):
    try:
        def process_url(url: str):
            if "youtube.com" in url or "youtu.be" in url:
                return extractor.extract_youtube(url)
            elif "instagram.com" in url:
                return extractor.extract_instagram(url)
            else:
                raise ValueError(f"Unsupported URL: {url}")

        video_a_data = process_url(request.url_a)
        video_b_data = process_url(request.url_b)

        return {
            "status": "success",
            "data": {
                "video_a": video_a_data.model_dump(),
                "video_b": video_b_data.model_dump()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))