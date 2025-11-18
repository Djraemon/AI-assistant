# 🎓 AI助教RAG系统 API 接口文档

## 📋 系统概述

AI助教RAG系统是一个基于RAG（检索增强生成）技术的智能教学助手，支持多种LLM模型（包括云服务和本地Phi3.5模型），提供智能问答、流式对话、反馈收集和系统监控等功能。

### 基本信息
- **服务地址**: `http://localhost:8001`
- **API 版本**: `v1.0.0`
- **技术栈**: FastAPI + Python + LlamaIndex
- **数据格式**: JSON
- **流式支持**: Server-Sent Events (SSE)
- **模型支持**: SiliconFlow云模型 + 本地Phi3.5模型

---

## 🗂️ 接口总览

| 接口分类 | 方法 | 路径 | 功能描述 |
|---------|------|------|----------|
| **页面服务** | GET | `/` | 返回 Web 应用主页 |
| **问答接口** | POST | `/api/rag/query` | 标准 RAG 问答接口 |
| **兼容接口** | POST | `/api/rag/v1/chat/completions` | OpenAI API 兼容格式 |
| **流式接口** | POST | `/api/rag/stream` | SSE 流式对话 ⭐ |
| **反馈接口** | POST | `/api/rag/feedback` | 用户反馈收集 |
| **统计接口** | GET | `/api/rag/stats` | 系统性能统计 |
| **健康检查** | GET | `/health` | 服务状态检查 |

---

## 📝 详细接口说明

### 1. 主页服务

#### `GET /`
返回 Web 应用的主页面，提供用户交互界面。

---

### 2. 标准问答接口

#### `POST /api/rag/query`

基础的 RAG 问答接口，返回完整的回答内容和评估结果。

