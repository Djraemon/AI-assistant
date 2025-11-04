## 三、 RAG / 大模型模块接口设计


<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'>接口功能</td><td style='text-align: center;'>方法</td><td style='text-align: center;'>路径</td></tr><tr><td style='text-align: center;'>RAG对话接口（流式输出）</td><td style='text-align: center;'>POST</td><td style='text-align: center;'>/api/rag/chat/stream</td></tr></table>

RAG 对话接口（Server-Sent Events 流式输出）

POST /api/rag/chat/stream Content-Type: application/json

请求体：
{
    "user_id": "s1",
    "question": "请解释一下什么是卷积神经网络?",
    "session_id": "sess_abc123",
    "stream": true
}

## 响应头:

Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

## 流式响应示例：

event: start
data: {"type": "start"}
event: delta
data: {"type": "delta", "content": "卷积神经网络是一种..."}
event: delta
data: {"type": "delta", "content": "网格状数据的深度学习模型...", "timestamp": "2024-01-20T10:30:03Z"}
event: sources
data: {"type": "sources", "sources": [{"node_id": "6.2", "node_name": "TensorFlow", "excerpt": "深度学习框架..."}], "timestamp": "2024-01-20T10:30:03Z"}
event: end
data: {"type": "end", "total_tokens": 150, "timestamp": "2024-01-20T10:30:05Z"}