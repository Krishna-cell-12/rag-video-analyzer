from pydantic import BaseModel
from typing import Optional

class VideoMetadata(BaseModel):
    video_id: str
    platform: str
    creator: str
    follower_count: Optional[int] = 0
    views: int
    likes: int
    comments: int
    engagement_rate: float
    transcript: str

class ExtractionRequest(BaseModel):
    url_a: str
    url_b: str