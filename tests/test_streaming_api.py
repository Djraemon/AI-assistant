import asyncio
import json
import requests
from datetime import datetime

def test_streaming_api():
    """Test the streaming API endpoint to ensure it follows the specification."""
    url = "http://localhost:8000/api/rag/chat/stream"
    
    payload = {
        "user_id": "s1",
        "question": "请解释一下什么是卷积神经网络?",
        "session_id": "sess_abc123",
        "stream": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing streaming API endpoint...")
    print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\nStreaming response content:")
            for line in response.iter_lines(decode_unicode=True):
                if line.strip():  # Skip empty lines
                    print(f"Line: {line}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_streaming_api()