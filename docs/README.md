# 🎓 AI助教RAG系统

基于 LlamaIndex 构建的智能教学助手系统，支持多种大语言模型和混合部署模式，为教育场景提供专业的RAG（检索增强生成）问答服务。

## ✨ 核心特性

### 🤖 多模型支持
- **云模型**: SiliconFlow API 集成 (Qwen2.5-7B-Instruct)
- **本地模型**: Phi3.5 本地部署支持
- **混合模式**: 本地LLM + 云端嵌入
- **灵活切换**: 通过配置文件一键切换模型提供商

### 📚 多数据源集成
- **课程材料**: PPT、PDF、Word文档
- **练习题库**: JSON、TXT格式习题集
- **教材内容**: 支持多种文档格式
- **自动解析**: 智能文档解析和元数据标注

### 🌐 现代化Web界面
- **FastAPI框架**: 高性能异步Web服务
- **流式对话**: Server-Sent Events实时响应
- **响应式设计**: 适配多种设备
- **中文优化**: 全程中文交互体验

### 📊 智能评估系统
- **自动评估**: 相关性、完整性、准确性多维度评分
- **用户反馈**: 支持评分和文字反馈
- **性能监控**: 实时系统性能统计
- **持续优化**: 基于反馈的系统改进

## 🏗️ 系统架构

```
schoolRAG/
├── 📁 src/                    # 核心源代码
│   ├── config.py             # 系统配置管理
│   ├── data_ingestor.py      # 数据摄取和预处理
│   ├── index_manager.py      # 向量索引管理
│   ├── query_engine.py       # 查询引擎和意图分类
│   ├── evaluation.py         # 评估和反馈系统
│   ├── paddleOCR.py          # OCR文字识别
│   ├── templates/            # Web模板文件
│   └── prompt/               # 提示词模板
├── 📁 data/                   # 数据目录
│   ├── ppt/                  # 课程PPT/讲义 (PDF格式)
│   ├── practice/             # 练习题库
│   ├── textbook/             # 教材内容
│   ├── evaluation/           # 评估数据
│   └── feedback/             # 用户反馈
├── 📁 model-phi3.5/           # 本地Phi3.5模型
├── 📁 utils/                  # 工具函数
├── 📁 tests/                  # 测试用例
├── 📁 docs/                   # 项目文档
├── 📄 web_app.py              # Web应用主程序
├── 📄 requirements.txt        # 依赖包列表
└── 📄 .env                    # 环境变量配置
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 8GB+ RAM (本地模型需要16GB+)
- 可选: NVIDIA GPU (本地模型加速)

### 安装步骤

1.  **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
# 创建 .env 文件
cp .env.example .env

# 编辑配置

# SiliconFlow API (云模型)
provider: str = "siliconflow"
SILICONFLOW_API_KEY=your_siliconflow_api_key

# 本地Phi3.5模型 (可选)
provider: str = "openailike" # 下载phi-3.5到schoolrag/model路径下之后再用
OPENAI_LIKE_API_KEY=sk-local-phi3.5
```

### 启动服务

#### 方式一: 云模型模式 (推荐新手)
```bash
bash start_server.sh
```

### 访问系统

- **Web界面**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health

## 📖 使用指南

### 数据准备

1. **课程材料**: 将PPT转换为PDF后放入 `data/ppt/`
2. **练习题库**: 将习题集放入 `data/practice/`
3. **教材内容**: 将教材放入 `data/textbook/`

支持的文件格式:
- 📄 PDF文档
- 📝 Word文档 (.docx)
- 📊 PowerPoint (.pptx)
- 📄 文本文件 (.txt, .md)
- 📋 结构化数据 (.json, .csv)

### API使用示例

#### 标准问答
```python
import requests

response = requests.post(
    "http://localhost:8001/api/rag/query",
    json={"query": "请解释什么是机器学习？"}
)

result = response.json()
print(f"回答: {result['response']}")
print(f"评分: {result['evaluation']['overall_score']}")
```

