#!/usr/bin/env python3
"""
测试基于LLM模型的意图识别功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_engine import TeachingQueryEngine
from config import CONFIG
from index_manager import IndexManager
from data_ingestor import DataIngestor

def test_intent_classification():
    """测试意图识别功能"""
    print("🧠 测试基于LLM的意图识别功能")
    print("=" * 50)

    # 初始化测试环境
    try:
        # 初始化模型配置
        from llama_index.core import Settings

        if CONFIG.model_config.provider == "openai_like":
            from llama_index.llms.openai_like import OpenAILike
            from llama_index.embeddings.siliconflow import SiliconFlowEmbedding

            Settings.llm = OpenAILike(
                model=CONFIG.model_config.openai_like_model,
                api_base=CONFIG.model_config.openai_like_api_base,
                api_key=CONFIG.model_config.openai_like_api_key,
                is_chat_model=CONFIG.model_config.is_chat_model
            )

            Settings.embed_model = SiliconFlowEmbedding(
                api_key=CONFIG.model_config.api_key,
                model_name=CONFIG.model_config.embedding_model
            )
            print(f"✅ 使用混合模型配置: {CONFIG.model_config.openai_like_model}")
        else:
            from llama_index.embeddings.siliconflow import SiliconFlowEmbedding
            from llama_index.llms.siliconflow import SiliconFlow

            Settings.embed_model = SiliconFlowEmbedding(
                api_key=CONFIG.model_config.api_key,
                model_name=CONFIG.model_config.embedding_model
            )

            Settings.llm = SiliconFlow(
                api_key=CONFIG.model_config.api_key,
                model=CONFIG.model_config.llm_model
            )
            print(f"✅ 使用SiliconFlow模型配置: {CONFIG.model_config.llm_model}")

        # 创建测试查询引擎（只用于意图测试，不需要实际的索引）
        class MockQueryEngine:
            def __init__(self, config):
                self.config = config

            def _classify_intent(self, query_str: str) -> str:
                """直接使用意图识别方法"""
                intent_prompt = f"""请分析用户的查询意图，并将其分类为以下两种类型之一：

1. **comprehensive** - 用户明确要求知道信息的来源、出处或参考资料
   - 关键词示例：来源、出自、根据什么、参考资料、哪个资料、哪里提到、哪里说的、根据哪个、基于什么、哪个文档、哪本书、哪个文件、原文、出处
   - 用户想知道信息的具体来源

2. **simple** - 用户只是想要获取信息答案，不关心具体来源
   - 一般性问题、概念解释、步骤说明等
   - 用户主要关注答案内容本身

用户查询："{query_str}"

请只回答以下两种结果之一（不要添加任何其他文字）：
comprehensive 或 simple