**请求格式**:
```json
{
  "query": "请解释一下什么是卷积神经网络?",
  "mode": "general"
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | ✅ | - | 用户问题文本 |
| mode | string | ❌ | "general" | 查询模式 |

**响应格式**:
```json
{
  "query": "请解释一下什么是卷积神经网络?",
  "response": "卷积神经网络是一种专门处理网格状数据的深度学习模型...",
  "evaluation": {
    "query": "请解释一下什么是卷积神经网络?",
    "response_length": 369,
    "relevance_score": 0.85,
    "completeness_score": 0.92,
    "accuracy_score": 0.78,
    "timestamp": "2025-11-04T21:33:55.858148",
    "overall_score": 0.85,
    "response": "卷积神经网络是一种...",
    "context_provided": false
  }
}
```

**响应参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| query | string | 原始问题 |
| response | string | AI 生成的回答内容 |
| evaluation | object | 评估指标对象 |

---

### 3. OpenAI 兼容接口

#### `POST /api/rag/v1/chat/completions`

完全兼容 OpenAI ChatGPT API 格式的接口，便于现有应用迁移。

**请求格式**: 与 `/api/rag/query` 相同
**响应格式**: 与 `/api/rag/query` 相同

---

### 4. 流式对话接口 ⭐

#### `POST /api/rag/stream`

**核心接口** - 使用 Server-Sent Events 技术的实时流式对话，提供流畅的用户体验。

**请求格式**:
```json
{
  "user_id": "s1",
  "question": "请解释一下什么是卷积神经网络?",
  "session_id": "sess_abc123",
  "stream": true
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | ✅ | 用户唯一标识 |
| question | string | ✅ | 用户问题 |
| session_id | string | ✅ | 会话标识 |
| stream | boolean | ✅ | 启用流式输出（固定为 true） |

**响应头**:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
Access-Control-Allow-Origin: *
```

**流式事件序列**:

1. **开始事件**
```
event: start
data: {"type": "start", "timestamp": "2025-11-04T21:30:01Z"}
```

2. **增量内容事件** (可多次出现)
```
event: delta
data: {"type": "delta", "content": "卷积神经网络是一种...", "timestamp": "2025-11-04T21:30:03Z"}
```

3. **来源引用事件**
```
event: sources
data: {
  "type": "sources",
  "sources": [
    {
      "node_id": "6.2",
      "node_name": "深度学习基础",
      "excerpt": "卷积神经网络是深度学习的重要模型..."
    }
  ],
  "timestamp": "2025-11-04T21:30:03Z"
}
```

4. **结束事件**
```
event: end
data: {"type": "end", "total_tokens": 150, "timestamp": "2025-11-04T21:30:05Z"}
```

5. **错误事件** (异常情况)
```
event: error
data: {
  "type": "error",
  "message": "Error processing query: ...",
  "timestamp": "2025-11-04T21:30:05Z"
}
```

---

### 5. 用户反馈接口

#### `POST /api/rag/feedback`

收集用户对问答质量的反馈，用于持续优化系统性能。

**请求格式**:
```json
{
  "query": "请解释一下什么是卷积神经网络?",
  "response": "卷积神经网络是一种深度学习模型...",
  "rating": 5,
  "comment": "回答很详细，很有帮助"
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | ✅ | 原始问题 |
| response | string | ✅ | AI 生成的回答 |
| rating | integer | ❌ | 用户评分 (1-5分制) |
| comment | string | ❌ | 用户文字反馈 |

**响应格式**:
```json
{
  "message": "Feedback received successfully"
}
```

---

### 6. 系统统计接口

#### `GET /api/rag/stats`

提供系统性能指标和数据统计，用于监控和分析。

**响应格式**:
```json
{
  "performance_metrics": {
    "avg_relevance_score": 0.82,
    "avg_completeness_score": 0.88,
    "avg_accuracy_score": 0.75,
    "total_queries": 156,
    "avg_response_time": 1.2
  },
  "feedback_summary": {
    "avg_rating": 4.3,
    "total_feedback": 45,
    "rating_distribution": {
      "5": 25,
      "4": 12,
      "3": 6,
      "2": 2,
      "1": 0
    }
  },
  "data_stats": {
    "total_documents": 168,
    "total_nodes": 447,
    "source_breakdown": {
      "ppt": 95,
      "practice": 34,
      "textbook": 39
    }
  }
}
```

**响应参数说明**:
- **performance_metrics**: 系统性能指标
  - `avg_relevance_score`: 平均相关性得分
  - `avg_completeness_score`: 平均完整性得分
  - `avg_accuracy_score`: 平均准确性得分
  - `total_queries`: 总查询次数
  - `avg_response_time`: 平均响应时间（秒）

- **feedback_summary**: 用户反馈汇总
  - `avg_rating`: 平均用户评分
  - `total_feedback`: 反馈总数
  - `rating_distribution`: 评分分布

- **data_stats**: 数据统计
  - `total_documents`: 文档总数
  - `total_nodes`: 索引节点总数
  - `source_breakdown`: 数据源分类统计

---

### 7. 健康检查接口

#### `GET /health`

简单的服务健康状态检查，用于负载均衡器和监控系统。

**响应格式**:
```json
{
  "status": "healthy",
  "message": "AI Teaching Assistant is running"
}
```

---

## 🤖 模型配置

### 支持的模型类型

#### 1. SiliconFlow 云模型 (默认)
- **LLM模型**: `Qwen/Qwen2.5-7B-Instruct`
- **嵌入模型**: `netease-youdao/bce-embedding-base_v1`
- **API地址**: `https://api.siliconflow.cn/v1/`

#### 2. 本地Phi3.5模型
- **LLM模型**: `phi-3.5-mini` (本地部署)
- **嵌入模型**: SiliconFlow云服务 (混合模式)
- **API地址**: `http://localhost:8000/v1`

### 模型切换

通过修改 `src/config.py` 文件切换模型提供商：

```python
# 使用云模型 (默认)
provider: str = "siliconflow"

# 使用本地Phi3.5模型
provider: str = "openai_like"
```

### 环境变量配置

**.env 文件配置**:
```env
# SiliconFlow 云模型配置
SILICONFLOW_API_KEY=your_siliconflow_api_key

# 本地Phi3.5模型配置
OPENAI_LIKE_API_KEY=sk-local-phi3.5
OPENAI_LIKE_API_BASE=http://localhost:8000/v1
```

---

## 🔧 数据模型定义

### QueryRequest
```python
class QueryRequest(BaseModel):
    query: str          # 用户问题
    mode: str = "general"  # 查询模式
```

### StreamChatRequest
```python
class StreamChatRequest(BaseModel):
    user_id: str        # 用户ID
    question: str       # 问题内容
    session_id: str     # 会话ID
    stream: bool = True # 流式标志
```

### FeedbackRequest
```python
class FeedbackRequest(BaseModel):
    query: str                    # 原始问题
    response: str                 # AI回答
    rating: Optional[int] = None  # 用户评分
    comment: Optional[str] = None # 用户评论
```

### QueryResponse
```python
class QueryResponse(BaseModel):
    query: str         # 原始问题
    response: str      # AI回答
    evaluation: dict   # 评估结果
```

---

## 🚀 使用示例

### Python 客户端示例

#### 标准问答
```python
import requests

# 发送问题
response = requests.post(
    "http://localhost:8001/api/rag/query",
    json={"query": "什么是机器学习?"}
)

result = response.json()
print(f"问题: {result['query']}")
print(f"回答: {result['response']}")
print(f"评估: {result['evaluation']}")
```

#### 流式对话
```python
import requests
import json

# 流式接收回答
response = requests.post(
    "http://localhost:8001/api/rag/stream",
    json={
        "user_id": "user123",
        "question": "解释深度学习的基本原理",
        "session_id": "session456",
        "stream": True
    },
    headers={"Accept": "text/event-stream"},
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print(f"事件: {data['type']}")
            if data['type'] == 'delta':
                print(f"内容: {data['content']}")
```

### JavaScript 客户端示例

```javascript
// 流式对话
async function streamChat() {
    const response = await fetch('/api/rag/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        },
        body: JSON.stringify({
            user_id: 'user123',
            question: '什么是人工智能？',
            session_id: 'session456',
            stream: true
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                handleStreamEvent(data);
            }
        }
    }
}

function handleStreamEvent(data) {
    switch (data.type) {
        case 'start':
            console.log('开始对话');
            break;
        case 'delta':
            console.log('新内容:', data.content);
            break;
        case 'sources':
            console.log('引用来源:', data.sources);
            break;
        case 'end':
            console.log('对话结束');
            break;
        case 'error':
            console.error('错误:', data.message);
            break;
    }
}
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:8001/health

# 标准问答
curl -X POST "http://localhost:8001/api/rag/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是神经网络？"}'

# 流式对话
curl -X POST "http://localhost:8001/api/rag/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "user_id": "user1",
    "question": "解释卷积神经网络",
    "session_id": "session1",
    "stream": true
  }'

# 提交反馈
curl -X POST "http://localhost:8001/api/rag/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是机器学习？",
    "response": "机器学习是人工智能的一个分支...",
    "rating": 5,
    "comment": "回答很详细"
  }'

# 获取统计信息
curl http://localhost:8001/api/rag/stats
```

---

## 📊 性能考虑

### 响应时间
- **云模型标准问答**: 1-3秒
- **本地模型标准问答**: 2-5秒
- **流式对话**: 首字响应 < 1秒，完整输出 3-8秒
- **健康检查**: < 100ms
- **统计查询**: 200-500ms

### 并发支持
- 支持多用户并发访问
- 流式连接有内存开销，建议控制并发数
- 本地模型并发能力受硬件限制

### 模型性能对比
| 模型类型 | 响应速度 | 准确性 | 成本 | 隐私性 |
|---------|----------|--------|------|--------|
| SiliconFlow云模型 | 快 | 高 | 按量付费 | 中等 |
| 本地Phi3.5模型 | 中等 | 中等 | 一次性成本 | 高 |

---

## ⚠️ 错误处理

### 标准错误响应
```json
{
  "detail": "Error message describing the issue"
}
```

### 常见错误状态码
| 状态码 | 错误类型 | 可能原因 |
|--------|----------|----------|
| 400 | Bad Request | 请求参数格式错误 |
| 500 | Internal Server Error | 系统内部错误 |
| 503 | Service Unavailable | 系统未初始化 |

### 典型错误场景
- **系统未初始化**: `"Query engine not initialized"`
- **查询处理失败**: `"Error processing query: ..."`
- **评估管理器未初始化**: `"Evaluation manager not initialized"`
- **本地模型服务不可用**: `"Connection refused to localhost:8000"`

---

## 🔧 本地模型部署

### Phi3.5模型启动步骤

1. **安装依赖**:
```bash
pip install llama-cpp-python
# GPU版本 (推荐)
pip install llama-cpp-python --prefer-binary --extra-index-url=https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118
```

2. **启动Phi3.5 API服务**:
```bash
python3 phi3_api_server.py
```

3. **验证服务**:
```bash
curl http://localhost:8000/
```

4. **启动RAG系统**:
```bash
export OPENAI_LIKE_API_KEY=sk-local-phi3.5
export SILICONFLOW_API_KEY=your_siliconflow_key
python3 web_app.py
```

### 本地模型配置文件

**phi3_api_server.py**: Phi3.5 OpenAI兼容API服务器
**PHI3_SETUP_GUIDE.md**: 详细部署指南
**start_phi3_service.sh**: 启动脚本

---

## 🔄 版本更新日志

### v1.1.0 (当前版本)
- ✅ 支持本地Phi3.5模型集成
- ✅ 优化API路径为 `/api/rag/*`
- ✅ 改进模板文件结构
- ✅ 增强错误处理机制
- ✅ 支持混合模式（本地LLM + 云嵌入）

### v1.0.0
- ✅ 基础问答功能
- ✅ 流式对话支持
- ✅ 用户反馈收集
- ✅ 系统监控统计
- ✅ OpenAI API 兼容
- ✅ 健康检查机制

---

## 📞 技术支持

如有技术问题或建议，请参考：
- **项目文档**: `/docs/` 目录
- **配置文件**: `src/config.py`
- **本地模型指南**: `PHI3_SETUP_GUIDE.md`
- **系统日志**: 启动时的控制台输出
- **API健康检查**: `GET /health`

**重要提示**: 使用前请确保系统已完全初始化，可通过 `/health` 接口检查状态。如需使用本地模型，请先启动Phi3.5 API服务。