#### 流式对话
```javascript
async function streamChat(question) {
    const response = await fetch('/api/rag/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: 'user123',
            question: question,
            session_id: 'session456',
            stream: true
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        // 处理流式数据...
    }
}
```

## ⚙️ 配置说明

### 模型配置 (`src/config.py`)

```python
@dataclass
class ModelConfig:
    # 模型提供商选择
    provider: str = "siliconflow"  # 或 "openai_like"

    # SiliconFlow 配置
    api_key: str = "your_api_key"
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    embedding_model: str = "netease-youdao/bce-embedding-base_v1"

    # 本地模型配置
    openai_like_api_key: str = "sk-local-phi3.5"
    openai_like_api_base: str = "http://localhost:8000/v1"
    openai_like_model: str = "phi-3.5-mini"
```

### RAG参数配置

```python
@dataclass
class RAGConfig:
    similarity_top_k: int = 5      # 检索文档数量
    rerank_top_n: int = 3          # 重排序后文档数量
    enable_reranking: bool = True  # 启用重排序
    enable_query_expansion: bool = True  # 启用查询扩展
```

## 🎯 问答模式

系统支持多种教育场景的问答:

| 模式 | 适用场景 | 示例问题 |
|------|----------|----------|
| **概念解释** | 理解专业术语 | "什么是卷积神经网络？" |
| **内容总结** | 概括课程重点 | "总结一下第三章的主要内容" |
| **练习解答** | 习题讲解分析 | "这道题的解题思路是什么？" |
| **综合问答** | 跨资料综合回答 | "结合实践案例解释这个理论" |

## 📊 系统监控

### 性能指标
- **响应时间**: 平均1-3秒 (云模型) / 2-5秒 (本地)
- **相关性得分**: 自动评估回答与问题的相关性
- **用户满意度**: 基于用户反馈的评分统计
- **系统负载**: 实时监控服务状态

### 统计API
```bash
curl http://localhost:8001/api/rag/stats
```

返回示例:
```json
{
  "performance_metrics": {
    "avg_relevance_score": 0.85,
    "total_queries": 156,
    "avg_response_time": 1.2
  },
  "data_stats": {
    "total_documents": 168,
    "source_breakdown": {
      "ppt": 95,
      "practice": 34,
      "textbook": 39
    }
  }
}
```

## 🔧 开发指南

### 添加新数据类型

1. **扩展DataIngestor** (`src/data_ingestor.py`):
```python
def ingest_new_data_type(self) -> List[Document]:
    # 实现新数据类型的摄取逻辑
    pass
```

2. **更新配置** (`src/config.py`):
```python
supported_extensions: List[str] = [
    '.pdf', '.docx', '.pptx', '.txt', '.md', '.csv', '.json',
    '.your_new_extension'  # 添加新扩展名
]
```

### 自定义提示词模板

编辑 `prompt/prompt_template.py`:
```python
custom_qa_template = PromptTemplate(
    "你的自定义提示词模板..."
)
```

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_query_engine.py
```

## 🐛 故障排除

### 常见问题

**Q: 模型加载失败**
```bash
# 检查API密钥
echo $SILICONFLOW_API_KEY

# 验证网络连接
curl https://api.siliconflow.cn/v1/models
```

**Q: 本地模型启动失败**
- 检查模型文件是否完整下载
- 确认硬件配置满足要求
- 查看端口8000是否被占用

**Q: 搜索结果不准确**
- 调整 `similarity_top_k` 参数
- 检查文档质量和预处理效果
- 考虑启用查询扩展功能

### 日志调试
```bash
# 启用详细日志
export RAG_DEBUG=1
python web_app.py
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 技术支持

- **文档**: [详细API文档](new_API.md)
- **问题反馈**: [GitHub Issues](https://github.com/your-repo/issues)
- **配置指南**: [src/config.py](src/config.py)
- **本地模型**: [model-phi3.5/](model-phi3.5/)

---

**⚡ 开始体验AI助教的强大功能吧！**