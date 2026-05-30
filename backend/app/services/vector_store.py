from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Fixed Name
from langchain_community.vectorstores.pgvector import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.video import VideoMetadata
from app.core.config import settings

class VectorService:
    def __init__(self):
        # Update the instantiation here as well
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GEMINI_API_KEY
        )
        self.connection_string = settings.DATABASE_URL
        self.collection_name = "video_transcripts"
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def process_and_store(self, video_data: VideoMetadata):
        if "failed" in video_data.transcript.lower() or "unavailable" in video_data.transcript.lower():
            print(f"Skipping vectorization for {video_data.video_id}: No valid transcript.")
            return

        meta_payload = {
            "video_id": video_data.video_id,
            "platform": video_data.platform,
            "creator": video_data.creator,
            "engagement_rate": video_data.engagement_rate,
            "views": video_data.views,
            "likes": video_data.likes
        }

        docs = self.text_splitter.create_documents(
            texts=[video_data.transcript],
            metadatas=[meta_payload]
        )

        print(f"Storing {len(docs)} chunks for video: {video_data.video_id}")

        PGVector.from_documents(
            embedding=self.embeddings,
            documents=docs,
            collection_name=self.collection_name,
            connection_string=self.connection_string,
            pre_delete_collection=False
        )