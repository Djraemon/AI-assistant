#!/bin/bash

# AI Teaching Assistant - Model Switching Utility
# AI助教RAG系统 - 模型切换工具

echo "🎓 AI Teaching Assistant - Model Switching Utility"
echo "🎓 AI助教RAG系统 - 模型切换工具"
echo ""

# Current model status
echo "📊 Current Model Status:"
echo "======================="

# Check if server is running
if lsof -ti:8001 >/dev/null 2>&1; then
    echo "✅ Server is running on port 8001"

    # Get current model info
    if command -v curl >/dev/null 2>&1; then
        echo ""
        echo "🔍 Current model info:"
        curl -s http://localhost:8001/api/rag/model_info | python3 -m json.tool 2>/dev/null || echo "Failed to get model info"
    else
        echo "⚠️ curl not available, cannot fetch model info"
    fi
else
    echo "❌ Server is not running"
fi

echo ""
echo "🔄 Available Models:"
echo "===================="
echo "1️⃣ qwen3        - Local Qwen3-VL Model (Vision-Language)"
echo "2️⃣ openai_like  - Local Phi3.5 Model (Text-only)"
echo "3️⃣ siliconflow  - Cloud SiliconFlow Model (Default)"
echo ""

# Ask user to select model
read -p "🤔 Select model (1/2/3) or press Enter for SiliconFlow: " choice

case $choice in
    1)
        SELECTED_MODEL="qwen3"
        echo "🤖 Selected: Qwen3 Local Model"
        ;;
    2)
        SELECTED_MODEL="openai_like"
        echo "🧠 Selected: Phi3.5 Local Model"
        ;;
    3|"")
        SELECTED_MODEL="siliconflow"
        echo "☁️ Selected: SiliconFlow Cloud Model"
        ;;
    *)
        echo "❌ Invalid choice. Using SiliconFlow."
        SELECTED_MODEL="siliconflow"
        ;;
esac

echo ""
echo "🚀 Restarting server with $SELECTED_MODEL model..."
echo "💻 Command: ./start_server.sh $SELECTED_MODEL"

# Stop existing server
echo "🔄 Stopping existing server..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 2

# Start new server
./start_server.sh $SELECTED_MODEL