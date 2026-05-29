# app/services/vector_store.py

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.video import VideoMetadata
from app.core.config import settings

class VectorService:
    def __init__(self):
        # Initialize the embedding model
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY, 
            model="text-embedding-3-small"
        )
        self.connection_string = settings.DATABASE_URL
        self.collection_name = "video_transcripts"
        
        # Configure the chunker (400 characters, 50 overlap to keep context context intact)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def process_and_store(self, video_data: VideoMetadata):
        # 1. Skip if transcript failed
        if "failed" in video_data.transcript.lower() or "unavailable" in video_data.transcript.lower():
            print(f"Skipping vectorization for {video_data.video_id}: No valid transcript.")
            return

        # 2. Define the exact metadata payload for every chunk
        meta_payload = {
            "video_id": video_data.video_id,
            "platform": video_data.platform,
            "creator": video_data.creator,
            "engagement_rate": video_data.engagement_rate,
            "views": video_data.views,
            "likes": video_data.likes
        }

        # 3. Slice the transcript into documents and inject metadata
        docs = self.text_splitter.create_documents(
            texts=[video_data.transcript],
            metadatas=[meta_payload]
        )

        print(f"Storing {len(docs)} chunks for video: {video_data.video_id}")

        # 4. Insert into pgvector
        PGVector.from_documents(
            embedding=self.embeddings,
            documents=docs,
            collection_name=self.collection_name,
            connection_string=self.connection_string,
            pre_delete_collection=False # Appends data instead of overwriting the whole DB
        )