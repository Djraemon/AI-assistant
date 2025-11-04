使用场景
from llama_index.llms.openai_like import OpenAILike
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# 1️⃣ 配置本地模型
llm = OpenAILike(
    model="phi-3.5-mini",
    api_base="http://llm.lbzfrombit.icu:8000/v1",
    api_key="dummy",
    is_chat_model=True
)
# 2️⃣ 配置 Embedding 模型
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
Settings.llm = llm
Settings.embed_model = embed_model

# 3️⃣ 加载文档并创建索引
documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)

# 4️⃣ 开始查询!
query_engine = index.as_query_engine()
response = query_engine.query("你的问题")
print(response)


环境配置
安装依赖
# 基础安装
pip install llama-index
pip install llama-index-llms-openai-like
pip install llama-index-embeddings-huggingface
# 文档处理 (可选)
pip install pypdf 
pip install docx2txt 
pip install openpyxl 
pip install python-pptx # PDF 支持
# Word 文档支持
# Excel 支持
# PPT 支持
# 向量数据库 (可选)
pip install chromadb # Chroma
pip install qdrant-client # Qdrant
pip install pymilvus # Milvus
启动本地模型服务
确保后端服务正在运行:
curl http://llm.lbzfrombit.icu:8000/v1/models