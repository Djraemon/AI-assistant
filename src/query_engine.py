"""Query engine for the AI Teaching Assistant with multi-source integration and intent classification."""

from typing import Optional, Dict, Any, List, Generator
import re
import json
import asyncio
from llama_index.core import VectorStoreIndex, QueryBundle, Document
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.schema import NodeWithScore
from llama_index.core.base.llms.base import ChatMessage
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from prompt.prompt_template import (
    text_qa_template,
    refine_template,
)
class TeachingQueryEngine:
    """Enhanced query engine with intent classification for educational use cases."""
    
    def __init__(self, index, config, composite_index=None):
        self.index = index
        self.config = config
        self.composite_index = composite_index
        self.query_engine = None
        self.source_indexes = None
        self.all_aource_indexeds = None
        
        if composite_index:
            self.source_indexes = composite_index["indexes"]
        else:
            # 初始化单个索引的查询引擎
            self._initialize_query_engine()
    
    def _initialize_query_engine(self):
        """Initialize the basic query engine with appropriate settings."""
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=self.config.similarity_top_k,
            # Add postprocessors if needed
            node_postprocessors=[
                SimilarityPostprocessor(similarity_cutoff=0.5)
            ] if self.config.enable_reranking else [],
            text_qa_template=text_qa_template,
            refine_template=refine_template,
        )
    

    def query(self, query_str: str, source_filter: Optional[List[str]] = None):
        """Execute a query with intent classification.
        Args:
            query_str: The query string
            source_filter: Optional list of source types to filter (for composite queries)
        """
        return self._query_with_intent_classification(query_str, source_filter)
    
    
    def _classify_intent(self, query_str: str) -> str:
        """Classify user query intent using LLM model into two categories: comprehensive or simple."""
        from prompt.prompt_template import query_intent_prompt
        intent_prompt = query_intent_prompt.format(query_str=query_str)
        try:
            # 使用当前配置的LLM进行意图识别
            llm = Settings.llm
            response = llm.complete(intent_prompt)
            intent = str(response).strip().lower()

            # 验证返回的意图是否有效
            if intent in ["comprehensive", "simple"]:
                return intent
            else:
                # 如果模型返回无效结果，使用关键词匹配作为后备方案
                return self._fallback_keyword_classification(query_str)

        except Exception as e:
            print(f"LLM意图识别失败，使用关键词匹配作为后备方案: {e}")
            return self._fallback_keyword_classification(query_str)

    def _fallback_keyword_classification(self, query_str: str) -> str:
        """Fallback keyword-based classification when LLM fails."""
        query_lower = query_str.lower()
        source_keywords = [
            '来源', '出自', '根据什么', '参考资料', '哪个资料', '哪里提到', '哪里说的',
            '根据哪个', '基于什么', '哪个文档', '哪本书', '哪个文件', '原文', '出处'
        ]
        source_matches = sum(1 for keyword in source_keywords if keyword in query_lower)
        return "comprehensive" if source_matches > 0 else "simple"
    
    def _query_with_intent_classification(self, query_str: str, source_filter: Optional[List[str]] = None):
        """Execute a query across multiple data sources with intent classification."""
        # 首先进行意图识别
        intent = self._classify_intent(query_str)
        
        if source_filter is None:
            # Query all available sources
            source_filter = list(self.source_indexes.keys())
        
        # 根据意图选择合适的提示模板
        template = text_qa_template
        
        if intent == "comprehensive":
            # "comprehensive"模式下，每种索引分别生成回答，再整合。
            results = {}
            for source_type in source_filter:
                if source_type in self.source_indexes:
                    engine = self.source_indexes[source_type].as_query_engine(
                        similarity_top_k=self.config.similarity_top_k,
                        text_qa_template=template 
                    )
                    try:
                        result = engine.query(query_str)
                        results[source_type] = result
                    except Exception as e:
                        print(f"Error querying {source_type}: {e}")
                        results[source_type] = f"Error retrieving information from {source_type}"
            response = self._combine_results(results, query_str, intent)
        else: 
            # "simple"模式下，使用QueryFusionRetriever从所有源中统一检索
            from llama_index.core.retrievers import QueryFusionRetriever
            
            # 创建所有源的检索器列表
            retrievers = []
            for source_type in source_filter:
                if source_type in self.source_indexes:
                    retriever = self.source_indexes[source_type].as_retriever(
                        similarity_top_k=self.config.similarity_top_k
                    )
                    retrievers.append(retriever)
            
            # 使用QueryFusionRetriever合并所有检索器
            fusion_retriever = QueryFusionRetriever(
                retrievers,
                similarity_top_k=self.config.similarity_top_k,
                use_async=False,
                # 使用简单的top-k组合策略
            )
            
            # 创建查询引擎，使用标准模板
            fused_query_engine = RetrieverQueryEngine.from_args(
                fusion_retriever,
                text_qa_template=template
            )
            
            # 执行查询并返回结果
            result = fused_query_engine.query(query_str)
            response = str(result)
            
        return response

    async def query_stream(self, query_str: str, source_filter: Optional[List[str]] = None):
        """Stream query response with intent classification.
        Args:
            query_str: The query string
            source_filter: Optional list of source types to filter (for composite queries)
        Yields:
            dict: Response chunks with type and content
        """
        # First classify intent
        intent = self._classify_intent(query_str)
        
        if source_filter is None:
            # Query all available sources
            source_filter = list(self.source_indexes.keys()) if self.source_indexes else []
        
        # For streaming, we'll use the same logic as regular query but with streaming response
        template = text_qa_template
        
        if intent == "comprehensive":
            # For comprehensive intent, stream results from different sources
            results = {}
            for source_type in source_filter:
                if source_type in self.source_indexes:
                    engine = self.source_indexes[source_type].as_query_engine(
                        similarity_top_k=self.config.similarity_top_k,
                        text_qa_template=template 
                    )
                    try:
                        # Attempt to stream from the engine
                        result = engine.query(query_str)
                        results[source_type] = result
                    except Exception as e:
                        print(f"Error querying {source_type}: {e}")
                        results[source_type] = f"Error retrieving information from {source_type}"
            
            # Stream the combined response
            response = self._combine_results(results, query_str, intent)
            # Stream response in chunks
            chunk_size = 20  # Number of characters per chunk
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                yield {"type": "delta", "content": chunk}
            
            # Provide sources information after content
            sources_info = []
            for source_type, result in results.items():
                if hasattr(result, 'source_nodes') and result.source_nodes:
                    for node in result.source_nodes:
                        sources_info.append({
                            "node_id": getattr(node, "node_id", "unknown"),
                            "node_name": getattr(node, "metadata", {}).get("file_name", "Unknown"),
                            "excerpt": getattr(node, "text", "")[:100]  # First 100 chars as excerpt
                        })
                else:
                    sources_info.append({
                        "node_id": f"{source_type}_unknown",
                        "node_name": source_type,
                        "excerpt": str(result)[:100]
                    })
            
            yield {"type": "sources", "sources": sources_info}
        else: 
            # For simple intent, use fused query engine with streaming
            from llama_index.core.retrievers import QueryFusionRetriever
            
            # Create a list of retrievers from all sources
            retrievers = []
            for source_type in source_filter:
                if source_type in self.source_indexes:
                    retriever = self.source_indexes[source_type].as_retriever(
                        similarity_top_k=self.config.similarity_top_k
                    )
                    retrievers.append(retriever)
            
            # Use QueryFusionRetriever to combine all retrievers
            if retrievers:
                fusion_retriever = QueryFusionRetriever(
                    retrievers,
                    similarity_top_k=self.config.similarity_top_k,
                    use_async=False,
                )
                
                # Create query engine with streaming capability
                fused_query_engine = RetrieverQueryEngine.from_args(
                    fusion_retriever,
                    text_qa_template=template
                )
                
                # Get result
                result = fused_query_engine.query(query_str)
                
                # Stream response in chunks
                response = str(result)
                chunk_size = 20  # Number of characters per chunk
                for i in range(0, len(response), chunk_size):
                    chunk = response[i:i + chunk_size]
                    yield {"type": "delta", "content": chunk}
                
                # Provide sources information after content
                sources_info = []
                if hasattr(result, 'source_nodes') and result.source_nodes:
                    for node in result.source_nodes:
                        sources_info.append({
                            "node_id": getattr(node, "node_id", "unknown"),
                            "node_name": getattr(node, "metadata", {}).get("file_name", "Unknown"),
                            "excerpt": getattr(node, "text", "")[:100]  # First 100 chars as excerpt
                        })
                
                yield {"type": "sources", "sources": sources_info}
            else:
                # If no retrievers available, return an error
                yield {"type": "delta", "content": "No data sources available for query."}

    def _combine_results(self, results: Dict[str, Any], original_query: str, intent: str = "simple") -> str:
        """Combine results from multiple sources into a coherent response based on intent."""
        if intent == "comprehensive":
            # 用户要求表明数据来源，所以明确展示各个来源的信息
            combined_text = f"关于您的问题：'{original_query}'，以下是来自不同资料的信息：\n\n"
            
            for source_type, result in results.items():
                if hasattr(result, 'response'):
                    content = result.response
                else:
                    content = str(result)
                
                source_name_map = {
                    "course_materials": "课程资料",
                    "practice": "练习题库", 
                    "textbook": "教材内容"
                }
                source_name = source_name_map.get(source_type, source_type)
                
                combined_text += f"【{source_name}】:\n{content}\n\n"
            
            combined_text += "以上是来自不同来源的信息整合。"
        else:  # simple
            # 简单模式，整合所有信息而不特别强调来源
            combined_text = ""
            for source_type, result in results.items():
                if hasattr(result, 'response'):
                    content = result.response
                else:
                    content = str(result)
                combined_text += f"{content}\n\n"
        
        return combined_text