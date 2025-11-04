"""Utility functions for the AI Teaching Assistant."""

import os
from pathlib import Path
from typing import List, Dict, Any
import json


def ensure_data_directories(config):
    """Ensure all required data directories exist."""
    directories = [
        config.data_config.ppt_dir,
        config.data_config.practice_dir,
        config.data_config.textbook_dir,
        config.data_config.index_dir
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")


def get_supported_files(config, directory: str) -> List[str]:
    """Get list of supported files in a directory."""
    if not os.path.exists(directory):
        return []
    
    supported_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in config.data_config.supported_extensions):
                supported_files.append(os.path.join(root, file))
    
    return supported_files


def create_practice_file(config, filename: str = "sample_practice.json"):
    """Create a sample practice file to demonstrate the practice question format."""
    practice_dir = config.data_config.practice_dir
    os.makedirs(practice_dir, exist_ok=True)
    
    sample_practice = {
        "questions": [
            {
                "id": 1,
                "question": "什么是大数据的4V特征？",
                "answer": "大数据的4V特征包括：Volume（大量）、Velocity（高速）、Variety（多样）、Veracity（真实性）。",
                "difficulty": "basic",
                "category": "big_data_fundamentals"
            },
            {
                "id": 2,
                "question": "如何处理非结构化数据？",
                "answer": "处理非结构化数据的方法包括：文本分析、自然语言处理、图像识别、音频分析等。",
                "difficulty": "intermediate",
                "category": "data_processing"
            }
        ]
    }
    
    filepath = os.path.join(practice_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(sample_practice, f, ensure_ascii=False, indent=2)
    
    print(f"Created sample practice file: {filepath}")


def create_textbook_placeholder(config, filename: str = "textbook_outline.txt"):
    """Create a placeholder for textbook content."""
    textbook_dir = config.data_config.textbook_dir
    os.makedirs(textbook_dir, exist_ok=True)
    
    content = """大数据分析教材大纲

第一章：大数据概述
- 定义与特征
- 发展历程
- 应用领域

第二章：大数据技术架构
- 分布式存储
- 分布式计算
- 数据处理框架

第三章：数据分析方法
- 数据挖掘
- 机器学习
- 统计分析

第四章：大数据应用实践
- 行业案例
- 实施策略
- 挑战与对策
"""
    
    filepath = os.path.join(textbook_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created textbook placeholder: {filepath}")


def print_system_info(config):
    """Print system configuration and data info."""
    print("="*60)
    print("AI Teaching Assistant - System Information")
    print("="*60)
    print(f"LLM Model: {config.model_config.llm_model}")
    print(f"Embedding Model: {config.model_config.embedding_model}")
    print(f"Data Directory: {config.data_config.base_data_dir}")
    print(f"Storage Directory: {config.data_config.index_dir}")
    print(f"Supported Extensions: {config.data_config.supported_extensions}")
    print("="*60)


def validate_config(config) -> List[str]:
    """Validate configuration and return a list of issues."""
    issues = []
    
    # Check if API key is set
    if not config.model_config.api_key or "your-api-key" in config.model_config.api_key:
        issues.append("API key is not set properly")
    
    # Check if base data directory exists
    if not os.path.exists(config.data_config.base_data_dir):
        issues.append(f"Base data directory does not exist: {config.data_config.base_data_dir}")
    
    return issues