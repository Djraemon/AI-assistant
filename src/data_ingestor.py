"""Data ingestion pipeline for the AI Teaching Assistant."""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.node_parser import SentenceSplitter


class DataIngestor:
    """Handles ingestion of different data types for the RAG system."""
    
    def __init__(self, config):
        self.config = config
        self.supported_extensions = config.data_config.supported_extensions
    
    def ingest_ppt_data(self) -> List[Document]:
        """Ingest PPT/PDF course materials."""
        if not os.path.exists(self.config.data_config.ppt_dir):
            print(f"PPT directory {self.config.data_config.ppt_dir} does not exist. Skipping PPT ingestion.")
            return []
        
        reader = SimpleDirectoryReader(
            input_dir=self.config.data_config.ppt_dir,
            required_exts=self.supported_extensions,
            recursive=True
        )
        documents = reader.load_data()
        
        # Add metadata to identify source type
        for doc in documents:
            doc.metadata["source_type"] = "course_material"
            doc.metadata["source_dir"] = "ppt"
        
        print(f"Ingested {len(documents)} documents from PPT directory.")
        return documents
    
    def ingest_practice_data(self) -> List[Document]:
        """Ingest practice exercises and questions."""
        if not os.path.exists(self.config.data_config.practice_dir):
            print(f"Practice directory {self.config.data_config.practice_dir} does not exist. Skipping practice ingestion.")
            return []
        
        reader = SimpleDirectoryReader(
            input_dir=self.config.data_config.practice_dir,
            required_exts=self.supported_extensions,
            recursive=True
        )
        documents = reader.load_data()
        
        # Add metadata to identify source type
        for doc in documents:
            doc.metadata["source_type"] = "practice"
            doc.metadata["source_dir"] = "practice"
        
        print(f"Ingested {len(documents)} documents from practice directory.")
        return documents
    
    def ingest_textbook_data(self) -> List[Document]:
        """Ingest textbook content."""
        if not os.path.exists(self.config.data_config.textbook_dir):
            print(f"Textbook directory {self.config.data_config.textbook_dir} does not exist. Skipping textbook ingestion.")
            return []
        
        reader = SimpleDirectoryReader(
            input_dir=self.config.data_config.textbook_dir,
            required_exts=self.supported_extensions,
            recursive=True
        )
        documents = reader.load_data()
        
        # Add metadata to identify source type
        for doc in documents:
            doc.metadata["source_type"] = "textbook"
            doc.metadata["source_dir"] = "textbook"
        
        print(f"Ingested {len(documents)} documents from textbook directory.")
        return documents
    
    def ingest_all_data(self) -> List[Document]:
        """Ingest data from all available sources."""
        all_documents = []
        
        # Ingest from all available directories
        all_documents.extend(self.ingest_ppt_data())
        all_documents.extend(self.ingest_practice_data())
        all_documents.extend(self.ingest_textbook_data())
        
        if not all_documents:
            print("No documents found in any data directory.")
            return []
        
        # Apply consistent chunking
        chunk_size = 1024
        chunk_overlap = 200
        node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        nodes = node_parser.get_nodes_from_documents(all_documents)
        print(f"Created {len(nodes)} nodes from all documents.")
        
        return nodes


def get_data_stats(nodes) -> Dict[str, Any]:
    """Get statistics about ingested data."""
    # Convert nodes to documents if necessary
    if nodes and hasattr(nodes[0], 'text'):
        documents = nodes
    else:
        documents = nodes  # assume it's already documents
    
    stats = {
        "total_docs": len(documents),
        "total_chars": sum(len(doc.text) for doc in documents),
        "by_source_type": {},
        "by_dir": {}
    }
    
    for doc in documents:
        source_type = doc.metadata.get("source_type", "unknown")
        source_dir = doc.metadata.get("source_dir", "unknown")
        
        stats["by_source_type"][source_type] = stats["by_source_type"].get(source_type, 0) + 1
        stats["by_dir"][source_dir] = stats["by_dir"].get(source_dir, 0) + 1
    
    return stats