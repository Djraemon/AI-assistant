# AI Teaching Assistant RAG System

这是一个基于 LlamaIndex 构建的 AI 教学助手机器人系统，支持多种数据源（PPT、练习题、教材等）的智能问答。

## 功能特性

- **多数据源支持**: 支持 PDF、Word、PPT、文本等多种格式
- **智能问答**: 针对课程内容、练习题、概念解释等不同场景优化
- **模块化架构**: 支持扩展新数据类型和功能
- **中文优化**: 提示词和交互全程中文支持
- **Web界面**: 提供基于FastAPI的网页版交互界面
- **评估反馈**: 自动评估回答质量，支持用户反馈

## 目录结构

```
schoolRAG/
├── config.py              # 系统配置
├── data_ingestor.py       # 数据摄入模块
├── index_manager.py       # 索引管理模块
├── query_engine.py        # 查询引擎模块
├── evaluation.py          # 评估反馈模块
├── web_app.py             # Web应用（FastAPI）
├── utils.py               # 工具函数
├── requirements.txt       # 依赖包列表
├── prompt/
│   └── prompt_template.py # 提示词模板
├── data/
│   ├── ppt/              # 课程PPT/讲义
│   ├── practice/         # 练习题库
│   ├── textbook/         # 教材内容
│   ├── evaluation/       # 评估数据
│   └── feedback/         # 用户反馈
└── source/
    └── rag_demo.py       # 命令行版主程序入口
```

## 数据目录说明

- `data/ppt/`: 放置课程PPT转换的PDF文件
- `data/practice/`: 放置练习题、习题集（支持JSON、TXT格式）
- `data/textbook/`: 放置教材内容（支持PDF、DOCX等格式）
- `data/evaluation/`: 放置评估数据
- `data/feedback/`: 放置用户反馈数据

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 命令行版本
```bash
cd /Users/suny.ding/Desktop/schoolRAG
python source/rag_demo.py
```

### 2. Web版本
```bash
cd /Users/suny.ding/Desktop/schoolRAG
python web_app.py
```
然后在浏览器中访问 `http://localhost:8000`

## API 配置

系统默认使用 SiliconFlow API，可在 `config.py` 中修改：

```python
api_key = "your-api-key"
llm_model = "Qwen/Qwen2.5-7B-Instruct"
embedding_model = "netease-youdao/bce-embedding-base_v1"
```

## 问答模式

系统支持不同类型的问答：

- **概念解释**: 询问课程中的概念定义
- **内容总结**: 总结课程主要内容
- **练习解答**: 解答练习题并给出思路
- **综合问答**: 结合多种资料回答问题

## Web界面功能

- **实时对话**: 在网页中与AI助手交互
- **评分系统**: 为AI回答进行评分
- **反馈收集**: 提供详细的反馈意见
- **评估显示**: 显示AI回答的评估分数
- **清空对话**: 重置对话历史

## 扩展支持

系统设计支持以下数据类型的扩展：
- PDF 文档
- Word 文档
- PPT 演示文稿
- 文本文件
- JSON 结构化数据
- CSV 表格数据