分类结果："""

                try:
                    # 使用当前配置的LLM进行意图识别
                    llm = Settings.llm
                    response = llm.complete(intent_prompt)
                    intent = str(response).strip().lower()

                    # 验证返回的意图是否有效
                    if intent in ["comprehensive", "simple"]:
                        return intent
                    else:
                        # 如果模型返回无效结果，使用关键词匹配作为后备方案
                        return self._fallback_keyword_classification(query_str)

                except Exception as e:
                    print(f"LLM意图识别失败，使用关键词匹配作为后备方案: {e}")
                    return self._fallback_keyword_classification(query_str)

            def _fallback_keyword_classification(self, query_str: str) -> str:
                """Fallback keyword-based classification when LLM fails."""
                query_lower = query_str.lower()
                source_keywords = [
                    '来源', '出自', '根据什么', '参考资料', '哪个资料', '哪里提到', '哪里说的',
                    '根据哪个', '基于什么', '哪个文档', '哪本书', '哪个文件', '原文', '出处'
                ]
                source_matches = sum(1 for keyword in source_keywords if keyword in query_lower)
                return "comprehensive" if source_matches > 0 else "simple"

        query_engine = MockQueryEngine(CONFIG)

        # 测试查询用例
        test_cases = [
            # Simple 意图测试
            ("什么是机器学习？", "simple"),
            ("解释一下深度学习的基本概念", "simple"),
            ("如何训练一个神经网络？", "simple"),
            ("Python中如何处理异常？", "simple"),
            ("线性回归的原理是什么？", "simple"),

            # Comprehensive 意图测试
            ("机器学习的定义来源于哪里？", "comprehensive"),
            ("这个概念是根据哪个教材提出的？", "comprehensive"),
            ("这些信息出自什么文档？", "comprehensive"),
            ("参考资料是什么？", "comprehensive"),
            ("哪本书中提到了这个理论？", "comprehensive"),

            # 边界测试 - 更自然的表达
            ("我想知道这个说法的出处", "comprehensive"),
            ("这个观点是基于什么研究？", "comprehensive"),
            ("告诉我答案，但也要说明来源", "comprehensive"),
            ("帮我解释一下，不用管来源", "simple"),
            ("直接告诉我怎么做就行", "simple"),
        ]

        print("\n📝 开始测试各种查询意图:\n")

        correct_count = 0
        total_count = len(test_cases)

        for i, (query, expected_intent) in enumerate(test_cases, 1):
            try:
                print(f"测试 {i}/{total_count}")
                print(f"查询: {query}")
                print(f"期望意图: {expected_intent}")

                # 调用意图识别方法
                predicted_intent = query_engine._classify_intent(query)
                print(f"预测意图: {predicted_intent}")

                # 判断是否正确
                is_correct = predicted_intent == expected_intent
                if is_correct:
                    correct_count += 1
                    print("✅ 正确")
                else:
                    print("❌ 错误")

                print("-" * 30)

            except Exception as e:
                print(f"❌ 测试失败: {e}")
                print("-" * 30)

        # 统计结果
        accuracy = correct_count / total_count * 100
        print(f"\n📊 测试结果统计:")
        print(f"总测试数: {total_count}")
        print(f"正确数: {correct_count}")
        print(f"准确率: {accuracy:.1f}%")

        if accuracy >= 80:
            print("🎉 意图识别效果良好！")
        elif accuracy >= 60:
            print("⚠️ 意图识别效果一般，可能需要调整提示词")
        else:
            print("🔧 意图识别需要优化")

        return accuracy

    except Exception as e:
        print(f"❌ 测试初始化失败: {e}")
        return 0

def test_fallback_mechanism():
    """测试后备机制（关键词匹配）"""
    print("\n🔄 测试后备关键词匹配机制")
    print("=" * 30)

    try:
        # 创建简单的测试类
        class TestFallback:
            def _fallback_keyword_classification(self, query_str: str) -> str:
                """Fallback keyword-based classification when LLM fails."""
                query_lower = query_str.lower()
                source_keywords = [
                    '来源', '出自', '根据什么', '参考资料', '哪个资料', '哪里提到', '哪里说的',
                    '根据哪个', '基于什么', '哪个文档', '哪本书', '哪个文件', '原文', '出处'
                ]
                source_matches = sum(1 for keyword in source_keywords if keyword in query_lower)
                return "comprehensive" if source_matches > 0 else "simple"

        test_engine = TestFallback()

        # 测试关键词匹配
        keyword_tests = [
            ("这些信息出自哪里？", "comprehensive"),
            ("根据什么资料？", "comprehensive"),
            ("原文是什么？", "comprehensive"),
            ("什么是AI？", "simple"),
            ("如何学习编程？", "simple"),
        ]

        for query, expected in keyword_tests:
            result = test_engine._fallback_keyword_classification(query)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{query}' -> {result} (期望: {expected})")

    except Exception as e:
        print(f"❌ 后备机制测试失败: {e}")

if __name__ == "__main__":
    print("🚀 开始测试基于LLM的意图识别功能")

    # 运行主要测试
    accuracy = test_intent_classification()

    # 测试后备机制
    test_fallback_mechanism()

    print(f"\n🏁 测试完成！")
    print(f"总体准确率: {accuracy:.1f}%")