#!/usr/bin/env python3
"""
启动使用Qwen3模型的RAG系统
Launch RAG system with Qwen3 model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    print("🚀 启动RAG系统 - 使用Qwen3模型")

    # 设置环境变量以使用Qwen3模型
    os.environ['RAG_MODEL_PROVIDER'] = 'qwen3'

    # 或者直接修改配置
    try:
        from src.config import CONFIG
        print("📝 配置当前provider为qwen3...")
        CONFIG.model_config.provider = "qwen3"

        print(f"📂 模型路径: {CONFIG.model_config.qwen3_model_path}")
        print(f"🔧 设备映射: {CONFIG.model_config.qwen3_device_map}")
        print(f"💾 数据类型: {CONFIG.model_config.qwen3_torch_dtype}")

        # 检查模型文件
        model_path = CONFIG.model_config.qwen3_model_path
        if os.path.exists(model_path):
            print("✅ 模型路径存在")
            # 检查关键文件
            key_files = ["config.json", "tokenizer.json"]
            for file in key_files:
                if os.path.exists(os.path.join(model_path, file)):
                    print(f"✅ {file} 存在")
                else:
                    print(f"❌ {file} 不存在")
        else:
            print("❌ 模型路径不存在，请检查配置")
            return

        print("\n🔄 启动FastAPI应用...")
        print("💡 提示：如果遇到模型加载问题，请确保:")
        print("   1. 安装了所需的依赖: transformers, torch, llama-index")
        print("   2. 有足够的内存/显存")
        print("   3. 如果在macOS上，建议使用MPS设备")

        # 启动web应用
        import subprocess
        subprocess.run([sys.executable, "web_app.py"])

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n🔧 故障排除:")
        print("1. 确保安装了所有依赖:")
        print("   pip install transformers torch llama-index")
        print("2. 检查模型文件是否完整")
        print("3. 确保有足够的系统内存")

if __name__ == "__main__":
    main()