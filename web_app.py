"""Web application for the AI Teaching Assistant using FastAPI."""

import os
import sys
import json
import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from data_ingestor import DataIngestor, get_data_stats
from index_manager import IndexManager
from query_engine import TeachingQueryEngine
from evaluation import EvaluationManager


# Global variables to store the system components
rag_system = None
query_engine = None
eval_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the RAG system when the application starts."""
    global rag_system, query_engine, eval_manager
    
    print("Initializing AI Teaching Assistant Web App...")
    
    # Initialize models based on provider configuration
    from llama_index.core import Settings

    if CONFIG.model_config.provider == "openai_like":
        # Use phi-3.5-mini LLM with SiliconFlow embedding (hybrid approach)
        from llama_index.llms.openai_like import OpenAILike
        from llama_index.embeddings.siliconflow import SiliconFlowEmbedding

        Settings.llm = OpenAILike(
            model=CONFIG.model_config.openai_like_model,
            api_base=CONFIG.model_config.openai_like_api_base,
            api_key=CONFIG.model_config.openai_like_api_key,
            is_chat_model=CONFIG.model_config.is_chat_model
        )

        Settings.embed_model = SiliconFlowEmbedding(
            api_key=CONFIG.model_config.api_key,
            model_name=CONFIG.model_config.embedding_model
        )
        print(f"Initialized with hybrid model:")
        print(f"  LLM: {CONFIG.model_config.openai_like_model} (OpenAI-like)")
        print(f"  Embedding: {CONFIG.model_config.embedding_model} (SiliconFlow)")
    else:
        # Use SiliconFlow configuration (existing)
        from llama_index.embeddings.siliconflow import SiliconFlowEmbedding
        from llama_index.llms.siliconflow import SiliconFlow

        Settings.embed_model = SiliconFlowEmbedding(
            api_key=CONFIG.model_config.api_key,
            model_name=CONFIG.model_config.embedding_model
        )

        Settings.llm = SiliconFlow(
            api_key=CONFIG.model_config.api_key,
            model=CONFIG.model_config.llm_model
        )
        print(f"Initialized with SiliconFlow model: {CONFIG.model_config.llm_model}")
    
    # Initialize data ingestor
    data_ingestor = DataIngestor(CONFIG)
    
    # Ingest all available data
    print("Ingesting data from all sources...")
    all_nodes = data_ingestor.ingest_all_data()
    
    if not all_nodes:
        print("No data found to process. Please add documents to the data directories.")
        return
    
    # Initialize index manager
    index_manager = IndexManager(CONFIG)
    
    # Create or load composite index
    print("Creating/loading index...")
    composite_index = index_manager.create_or_load_composite_index(all_nodes)
    
    if composite_index is None:
        print("Failed to create index. Exiting.")
        return
    
    # Initialize query engine
    query_engine = TeachingQueryEngine(None, CONFIG, composite_index)
    eval_manager = EvaluationManager(CONFIG)
    
    print("AI Teaching Assistant Web App initialized successfully!")
    
    yield
    
    print("Shutting down AI Teaching Assistant Web App...")


app = FastAPI(
    title="AI Teaching Assistant",
    description="A web-based AI assistant for educational purposes",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files directory (for CSS, JS, images)
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up templates directory
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str
    mode: str = "general"


class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: Optional[int] = None
    comment: Optional[str] = None


class StreamChatRequest(BaseModel):
    user_id: str
    question: str
    session_id: str
    stream: bool = True


class QueryResponse(BaseModel):
    query: str
    response: str
    evaluation: dict


from web_source import index
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main page of the web application."""
    html_content = index.html_content
    return HTMLResponse(content=html_content)


@app.post("/api/query", response_model=QueryResponse)
@app.post("/v1/chat/completions", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """Process a query and return the response."""
    global query_engine, eval_manager
    
    if not query_engine:
        raise HTTPException(status_code=500, detail="Query engine not initialized")
    
    try:
        response = query_engine.query(request.query)
        response_text = str(response)
        
        # Evaluate the response
        evaluation = eval_manager.evaluate_and_log(request.query, response_text)
        
        return QueryResponse(
            query=request.query,
            response=response_text,
            evaluation=evaluation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/api/feedback")
async def feedback_endpoint(request: FeedbackRequest):
    """Collect feedback for a query-response pair."""
    global eval_manager
    
    if not eval_manager:
        raise HTTPException(status_code=500, detail="Evaluation manager not initialized")
    
    try:
        eval_manager.evaluate_and_log(
            request.query,
            request.response,
            user_rating=request.rating,
            user_comment=request.comment
        )
        return {"message": "Feedback received successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get system statistics and performance metrics."""
    global eval_manager
    
    if not eval_manager:
        raise HTTPException(status_code=500, detail="Evaluation manager not initialized")
    
    try:
        performance = eval_manager.get_system_performance()
        # Get data statistics
        from data_ingestor import DataIngestor
        data_ingestor = DataIngestor(CONFIG)
        all_nodes = data_ingestor.ingest_all_data()
        data_stats = get_data_stats(all_nodes)
        
        return {
            "performance_metrics": performance["evaluation_metrics"],
            "feedback_summary": performance["feedback_summary"],
            "data_stats": data_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "AI Teaching Assistant is running"}


@app.post("/api/rag/chat/stream")
async def stream_chat_endpoint(request: StreamChatRequest):
    """RAG Chat API with Server-Sent Events streaming response."""
    global query_engine, eval_manager
    
    if not query_engine:
        raise HTTPException(status_code=500, detail="Query engine not initialized")
    
    async def event_generator():
        try:
            # Send start event
            yield f"event: start\n"
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.datetime.utcnow().isoformat()+'Z'})}\n\n"
            # Process the query with streaming
            async for chunk in query_engine.query_stream(request.question):
                if chunk["type"] == "delta":
                    yield f"event: delta\n"
                    yield f"data: {json.dumps({'type': 'delta', 'content': chunk['content'], 'timestamp': datetime.datetime.utcnow().isoformat()+'Z'})}\n\n"
                elif chunk["type"] == "sources":
                    yield f"event: sources\n"
                    yield f"data: {json.dumps({'type': 'sources', 'sources': chunk['sources'], 'timestamp': datetime.datetime.utcnow().isoformat()+'Z'})}\n\n"
            # Send end event
            # For now, just send a placeholder for total tokens
            yield f"event: end\n"
            yield f"data: {json.dumps({'type': 'end', 'total_tokens': 150, 'timestamp': datetime.datetime.utcnow().isoformat()+'Z'})}\n\n"            
        except Exception as e:
            # Send error event if something goes wrong
            yield f"event: error\n"
            yield f"data: {json.dumps({'type': 'error', 'message': f'Error processing query: {str(e)}', 'timestamp': datetime.datetime.utcnow().isoformat()+'Z'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)