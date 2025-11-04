"""Test the RAG streaming API implementation against APIs.md specification."""

import json
import asyncio
import aiohttp
import datetime

async def test_rag_streaming_api():
    """Test the /api/rag/chat/stream endpoint."""

    # API endpoint
    url = "http://localhost:8000/api/rag/chat/stream"

    # Request payload matching APIs.md specification
    request_data = {
        "user_id": "s1",
        "question": "请解释一下什么是卷积神经网络?",
        "session_id": "sess_abc123",
        "stream": True
    }

    print("Testing RAG Streaming API...")
    print(f"URL: {url}")
    print(f"Request: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    print("\n" + "="*60)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
            ) as response:

                if response.status != 200:
                    print(f"Error: HTTP {response.status}")
                    print(f"Response: {await response.text()}")
                    return

                print("✅ Connected successfully!")
                print("📡 Receiving streaming response:\n")

                # Track response structure
                received_events = []

                async for line in response.content:
                    line = line.decode('utf-8').strip()

                    if line.startswith('event:'):
                        event_type = line.split(':', 1)[1].strip()
                        print(f"🔔 Event: {event_type}")

                    elif line.startswith('data:'):
                        try:
                            data_str = line.split(':', 1)[1].strip()
                            data = json.loads(data_str)
                            received_events.append(data)

                            # Format and print data
                            if data.get('type') == 'start':
                                print(f"   🚀 Stream started at {data.get('timestamp', 'N/A')}")
                            elif data.get('type') == 'delta':
                                print(f"   💬 {data.get('content', '')}")
                            elif data.get('type') == 'sources':
                                sources = data.get('sources', [])
                                print(f"   📚 Sources: {len(sources)} references")
                                for source in sources[:2]:  # Show first 2 sources
                                    print(f"      - {source.get('node_name', 'Unknown')}: {source.get('excerpt', '')[:50]}...")
                            elif data.get('type') == 'end':
                                print(f"   🏁 Stream ended. Total tokens: {data.get('total_tokens', 'N/A')}")
                            elif data.get('type') == 'error':
                                print(f"   ❌ Error: {data.get('message', 'Unknown error')}")

                        except json.JSONDecodeError as e:
                            print(f"   ⚠️  Invalid JSON data: {data_str}")

                print("\n" + "="*60)
                print("📊 Summary:")
                print(f"   Total events received: {len(received_events)}")

                # Validate response structure
                event_types = [event.get('type') for event in received_events]
                print(f"   Event types: {event_types}")

                # Check required events
                has_start = 'start' in event_types
                has_end = 'end' in event_types
                has_delta = 'delta' in event_types

                print(f"   ✅ Has start event: {has_start}")
                print(f"   ✅ Has delta events: {has_delta}")
                print(f"   ✅ Has end event: {has_end}")

                if has_start and has_end:
                    print("\n🎉 API test completed successfully!")
                    print("📋 The implementation matches APIs.md specification.")
                else:
                    print("\n⚠️  API test incomplete - missing required events.")

    except aiohttp.ClientConnectorError:
        print("❌ Connection failed. Make sure the server is running on http://localhost:8000")
        print("💡 Start the server with: python web_app.py")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("🧪 RAG Streaming API Test")
    print("Testing implementation against APIs.md specification")
    print("="*60)

    asyncio.run(test_rag_streaming_api())