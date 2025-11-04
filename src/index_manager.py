"""Index management system for the AI Teaching Assistant."""

import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Document,
    Settings
)
from llama_index.core.indices.composability import ComposableGraph
from llama_index.core.schema import IndexNode

'''
IndexManager中构建了四种索引：
   1. course_materials_index（课程材料索引） - 从标记为"course_material"的节点创建，这些通常来自PPT等课程材料
   2. practice_index（练习索引） - 从标记为"practice"的节点创建，这些来自练习题数据
   3. textbook_index（教科书索引） - 从标记为"textbook"的节点创建，这些来自教科书内容
   4. main_index（主索引） - 从索引节点创建，用于整合所有其他索引
'''
class IndexManager:
    """Manages multiple indexes for different data sources."""
    
    def __init__(self, config):
        self.config = config
        self.index_dir = self.config.data_config.index_dir
        self.persist_dir = self.config.persist_dir
        
        # Ensure directories exist
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.persist_dir, exist_ok=True)
    
    def create_index_from_nodes(self, nodes, index_name: str):
        """Create an index from nodes and store it."""
        index = VectorStoreIndex(nodes=nodes)
        index_path = os.path.join(self.index_dir, f"{index_name}_index")
        
        # Persist the index
        index.storage_context.persist(persist_dir=index_path)
        print(f"Saved index for {index_name} at {index_path}")
        return index
    
    def load_index(self, index_name: str):
        """Load an existing index."""
        index_path = os.path.join(self.index_dir, f"{index_name}_index")
        if os.path.exists(index_path):
            storage_context = StorageContext.from_defaults(persist_dir=index_path)
            index = load_index_from_storage(storage_context)
            print(f"Loaded index for {index_name}")
            return index
        else:
            print(f"Index for {index_name} not found at {index_path}")
            return None
    
    def create_or_load_composite_index(self, all_nodes: List[Document]):
        """Create a composite index that can handle multiple data sources."""
        composite_index_path = os.path.join(self.persist_dir, "composite_index.pkl")
        
        # Check if composite index exists
        if os.path.exists(composite_index_path):
            print("Loading existing composite index...")
            try:
                with open(composite_index_path, 'rb') as f:
                    composite_index = pickle.load(f)
                return composite_index
            except Exception as e:
                print(f"Error loading composite index: {e}. Recreating...")
        
        print("Creating new composite index...")
        
        if not all_nodes:
            print("No nodes provided to create an index.")
            return None
        
        # Create separate indexes for different source types
        course_materials_nodes = [node for node in all_nodes 
                                  if node.metadata.get("source_type") == "course_material"]
        practice_nodes = [node for node in all_nodes 
                          if node.metadata.get("source_type") == "practice"]
        textbook_nodes = [node for node in all_nodes 
                          if node.metadata.get("source_type") == "textbook"]
        
        indexes = {}
        index_nodes = []
        
        # Create index for course materials if available
        if course_materials_nodes:
            print(f"Creating index for {len(course_materials_nodes)} course materials...")
            try:
                course_index = VectorStoreIndex(course_materials_nodes)
                course_index_path = os.path.join(self.index_dir, "course_materials_index")
                course_index.storage_context.persist(persist_dir=course_index_path)
                indexes["course_materials"] = course_index
                index_nodes.append(
                    IndexNode(text="Course Materials", index_id="course_materials")
                )
            except Exception as e:
                print(f"Error creating course materials index: {e}")
        
        # Create index for practice materials if available
        if practice_nodes:
            print(f"Creating index for {len(practice_nodes)} practice materials...")
            try:
                practice_index = VectorStoreIndex(practice_nodes)
                practice_index_path = os.path.join(self.index_dir, "practice_index")
                practice_index.storage_context.persist(persist_dir=practice_index_path)
                indexes["practice"] = practice_index
                index_nodes.append(
                    IndexNode(text="Practice Exercises", index_id="practice")
                )
            except Exception as e:
                print(f"Error creating practice index: {e}")
        
        # Create index for textbooks if available
        if textbook_nodes:
            print(f"Creating index for {len(textbook_nodes)} textbook materials...")
            try:
                textbook_index = VectorStoreIndex(textbook_nodes)
                textbook_index_path = os.path.join(self.index_dir, "textbook_index")
                textbook_index.storage_context.persist(persist_dir=textbook_index_path)
                indexes["textbook"] = textbook_index
                index_nodes.append(
                    IndexNode(text="Textbook Content", index_id="textbook")
                )
            except Exception as e:
                print(f"Error creating textbook index: {e}")
        
        # Create a main index over the index nodes
        if index_nodes:
            print(f"Creating main index with {len(index_nodes)} index nodes...")
            try:
                main_index = VectorStoreIndex(index_nodes)
                main_index_path = os.path.join(self.index_dir, "main_index")
                main_index.storage_context.persist(persist_dir=main_index_path)
                
                # Save composite structure
                composite_index = {
                    "main_index": main_index,
                    "indexes": indexes,
                    "index_nodes": index_nodes
                }
                
                with open(composite_index_path, 'wb') as f:
                    pickle.dump(composite_index, f)
                
                return composite_index
            except Exception as e:
                print(f"Error creating main index: {e}")
                # Return partial composite index if possible
                if indexes:
                    return {
                        "main_index": None,
                        "indexes": indexes,
                        "index_nodes": []
                    }
        else:
            print("No nodes available to create an index.")
            return None
    
    def create_simple_index(self, documents: List[Document], force_recreate: bool = False):
        """Create a simple unified index from all documents."""
        index_path = os.path.join(self.persist_dir)
        
        if os.path.exists(index_path) and not force_recreate:
            # Load existing index
            storage_context = StorageContext.from_defaults(persist_dir=index_path)
            index = load_index_from_storage(storage_context)
            print("Loaded existing unified index.")
            return index
        else:
            # Create new index
            if documents:
                index = VectorStoreIndex.from_documents(documents)
                index.storage_context.persist(persist_dir=index_path)
                print("Created new unified index and persisted to storage.")
                return index
            else:
                print("No documents provided to create index.")
                return None