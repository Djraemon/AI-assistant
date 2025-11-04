"""Simple test to verify the query engine streaming functionality"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_engine import TeachingQueryEngine
from config import CONFIG

# Mock a minimal query engine for testing the streaming function
class MockIndex:
    def as_query_engine(self, *args, **kwargs):
        class MockQueryEngine:
            def query(self, query_str):
                class MockResult:
                    def __init__(self):
                        self.response = "这是一个关于卷积神经网络的详细解释。卷积神经网络是一种深度学习模型..."
                        self.source_nodes = []
                return MockResult()
        return MockQueryEngine()

def test_streaming_function():
    """Test the streaming function without initializing the full system"""
    print("Testing the streaming function implementation...")
    
    # Create a mock query engine to test the streaming method
    mock_index = MockIndex()
    query_engine = TeachingQueryEngine(mock_index, CONFIG, composite_index=None)
    
    # Add mock source indexes for testing
    query_engine.source_indexes = {
        "course_materials": MockIndex(),
        "practice": MockIndex(),
        "textbook": MockIndex()
    }
    
    print("Streaming function exists:", hasattr(query_engine, 'query_stream'))
    print("Query stream method is async:", asyncio.iscoroutinefunction(query_engine.query_stream))

if __name__ == "__main__":
    import asyncio
    test_streaming_function()