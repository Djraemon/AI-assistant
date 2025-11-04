#!/bin/bash

# AI Teaching Assistant RAG System - Server Startup Script
# AI助教RAG系统 - 服务器启动脚本

echo "🎓 Starting AI Teaching Assistant RAG System..."
echo "🎓 启动AI助教RAG系统..."

# Set environment variables
export SILICONFLOW_API_KEY=sk-yrmmgcztvxoijeigwmhqqohhafaolagrmlffjuhiifmrdlcg
export OPENAI_LIKE_API_KEY=dummy

echo "✅ Environment variables set"
echo "✅ 环境变量已设置"

# Stop any existing process on port 8001
echo "🔄 Stopping any existing server on port 8001..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

echo "🚀 Starting server..."
echo "🚀 启动服务器..."

# Start the server
python3 web_app.py