# app/main.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from app.services.chatbot import VideoChatAgent, HumanMessage, AIMessage
from app.core.config import settings
from app.models.video import ExtractionRequest
from app.services.ingestion import VideoExtractor
from app.services.vector_store import VectorService
from app.services.chatbot import VideoChatAgent, HumanMessage
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.PROJECT_NAME)

# CRITICAL FIX: Allow React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
# Setup chat message tracking schema
class ChatMessageInput(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessageInput]
    video_ids: List[str]

# Instantiate our conversational orchestrator
chat_agent = VideoChatAgent()

@app.post("/api/chat")
async def chat_with_videos(request: ChatRequest):
    try:
        # Convert incoming list into LangChain Message structures
        formatted_messages = []
        for msg in request.messages:
            if msg.role == "user":
                formatted_messages.append(HumanMessage(content=msg.content))
            else:
                formatted_messages.append(AIMessage(content=msg.content))
                
        # Fire up the state machine execution loop
        initial_state = {
            "messages": formatted_messages,
            "video_ids": request.video_ids,
            "context": "",
            "next_node": ""
        }
        
        final_output = chat_agent.agent.invoke(initial_state)
        output_message = final_output["messages"][-1].content
        
        return {"status": "success", "response": output_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    