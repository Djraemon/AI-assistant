"""
Web application for the AI Teaching Assistant using FastAPI.
AI助教RAG系统 - 基于FastAPI的Web应用程序
"""

# Standard library imports (标准库导入)
import os
import sys
import json
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

# Third-party imports (第三方库导入)
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Local imports (本地模块导入)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv

from src.config import CONFIG
from src.data_ingestor import DataIngestor, get_data_stats
from src.index_manager import IndexManager
from src.query_engine import TeachingQueryEngine
from src.evaluation import EvaluationManager

# Load environment variables (加载环境变量)
load_dotenv()

# Set up templates directory
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'templates')
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)


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

    # Check API keys
    siliconflow_api_key = CONFIG.model_config.api_key
    openai_like_api_key = CONFIG.model_config.openai_like_api_key

    if CONFIG.model_config.provider == "openai_like":
        # Use phi-3.5-mini LLM with SiliconFlow embedding (hybrid approach)
        from llama_index.llms.openai_like import OpenAILike
        from llama_index.embeddings.siliconflow import SiliconFlowEmbedding

        if not openai_like_api_key:
            print("WARNING: OPENAI_LIKE_API_KEY not set. Please set this environment variable.")
            print("Example: export OPENAI_LIKE_API_KEY='your-api-key-here'")
            yield
            return

        if not siliconflow_api_key:
            print("WARNING: SILICONFLOW_API_KEY not set. Please set this environment variable.")
            print("Example: export SILICONFLOW_API_KEY='your-siliconflow-api-key'")
            yield
            return

        Settings.llm = OpenAILike(
            model=CONFIG.model_config.openai_like_model,
            api_base=CONFIG.model_config.openai_like_api_base,
            api_key=openai_like_api_key,
            is_chat_model=CONFIG.model_config.is_chat_model
        )

        Settings.embed_model = SiliconFlowEmbedding(
            api_key=siliconflow_api_key,
            model_name=CONFIG.model_config.embedding_model
        )
        print(f"Initialized with hybrid model:")
        print(f"  LLM: {CONFIG.model_config.openai_like_model} (OpenAI-like)")
        print(f"  Embedding: {CONFIG.model_config.embedding_model} (SiliconFlow)")
    else:
        # Use SiliconFlow configuration (existing)
        from llama_index.embeddings.siliconflow import SiliconFlowEmbedding
        from llama_index.llms.siliconflow import SiliconFlow

        if not siliconflow_api_key:
            print("WARNING: SILICONFLOW_API_KEY not set. Please set this environment variable.")
            print("Example: export SILICONFLOW_API_KEY='your-siliconflow-api-key'")
            yield
            return

        Settings.embed_model = SiliconFlowEmbedding(
            api_key=siliconflow_api_key,
            model_name=CONFIG.model_config.embedding_model
        )

        Settings.llm = SiliconFlow(
            api_key=siliconflow_api_key,
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
        yield
        return

    # Initialize index manager
    index_manager = IndexManager(CONFIG)

    # Create or load composite index
    print("Creating/loading index...")
    composite_index = index_manager.create_or_load_composite_index(all_nodes)

    if composite_index is None:
        print("Failed to create index. Exiting.")
        yield
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


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main page of the web application."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"Template loading error: {e}")
        # Return a simple error page if template fails
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🎓 AI助教RAG系统 - 错误</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 50px; text-align: center; }
                .error-container { max-width: 600px; margin: 0 auto; }
                .error-message { color: #dc3545; background: #f8d7da; padding: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>🎓 AI助教RAG系统</h1>
                <div class="error-message">
                    <h2>页面加载失败</h2>
                    <p>抱歉，模板文件加载失败。请联系管理员或稍后重试。</p>
                    <p><small>错误信息：模板文件未找到或配置错误</small></p>
                </div>
            </div>
        </body>
        </html>
        """, status_code=500)


@app.post("/api/rag/query", response_model=QueryResponse)
@app.post("/api/rag/v1/chat/completions", response_model=QueryResponse)
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


@app.post("/api/rag/feedback")
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


@app.get("/api/rag/stats")
async def get_stats():
    """Get system statistics and performance metrics."""
    global eval_manager
    
    if not eval_manager:
        raise HTTPException(status_code=500, detail="Evaluation manager not initialized")
    
    try:
        performance = eval_manager.get_system_performance()
        # Get data statistics
        from src.data_ingestor import DataIngestor
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


@app.post("/api/rag/stream")
async def stream_chat_endpoint(request: StreamChatRequest):
    """RAG Chat API with Server-Sent Events streaming response."""
    global query_engine, eval_manager
    
    if not query_engine:
        raise HTTPException(status_code=500, detail="Query engine not initialized")
    
    async def event_generator():
        try:
            # Send start event
            yield f"event: start\n"
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

            # Process the query with streaming
            async for chunk in query_engine.query_stream(request.question):
                if chunk["type"] == "delta":
                    yield f"event: delta\n"
                    yield f"data: {json.dumps({'type': 'delta', 'content': chunk['content'], 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                elif chunk["type"] == "sources":
                    yield f"event: sources\n"
                    yield f"data: {json.dumps({'type': 'sources', 'sources': chunk['sources'], 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

            # Send end event
            # For now, just send a placeholder for total tokens
            yield f"event: end\n"
            yield f"data: {json.dumps({'type': 'end', 'total_tokens': 150, 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
        except Exception as e:
            # Send error event if something goes wrong
            yield f"event: error\n"
            yield f"data: {json.dumps({'type': 'error', 'message': f'Error processing query: {str(e)}', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
    
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