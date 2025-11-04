#!/usr/bin/env python3
"""
本地模型启动脚本
如果遇到类型注解错误，可以尝试使用这个脚本
"""

import os
import sys

# 设置环境变量以避免一些警告
os.environ["TOKENIZERS_PARALLELISM"] = "false"

try:
    print("🚀 正在启动本地模型配置的RAG系统...")

    # 导入基本模块
    from config import CONFIG

    # 检查配置
    print(f"📋 当前配置:")
    print(f"   模型提供商: {CONFIG.model_config.provider}")
    print(f"   LLM模型: {CONFIG.model_config.openai_like_model}")
    print(f"   Embedding模型: {CONFIG.model_config.openai_like_embedding_model}")

    # 尝试启动应用
    from web_app import app
    import uvicorn

    print("✅ 配置加载成功")
    print("🌐 正在启动服务器...")

    uvicorn.run(app, host="0.0.0.0", port=8000)

except Exception as e:
    print(f"❌ 启动失败: {e}")
    print("💡 故障排除建议:")
    print("1. 确保phi-3.5-mini模型服务正在运行")
    print("2. 检查网络连接")
    print("3. 尝试使用SiliconFlow备用配置")
    print("4. 升级到Python 3.10+以获得更好的兼容性")

    # 回退到SiliconFlow
    print("🔄 正在尝试切换到SiliconFlow配置...")
    try:
        from config import ModelConfig
        # 创建临时配置
        temp_config = ModelConfig()
        temp_config.provider = "siliconflow"

        # 修改全局配置
        import config
        config.CONFIG.model_config.provider = "siliconflow"

        print("✅ 已切换到SiliconFlow配置")
        print("🌐 正在使用SiliconFlow启动服务器...")

        from web_app import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except Exception as fallback_error:
        print(f"❌ 备用方案也失败: {fallback_error}")
        sys.exit(1)
