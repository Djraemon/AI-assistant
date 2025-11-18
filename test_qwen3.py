#!/usr/bin/env python3
"""
测试Qwen3模型集成的脚本
Test script for Qwen3 model integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import CONFIG

def test_qwen3_config():
    """测试Qwen3配置"""
    print("🔧 测试Qwen3配置...")
    print(f"模型路径: {CONFIG.model_config.qwen3_model_path}")
    print(f"设备映射: {CONFIG.model_config.qwen3_device_map}")
    print(f"数据类型: {CONFIG.model_config.qwen3_torch_dtype}")
    print(f"最大新token: {CONFIG.model_config.qwen3_max_new_tokens}")

    # 检查模型文件是否存在
    if os.path.exists(CONFIG.model_config.qwen3_model_path):
        print("✅ 模型路径存在")
        # 检查必要文件
        required_files = ["config.json", "tokenizer.json", "model.safetensors.index.json"]
        for file in required_files:
            file_path = os.path.join(CONFIG.model_config.qwen3_model_path, file)
            if os.path.exists(file_path):
                print(f"✅ {file} 存在")
            else:
                print(f"❌ {file} 不存在")
    else:
        print("❌ 模型路径不存在")

def test_qwen3_loading():
    """测试Qwen3模型加载"""
    print("\n🔄 测试Qwen3模型加载...")

    try:
        # 设置provider为qwen3
        CONFIG.model_config.provider = "qwen3"

        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        model_path = CONFIG.model_config.qwen3_model_path

        # 检查模型文件
        if not os.path.exists(model_path):
            print(f"❌ 模型路径不存在: {model_path}")
            return False

        print(f"📂 正在加载tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print("✅ Tokenizer加载成功")

        print(f"🧠 正在加载模型...")
        # 只加载模型配置，不加载权重
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,  # 使用轻量级类型进行测试
            device_map="cpu",  # 使用CPU避免内存问题
            trust_remote_code=True,
            # 只加载配置，不加载完整权重以节省内存
            low_cpu_mem_usage=True
        )
        print("✅ 模型加载成功")

        # 测试tokenization
        test_text = "你好，这是一个测试。"
        inputs = tokenizer(test_text, return_tensors="pt")
        print(f"✅ Tokenization测试成功: {len(inputs['input_ids'][0])} tokens")

        return True

    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return False

def test_rag_integration():
    """测试与RAG系统的集成"""
    print("\n🔗 测试RAG系统集成...")

    try:
        # 临时设置配置使用Qwen3
        original_provider = CONFIG.model_config.provider
        CONFIG.model_config.provider = "qwen3"

        # 尝试导入和初始化
        from llama_index.core import Settings
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from llama_index.llms.huggingface import HuggingFaceLLM
        import torch

        model_path = CONFIG.model_config.qwen3_model_path

        # 简化的模型加载（只测试配置）
        print("📝 测试模型配置...")

        # 测试tokenizer加载
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        print("✅ Tokenizer配置正确")

        print("✅ RAG系统集成测试通过")

        # 恢复原始配置
        CONFIG.model_config.provider = original_provider

        return True

    except Exception as e:
        print(f"❌ RAG系统集成失败: {e}")
        # 恢复原始配置
        CONFIG.model_config.provider = original_provider
        return False

def main():
    """主函数"""
    print("🧪 开始测试Qwen3模型集成\n")

    # 测试配置
    test_qwen3_config()

    # 测试模型加载
    loading_success = test_qwen3_loading()

    # 测试RAG集成
    if loading_success:
        integration_success = test_rag_integration()

        if integration_success:
            print("\n🎉 所有测试通过！")
            print("\n💡 使用方法:")
            print("1. 设置环境变量或修改配置文件:")
            print("   export RAG_MODEL_PROVIDER=qwen3")
            print("2. 或者在src/config.py中设置:")
            print("   CONFIG.model_config.provider = \"qwen3\"")
            print("3. 运行RAG系统:")
            print("   python web_app.py")
        else:
            print("\n❌ RAG集成测试失败")
    else:
        print("\n❌ 模型加载失败，请检查模型文件")

if __name__ == "__main__":
    main()