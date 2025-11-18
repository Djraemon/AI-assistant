# 🎓 AI助教RAG系统 - 快速启动指南

## 🚀 启动方式

### 1. 基础启动（默认使用SiliconFlow云模型）
```bash
./start_server.sh
# 或者
./start_server.sh siliconflow
```

### 2. 使用本地Qwen3模型
```bash
./start_server.sh qwen3
```

### 3. 使用本地Phi3.5模型
```bash
./start_server.sh openai_like
```

### 4. 交互式模型切换
```bash
./switch_model.sh
```

## 📊 模型信息

启动后，访问以下地址查看当前使用的模型信息：
- **模型信息**: http://localhost:8001/api/rag/model_info
- **健康检查**: http://localhost:8001/health
- **Web界面**: http://localhost:8001

## 🤖 模型对比

| 模型 | 类型 | 位置 | 优势 | 劣势 |
|------|------|------|------|------|
| **SiliconFlow** | 云端模型 | 在线 | 无需本地资源，稳定 | 需要网络，有API费用 |
| **Qwen3** | 本地视觉语言模型 | 本地 | 支持图像，隐私安全 | 需要大内存，加载慢 |
| **Phi3.5** | 本地文本模型 | 本地 | 轻量级，快速 | 仅支持文本 |

## ⚙️ 配置文件

配置文件位置：`src/config.py`

主要配置项：
```python
# Qwen3模型配置
qwen3_model_path: str = "./model-qwen3/Qwen3_vl_thinking"
qwen3_device_map: str = "auto"  # auto/cpu/mps/cuda
qwen3_torch_dtype: str = "bfloat16"  # float16/bfloat16/float32
qwen3_max_new_tokens: int = 1024
```

## 🔧 故障排除

### Qwen3模型加载失败
1. 检查transformers版本：
   ```bash
   pip install --upgrade transformers>=4.45.0
   ```

2. 检查内存使用（建议8GB+）

3. 查看错误日志，系统会给出具体解决建议

### 服务器端口冲突
```bash
# 杀死占用8001端口的进程
lsof -ti:8001 | xargs kill -9
```

### 查看详细日志
启动时会显示详细的模型加载信息，包括：
- 模型路径
- 设备映射（MPS/CPU/CUDA）
- 数据类型
- 加载状态

## 📝 使用示例

### 启动Qwen3模型
```bash
# 方法1：直接启动
./start_server.sh qwen3

# 方法2：交互式选择
./switch_model.sh
# 然后选择 1
```

### 检查模型状态
```bash
curl http://localhost:8001/api/rag/model_info
```

### 测试问答
访问 http://localhost:8001 并在网页中提问：
- "请解释机器学习的基本概念"
- "什么是深度学习？"
- "推荐一些学习AI的资源"

## 🎉 现在你可以：

1. ✅ **一键切换模型**：通过启动脚本参数选择不同模型
2. ✅ **查看模型信息**：通过API端点了解当前模型状态
3. ✅ **交互式切换**：使用 `switch_model.sh` 快速切换
4. ✅ **统一启动**：所有模型都通过 `start_server.sh` 启动