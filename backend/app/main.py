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
        # For testing, assuming URL A is YouTube
        video_a_data = extractor.extract_youtube(request.url_a)
        
        # We will handle Instagram specifically later, just testing YouTube for now
        
        return {
            "status": "success",
            "data": {
                "video_a": video_a_data.model_dump()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))