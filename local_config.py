
# 本地模型配置文件
# 使用phi-3.5-mini + HuggingFace embedding

import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LocalModelConfig:
    """本地模型配置"""
    # LLM配置
    llm_provider: str = "openai_like"
    llm_model: str = "phi-3.5-mini"
    llm_api_base: str = "http://llm.lbzfrombit.icu:8000/v1"
    llm_api_key: str = "dummy"
    is_chat_model: bool = True

    # Embedding配置
    embedding_provider: str = "huggingface"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"  # 或 "cuda" 如果有GPU

# 创建本地配置实例
LOCAL_CONFIG = LocalModelConfig()

print("本地模型配置:")
print(f"  LLM模型: {LOCAL_CONFIG.llm_model}")
print(f"  LLM API: {LOCAL_CONFIG.llm_api_base}")
print(f"  Embedding: {LOCAL_CONFIG.embedding_model}")
print(f"  设备: {LOCAL_CONFIG.embedding_device}")
