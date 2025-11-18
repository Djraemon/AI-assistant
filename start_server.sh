#!/bin/bash

# AI Teaching Assistant RAG System - Server Startup Script
# AI助教RAG系统 - 服务器启动脚本

echo "🎓 Starting AI Teaching Assistant RAG System..."
echo "🎓 启动AI助教RAG系统..."

# Check for model provider argument
MODEL_PROVIDER=${1:-siliconflow}
case $MODEL_PROVIDER in
    "qwen3")
        echo "🤖 Using Qwen3 Local Model"
        ;;
    "openai_like")
        echo "🧠 Using OpenAI-like Local Model (Phi3.5)"
        ;;
    "siliconflow"|*)
        echo "☁️ Using SiliconFlow Cloud Model"
        ;;
esac

# Set environment variables
export SILICONFLOW_API_KEY=sk-yrmmgcztvxoijeigwmhqqohhafaolagrmlffjuhiifmrdlcg
export OPENAI_LIKE_API_KEY=dummy
export RAG_MODEL_PROVIDER=$MODEL_PROVIDER

echo "✅ Environment variables set"
echo "✅ 环境变量已设置"
echo "📋 Model Provider: $MODEL_PROVIDER"

# Stop any existing process on port 8001
echo "🔄 Stopping any existing server on port 8001..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

echo "🚀 Starting server with $MODEL_PROVIDER model..."
echo "🚀 使用 $MODEL_PROVIDER 模型启动服务器..."
echo "💡 Usage examples:"
echo "   ./start_server.sh siliconflow  # Use cloud model (default)"
echo "   ./start_server.sh qwen3        # Use local Qwen3 model"
echo "   ./start_server.sh openai_like  # Use local Phi3.5 model"
echo ""
echo "📊 Check model info at: http://localhost:8001/api/rag/model_info"
echo ""

# Start the server
python3 web_app.py