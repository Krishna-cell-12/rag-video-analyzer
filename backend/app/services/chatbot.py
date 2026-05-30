from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings # Fixed Name
from langchain_community.vectorstores.pgvector import PGVector
from app.core.config import settings

class AgentState(TypedDict):
    messages: List[BaseMessage]
    video_ids: List[str]
    context: str
    next_node: str
    
class VideoChatAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", 
            google_api_key=settings.GEMINI_API_KEY,
            streaming=True
        )
        # Update the instantiation here as well
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GEMINI_API_KEY
        )
        self.store = PGVector(
            collection_name="video_transcripts",
            connection_string=settings.DATABASE_URL,
            embedding_function=self.embeddings
        )
        
        self.workflow = self._create_workflow()
        self.agent = self.workflow.compile()

    def router_node(self, state: AgentState) -> Dict[str, Any]:
        last_message = state["messages"][-1].content.lower()
        if any(word in last_message for word in ["views", "likes", "comments", "engagement", "stats", "popular"]):
            return {"next_node": "fetch_metadata"}
        return {"next_node": "retrieve_transcript_chunks"}

    def fetch_metadata_node(self, state: AgentState) -> Dict[str, Any]:
        video_ids = state.get("video_ids", [])
        if not video_ids:
            return {"context": "No specific video data loaded in active state."}
            
        context_str = "=== Video Performance Metrics ===\n"
        for v_id in video_ids:
            docs = self.store.similarity_search(
                query="summary", 
                k=1, 
                filter={"video_id": v_id}
            )
            if docs:
                m = docs[0].metadata
                context_str += f"Platform: {m['platform'].upper()} | Creator: {m['creator']} | ID: {m['video_id']}\n"
                context_str += f" - Views: {m['views']} | Likes: {m['likes']}\n"
                context_str += f" - Engagement Rate: {m['engagement_rate']}%\n\n"
                
        return {"context": context_str}

    def retrieve_chunks_node(self, state: AgentState) -> Dict[str, Any]:
        last_message = state["messages"][-1].content
        video_ids = state.get("video_ids", [])
        
        docs = self.store.similarity_search(
            query=last_message, 
            k=4,
            filter={"video_id": {"$in": video_ids}} if video_ids else None
        )
        
        context_str = "=== Relevant Video Transcript Segments ===\n"
        for doc in docs:
            context_str += f"[{doc.metadata['creator']} ({doc.metadata['platform']})]: \"{doc.page_content}\"\n\n"
            
        return {"context": context_str}

    def generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert Social Media Data Analyst. Your goal is to compare two specific videos "
            "based strictly on the gathered context data provided below. Provide concise, impactful engineering "
            "and content insights. Always cite which creator or platform you are referencing.\n\n"
            f"Context Resource:\n{state['context']}"
        )
        
        messages = [HumanMessage(content=system_prompt)] + state["messages"]
        response = self.llm.invoke(messages)
        return {"messages": state["messages"] + [response]}

    def _create_workflow(self) -> StateGraph:
        graph = StateGraph(AgentState)
        graph.add_node("router", self.router_node)
        graph.add_node("fetch_metadata", self.fetch_metadata_node)
        graph.add_node("retrieve_transcript_chunks", self.retrieve_chunks_node)
        graph.add_node("generate", self.generate_response_node)
        
        graph.set_entry_point("router")
        graph.add_conditional_edges(
            "router",
            lambda state: state["next_node"],
            {
                "fetch_metadata": "fetch_metadata",
                "retrieve_transcript_chunks": "retrieve_transcript_chunks"
            }
        )
        graph.add_edge("fetch_metadata", "generate")
        graph.add_edge("retrieve_transcript_chunks", "generate")
        graph.add_edge("generate", END)
        
        return graph