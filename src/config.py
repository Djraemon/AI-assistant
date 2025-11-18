"""Configuration file for the AI Teaching Assistant RAG system."""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ModelConfig:
    """Configuration for LLM and embedding models"""
    # Model provider selection: "siliconflow", "openai_like", or "qwen3"
    provider: str = "siliconflow"

    # SiliconFlow configuration (existing)
    api_key: str = os.getenv("SILICONFLOW_API_KEY", "")
    api_base_url: str = os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1/")
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    embedding_model: str = "netease-youdao/bce-embedding-base_v1"

    # OpenAI-like configuration (phi-3.5-mini)
    openai_like_api_key: str = os.getenv("OPENAI_LIKE_API_KEY", "")
    openai_like_api_base: str = os.getenv("OPENAI_LIKE_API_BASE", "http://localhost:8000/v1")
    openai_like_model: str = "phi-3.5-mini"
    openai_like_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    is_chat_model: bool = True

    # Qwen3 model configuration
    qwen3_model_path: str = "./model-qwen3/Qwen3_vl_thinking"
    qwen3_device_map: str = "auto"  # "auto", "cpu", "mps", "cuda"
    qwen3_torch_dtype: str = "bfloat16"  # "float16", "bfloat16", "float32"
    qwen3_max_new_tokens: int = 1024
    qwen3_use_lora: bool = False


@dataclass
class DataConfig:
    """Configuration for data sources"""
    base_data_dir: str = "./data"
    ppt_dir: str = "./data/ppt"
    practice_dir: str = "./data/practice"
    textbook_dir: str = "./data/textbook"  # Will be created when textbooks are added
    index_dir: str = "./storage"
    
    # Supported file extensions
    supported_extensions: List[str] = None
    
    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = ['.pdf', '.docx', '.pptx', '.txt', '.md', '.csv', '.json']


@dataclass
class RAGConfig:
    """Main RAG system configuration"""
    model_config: ModelConfig = None
    data_config: DataConfig = None
    
    # Query settings
    similarity_top_k: int = 5
    rerank_top_n: int = 3
    
    # Storage settings
    persist_dir: str = "./storage"
    
    # System behavior
    enable_reranking: bool = True
    enable_query_expansion: bool = True
    
    def __post_init__(self):
        if self.model_config is None:
            self.model_config = ModelConfig()
        if self.data_config is None:
            self.data_config = DataConfig()


# Global configuration instance
CONFIG = RAGConfig()