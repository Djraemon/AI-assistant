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
from src.file_scanner import AutoIndexer

# Load environment variables (加载环境变量)
load_dotenv()

# Set model provider from environment variable if available
model_provider = os.getenv("RAG_MODEL_PROVIDER", CONFIG.model_config.provider)
CONFIG.model_config.provider = model_provider

# Set up templates directory
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'templates')
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

print(f"🔧 Using model provider: {CONFIG.model_config.provider}")


# Global variables to store the system components
rag_system = None
query_engine = None
eval_manager = None
auto_indexer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the RAG system when the application starts."""
    global rag_system, query_engine, eval_manager, auto_indexer

    print("Initializing AI Teaching Assistant Web App...")

    # Initialize models based on provider configuration
    from llama_index.core import Settings

    # Check API keys
    siliconflow_api_key = CONFIG.model_config.api_key
    openai_like_api_key = CONFIG.model_config.openai_like_api_key

    if CONFIG.model_config.provider == "qwen3":
        # Use local Qwen3 model with Transformers
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from llama_index.llms.huggingface import HuggingFaceLLM
            from llama_index.embeddings.siliconflow import SiliconFlowEmbedding
            import torch
            import os

            model_path = CONFIG.model_config.qwen3_model_path
            print(f"🔄 Loading local Qwen3 model from: {model_path}")

            # Check if model files exist
            if not os.path.exists(model_path):
                print(f"❌ Error: Model not found at {model_path}")
                yield
                return

            # Determine device and dtype
            device_map = CONFIG.model_config.qwen3_device_map
            torch_dtype = CONFIG.model_config.qwen3_torch_dtype
            if torch_dtype == "float16":
                torch_dtype = torch.float16
            elif torch_dtype == "bfloat16":
                torch_dtype = torch.bfloat16
            else:
                torch_dtype = torch.float32

            # Auto-detect platform and configure device
            import platform
            if platform.system() == "Darwin":  # macOS
                if torch.backends.mps.is_available() and device_map == "auto":
                    device_map = "mps"
                    print("🍎 Using MPS (Metal Performance Shaders) for macOS")
                elif device_map == "auto":
                    device_map = "cpu"
                    print("🍎 Using CPU for macOS (MPS not available)")

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            print("✅ Qwen3 tokenizer loaded successfully!")

            # Load model - Qwen3VL requires special handling
            print("📝 Loading Qwen3VL model...")
            try:
                from transformers import Qwen3VLForConditionalGeneration, AutoConfig

                # Load the Qwen3VL model
                model = Qwen3VLForConditionalGeneration.from_pretrained(
                    model_path,
                    torch_dtype=torch_dtype,
                    device_map=device_map,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                    _attn_implementation="flash_attention_2" if device_map != "cpu" else "eager"
                )
                print("✅ Qwen3VL model loaded successfully!")

            except ImportError:
                print("⚠️ Qwen3VL not available in current transformers version")
                print("🔄 Attempting generic model loading...")
                try:
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        torch_dtype=torch_dtype,
                        device_map=device_map,
                        trust_remote_code=True,
                    )
                except Exception as e:
                    if "Unrecognized configuration class" in str(e):
                        print("❌ This model requires transformers >= 4.45.0 with Qwen3VL support")
                        print("💡 Please upgrade: pip install transformers>=4.45.0")
                        raise
                    else:
                        raise
            except Exception as e:
                print(f"❌ Failed to load Qwen3VL model: {e}")
                print("💡 Try upgrading transformers: pip install transformers>=4.45.0")
                raise

            # Create HuggingFace LLM wrapper
            Settings.llm = HuggingFaceLLM(
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=CONFIG.model_config.qwen3_max_new_tokens,
                generate_kwargs={"temperature": 0.7, "top_p": 0.9, "do_sample": True}
            )

            # Use SiliconFlow embedding for better performance if available
            if not siliconflow_api_key:
                print("WARNING: SILICONFLOW_API_KEY not set. Using fallback embedding model.")
                from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                Settings.embed_model = HuggingFaceEmbedding(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            else:
                Settings.embed_model = SiliconFlowEmbedding(
                    api_key=siliconflow_api_key,
                    model_name=CONFIG.model_config.embedding_model
                )

            print(f"✅ Initialized with local Qwen3 model:")
            print(f"  LLM: Local Qwen3 (Transformers)")
            print(f"  Embedding: {CONFIG.model_config.embedding_model if siliconflow_api_key else 'HuggingFace'}")
            print(f"  Device: {device_map}")
            print(f"  Dtype: {CONFIG.model_config.qwen3_torch_dtype}")

        except Exception as e:
            print(f"❌ Failed to load local Qwen3 model: {e}")
            print("⚠️ Falling back to SiliconFlow model...")

            # Fallback to SiliconFlow
            from llama_index.embeddings.siliconflow import SiliconFlowEmbedding
            from llama_index.llms.siliconflow import SiliconFlow

            if not siliconflow_api_key:
                print("WARNING: SILICONFLOW_API_KEY not set.")
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
            print(f"Fallback: Initialized with SiliconFlow model: {CONFIG.model_config.llm_model}")

    elif CONFIG.model_config.provider == "openai_like":
        # Use local Phi3.5 model with Transformers
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModelForSequenceClassification
            from llama_index.llms.huggingface import HuggingFaceLLM
            from llama_index.embeddings.siliconflow import SiliconFlowEmbedding
            import torch
            import os

            # Model paths
            model_path = "./model-phi3.5/cn_model"
            lora_path = "./model-phi3.5/phi3_bigdata_qlora_continued"

            print(f"🔄 Loading local Phi3.5 model from: {model_path}")

            # Check if model files exist
            if not os.path.exists(model_path):
                print(f"❌ Error: Model not found at {model_path}")
                yield
                return

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            print("✅ Tokenizer loaded successfully!")

            # Detect platform and configure model loading accordingly
            import platform

            if platform.system() == "Darwin":  # macOS
                # Use MPS (Metal Performance Shaders) for macOS
                if torch.backends.mps.is_available():
                    device_map = "mps"
                    print("🍎 Using MPS (Metal Performance Shaders) for macOS")
                else:
                    device_map = "cpu"
                    print("🍎 Using CPU for macOS (MPS not available)")

                model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map=device_map,
                    trust_remote_code=True,
                    # Don't use 4-bit quantization on macOS
                )
            else:
                # For other platforms (Linux/Windows with CUDA)
                model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    load_in_4bit=True  # Use 4-bit quantization to reduce memory usage
                )
            print("✅ Base model loaded successfully!")

            # Apply LoRA if available
            if os.path.exists(lora_path):
                print(f"📌 Applying LoRA from: {lora_path}")
                try:
                    from peft import PeftModel
                    model = PeftModel.from_pretrained(model, lora_path)
                    print("✅ LoRA applied successfully!")
                except ImportError:
                    print("⚠️ peft not installed. Install with: pip install peft")
                    print("⚠️ Continuing with base model only...")
                except Exception as e:
                    print(f"⚠️ Failed to apply LoRA: {e}")
                    print("⚠️ Continuing with base model only...")

            # Create HuggingFace LLM wrapper
            Settings.llm = HuggingFaceLLM(
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512
            )

            # Use SiliconFlow embedding for better performance
            if not siliconflow_api_key:
                print("WARNING: SILICONFLOW_API_KEY not set. Using fallback embedding model.")
                from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                Settings.embed_model = HuggingFaceEmbedding(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            else:
                Settings.embed_model = SiliconFlowEmbedding(
                    api_key=siliconflow_api_key,
                    model_name=CONFIG.model_config.embedding_model
                )

            print(f"✅ Initialized with local Phi3.5 model:")
            print(f"  LLM: Local Phi3.5 (Transformers)")
            print(f"  Embedding: {CONFIG.model_config.embedding_model if siliconflow_api_key else 'HuggingFace'}")

        except Exception as e:
            print(f"❌ Failed to load local Phi3.5 model: {e}")
            print("⚠️ Falling back to SiliconFlow model...")

            # Fallback to SiliconFlow
            from llama_index.embeddings.siliconflow import SiliconFlowEmbedding
            from llama_index.llms.siliconflow import SiliconFlow

            if not siliconflow_api_key:
                print("WARNING: SILICONFLOW_API_KEY not set.")
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
            print(f"Fallback: Initialized with SiliconFlow model: {CONFIG.model_config.llm_model}")
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

    # Initialize auto indexer
    auto_indexer = AutoIndexer()
    auto_indexer.set_rag_components(index_manager, query_engine)

    # Run automatic file scanning and processing
    print("Running automatic file scanning and processing...")
    try:
        auto_index_result = auto_indexer.scan_and_process()
        scan_result = auto_index_result['scan_result']
        process_result = auto_index_result['process_result']

        print(f"📂 File scan completed:")
        print(f"  New files: {len(scan_result['new_files'])}")
        print(f"  Modified files: {len(scan_result['modified_files'])}")
        print(f"  Existing files: {len(scan_result['existing_files'])}")

        if process_result['processed_count'] > 0:
            print(f"  ✅ Processed {process_result['processed_count']} new files successfully")
            if process_result['processed_files']:
                print(f"     Files: {', '.join(process_result['processed_files'][:3])}{'...' if len(process_result['processed_files']) > 3 else ''}")

        if 'failed_count' in process_result and process_result['failed_count'] > 0:
            print(f"  ❌ Failed to process {process_result['failed_count']} files")
            if process_result['failed_files']:
                print(f"     Files: {', '.join(process_result['failed_files'][:3])}{'...' if len(process_result['failed_files']) > 3 else ''}")

        if process_result['processed_count'] == 0 and process_result['failed_count'] == 0:
            print(f"  ℹ️ No new files to process")

    except Exception as e:
        print(f"⚠️ Auto indexing failed: {e}")
        print("Continuing with startup...")

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
    return {
        "status": "healthy",
        "message": "AI Teaching Assistant is running",
        "model_provider": CONFIG.model_config.provider
    }


@app.get("/api/rag/model_info")
async def get_model_info():
    """Get current model information."""
    model_info = {
        "provider": CONFIG.model_config.provider,
        "model_name": None,
        "model_type": None,
        "device": None,
        "embedding_model": None
    }

    try:
        if CONFIG.model_config.provider == "qwen3":
            model_info.update({
                "model_name": "Qwen3-VL-4B-Thinking",
                "model_type": "Local Vision-Language Model",
                "model_path": CONFIG.model_config.qwen3_model_path,
                "device_map": CONFIG.model_config.qwen3_device_map,
                "dtype": CONFIG.model_config.qwen3_torch_dtype,
                "max_tokens": CONFIG.model_config.qwen3_max_new_tokens
            })
        elif CONFIG.model_config.provider == "openai_like":
            model_info.update({
                "model_name": CONFIG.model_config.openai_like_model,
                "model_type": "Local Text Model (Phi3.5)",
                "device": "Local",
                "api_base": CONFIG.model_config.openai_like_api_base
            })
        else:  # siliconflow
            model_info.update({
                "model_name": CONFIG.model_config.llm_model,
                "model_type": "Cloud Model",
                "api_base": CONFIG.model_config.api_base_url
            })

        # Get embedding model info
        if os.getenv("SILICONFLOW_API_KEY"):
            model_info["embedding_model"] = CONFIG.model_config.embedding_model
        else:
            model_info["embedding_model"] = "HuggingFace Embedding"

        return model_info
    except Exception as e:
        return {
            "error": f"Failed to get model info: {str(e)}",
            "provider": CONFIG.model_config.provider
        }


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