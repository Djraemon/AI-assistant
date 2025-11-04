#!/usr/bin/env python3
"""测试中文流式响应的专用脚本"""

import json
import requests
import asyncio

async def test_chinese_stream():
    """测试中文流式响应"""

    url = "http://localhost:8000/api/rag/chat/stream"

    # 请求数据
    request_data = {
        "user_id": "test_chinese",
        "question": "请详细解释卷积神经网络的工作原理和在图像识别中的应用",
        "session_id": "chinese_test_001",
        "stream": True
    }

    print("🧪 测试中文流式响应...")
    print(f"📝 问题: {request_data['question']}")
    print("="*60)

    try:
        response = requests.post(
            url,
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True,
            timeout=120
        )

        if response.status_code != 200:
            print(f"❌ 错误: HTTP {response.status_code}")
            print(response.text)
            return

        print("✅ 连接成功！\n")

        full_content = []
        sources = []

        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('event:'):
                event_type = line[6:].strip()
                print(f"🔔 事件: {event_type}")

            elif line.startswith('data:'):
                try:
                    data = json.loads(line[6:])

                    if data.get('type') == 'start':
                        print("🚀 开始流式响应...")

                    elif data.get('type') == 'delta':
                        content = data.get('content', '')
                        print(content, end='', flush=True)
                        full_content.append(content)

                    elif data.get('type') == 'sources':
                        sources = data.get('sources', [])
                        print(f"\n\n📚 引用来源 ({len(sources)}个):")
                        for i, source in enumerate(sources[:3], 1):
                            print(f"   {i}. {source.get('node_name', '未知文档')}")
                            excerpt = source.get('excerpt', '')[:100]
                            print(f"      摘要: {excerpt}...")

                    elif data.get('type') == 'end':
                        tokens = data.get('total_tokens', 0)
                        print(f"\n\n🏁 响应完成!")
                        print(f"📊 总token数: {tokens}")

                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON解析错误: {e}")

        # 显示完整内容
        print("\n" + "="*60)
        print("📋 完整回答预览:")
        full_text = ''.join(full_content)
        print(full_text[:500] + "..." if len(full_text) > 500 else full_text)

        print(f"\n📏 回答长度: {len(full_text)} 字符")
        print(f"📚 引用来源: {len(sources)} 个")

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    print("🧪 中文流式响应测试工具")
    print("="*60)

    # 运行异步测试
    asyncio.run(test_chinese_stream())