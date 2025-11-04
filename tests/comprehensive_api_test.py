#!/usr/bin/env python3
"""
集中测试所有RAG API接口的综合测试脚本
测试内容：
1. 健康检查接口
2. RAG流式对话接口
3. 普通查询接口
4. 反馈收集接口
"""

import json
import requests
import time
import sys
from typing import Dict, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, test_name: str, status: str, details: str = "", duration: float = 0):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "duration": duration,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)

        # 实时显示结果
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status} ({duration:.2f}s)")
        if details:
            print(f"     {details}")
        print()

    def test_health_check(self) -> bool:
        """测试健康检查接口"""
        test_name = "健康检查接口 (GET /health)"
        start_time = time.time()

        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                details = f"状态: {data.get('status')}, 消息: {data.get('message')}"
                self.log_test(test_name, "PASS", details, duration)
                return True
            else:
                details = f"HTTP错误: {response.status_code}"
                self.log_test(test_name, "FAIL", details, duration)
                return False

        except Exception as e:
            duration = time.time() - start_time
            details = f"连接错误: {str(e)}"
            self.log_test(test_name, "FAIL", details, duration)
            return False

    def test_stream_chat(self) -> bool:
        """测试RAG流式对话接口"""
        test_name = "RAG流式对话接口 (POST /api/rag/chat/stream)"
        start_time = time.time()

        request_data = {
            "user_id": "researcher",
            "question": "什么是大数据技术？",
            "session_id": "research_001",
            "stream": True
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/rag/chat/stream",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },
                stream=True,
                timeout=120
            )

            duration = time.time() - start_time

            if response.status_code != 200:
                details = f"HTTP错误: {response.status_code}"
                self.log_test(test_name, "FAIL", details, duration)
                return False

            # 解析流式响应
            events = []
            content_parts = []
            sources = []

            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('event:'):
                    events.append(line[6:].strip())
                elif line.startswith('data:'):
                    try:
                        data = json.loads(line[6:])
                        if data.get('type') == 'delta':
                            content_parts.append(data.get('content', ''))
                        elif data.get('type') == 'sources':
                            sources = data.get('sources', [])
                    except json.JSONDecodeError:
                        pass

            full_content = ''.join(content_parts)

            # 验证响应完整性
            has_start = 'start' in events
            has_end = 'end' in events
            has_delta = 'delta' in events
            has_sources = 'sources' in events

            if has_start and has_end and has_delta:
                details = (f"流式响应正常, 内容长度: {len(full_content)}字符, "
                          f"来源数量: {len(sources)}, 事件类型: {set(events)}")

                # 创建详细的结果数据，包含响应内容
                stream_result = {
                    "test_name": test_name,
                    "status": "PASS",
                    "details": details,
                    "duration": duration,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "request": request_data,
                    "response": {
                        "full_content": full_content,
                        "content_length": len(full_content),
                        "sources": sources,
                        "events": events,
                        "event_types": list(set(events))
                    }
                }
                # 替换最后一个结果为详细版本
                if self.test_results and self.test_results[-1]["test_name"] == test_name:
                    self.test_results[-1] = stream_result
                else:
                    self.test_results.append(stream_result)

                # 显示结果
                status_icon = "✅"
                print(f"{status_icon} {test_name}: PASS ({duration:.2f}s)")
                print(f"     {details}")
                print()

                return True
            else:
                details = f"流式响应不完整, 事件: {set(events)}"

                # 创建失败时的详细结果
                stream_result = {
                    "test_name": test_name,
                    "status": "FAIL",
                    "details": details,
                    "duration": duration,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "request": request_data,
                    "response": {
                        "partial_content": full_content,
                        "content_length": len(full_content),
                        "sources": sources,
                        "events": events,
                        "event_types": list(set(events)),
                        "error": "响应不完整"
                    }
                }

                if self.test_results and self.test_results[-1]["test_name"] == test_name:
                    self.test_results[-1] = stream_result
                else:
                    self.test_results.append(stream_result)

                # 显示结果
                status_icon = "❌"
                print(f"{status_icon} {test_name}: FAIL ({duration:.2f}s)")
                print(f"     {details}")
                print()

                return False

        except Exception as e:
            duration = time.time() - start_time
            details = f"错误: {str(e)}"

            # 创建异常时的详细结果
            stream_result = {
                "test_name": test_name,
                "status": "FAIL",
                "details": details,
                "duration": duration,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "request": request_data,
                "response": {
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            }

            if self.test_results and self.test_results[-1]["test_name"] == test_name:
                self.test_results[-1] = stream_result
            else:
                self.test_results.append(stream_result)

            # 显示结果
            status_icon = "❌"
            print(f"{status_icon} {test_name}: FAIL ({duration:.2f}s)")
            print(f"     {details}")
            print()

            return False

    def test_query(self) -> bool:
        """测试普通查询接口"""
        test_name = "普通查询接口 (POST /api/query)"
        start_time = time.time()

        request_data = {
            "query": "什么是大数据技术？",
            "mode": "general"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/query",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            duration = time.time() - start_time

            if response.status_code != 200:
                details = f"HTTP错误: {response.status_code}"
                self.log_test(test_name, "FAIL", details, duration)
                return False

            data = response.json()

            # 验证响应格式
            required_fields = ['query', 'response', 'evaluation']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                details = f"响应缺少字段: {missing_fields}"

                # 创建失败时的详细结果
                query_result = {
                    "test_name": test_name,
                    "status": "FAIL",
                    "details": details,
                    "duration": duration,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "request": request_data,
                    "response": {
                        "error": f"响应缺少字段: {missing_fields}",
                        "received_data": data
                    }
                }

                if self.test_results and self.test_results[-1]["test_name"] == test_name:
                    self.test_results[-1] = query_result
                else:
                    self.test_results.append(query_result)

                # 显示结果
                status_icon = "❌"
                print(f"{status_icon} {test_name}: FAIL ({duration:.2f}s)")
                print(f"     {details}")
                print()

                return False

            response_length = len(data.get('response', ''))
            evaluation = data.get('evaluation', {})
            overall_score = evaluation.get('overall_score', 0)

            details = (f"回答长度: {response_length}字符, "
                      f"评估分数: {overall_score:.2f}")

            # 创建详细的结果数据，包含响应内容
            query_result = {
                "test_name": test_name,
                "status": "PASS",
                "details": details,
                "duration": duration,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "request": request_data,
                "response": {
                    "query": data.get('query'),
                    "response": data.get('response'),
                    "response_length": response_length,
                    "evaluation": evaluation,
                    "relevance_score": evaluation.get('relevance_score', 0),
                    "completeness_score": evaluation.get('completeness_score', 0),
                    "accuracy_score": evaluation.get('accuracy_score', 0),
                    "overall_score": overall_score,
                    "timestamp": evaluation.get('timestamp')
                }
            }
            # 替换最后一个结果为详细版本
            if self.test_results and self.test_results[-1]["test_name"] == test_name:
                self.test_results[-1] = query_result
            else:
                self.test_results.append(query_result)

            # 显示结果
            status_icon = "✅"
            print(f"{status_icon} {test_name}: PASS ({duration:.2f}s)")
            print(f"     {details}")
            print()

            return True

        except Exception as e:
            duration = time.time() - start_time
            details = f"错误: {str(e)}"
            self.log_test(test_name, "FAIL", details, duration)
            return False

    def test_feedback(self) -> bool:
        """测试反馈收集接口"""
        test_name = "反馈收集接口 (POST /api/feedback)"
        start_time = time.time()

        request_data = {
            "query": "什么是机器学习?",
            "response": "机器学习是人工智能的一个分支，它使计算机能够在不进行明确编程的情况下从数据中学习。",
            "rating": 5,
            "comment": "回答很详细，帮助很大！"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/feedback",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            duration = time.time() - start_time

            if response.status_code != 200:
                details = f"HTTP错误: {response.status_code}"
                self.log_test(test_name, "FAIL", details, duration)
                return False

            data = response.json()

            if data.get('message') == 'Feedback received successfully':
                details = f"反馈接收成功, 评分: {request_data['rating']}/5"
                self.log_test(test_name, "PASS", details, duration)
                return True
            else:
                details = f"响应异常: {data}"
                self.log_test(test_name, "FAIL", details, duration)
                return False

        except Exception as e:
            duration = time.time() - start_time
            details = f"错误: {str(e)}"
            self.log_test(test_name, "FAIL", details, duration)
            return False

    def test_stats(self) -> bool:
        """测试系统统计接口"""
        test_name = "系统统计接口 (GET /api/stats)"
        start_time = time.time()

        try:
            response = self.session.get(f"{self.base_url}/api/stats", timeout=10)
            duration = time.time() - start_time

            if response.status_code != 200:
                details = f"HTTP错误: {response.status_code}"
                self.log_test(test_name, "FAIL", details, duration)
                return False

            data = response.json()

            # 验证响应格式
            required_fields = ['performance_metrics', 'feedback_summary', 'data_stats']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                details = f"响应缺少字段: {missing_fields}"

                # 创建失败时的详细结果
                stats_result = {
                    "test_name": test_name,
                    "status": "FAIL",
                    "details": details,
                    "duration": duration,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "response": {
                        "error": f"响应缺少字段: {missing_fields}",
                        "received_data": data
                    }
                }

                if self.test_results and self.test_results[-1]["test_name"] == test_name:
                    self.test_results[-1] = stats_result
                else:
                    self.test_results.append(stats_result)

                # 显示结果
                status_icon = "❌"
                print(f"{status_icon} {test_name}: FAIL ({duration:.2f}s)")
                print(f"     {details}")
                print()

                return False

            # 提取关键统计信息
            perf_metrics = data.get('performance_metrics', {})
            feedback_summary = data.get('feedback_summary', {})
            data_stats = data.get('data_stats', {})

            total_evaluations = perf_metrics.get('total_evaluations', 0)
            avg_relevance = perf_metrics.get('average_relevance', 0)
            avg_accuracy = perf_metrics.get('average_accuracy', 0)
            total_feedback = feedback_summary.get('total_feedback', 0)
            avg_rating = feedback_summary.get('average_rating', 0)
            total_docs = data_stats.get('total_docs', 0)

            details = (f"总评估: {total_evaluations}次, 相关性: {avg_relevance:.2f}, "
                      f"准确性: {avg_accuracy:.2f}, 反馈: {total_feedback}条, "
                      f"文档: {total_docs}个")

            # 创建详细的结果数据，包含统计内容
            stats_result = {
                "test_name": test_name,
                "status": "PASS",
                "details": details,
                "duration": duration,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "response": {
                    "performance_metrics": perf_metrics,
                    "feedback_summary": feedback_summary,
                    "data_stats": data_stats,
                    "summary": {
                        "total_evaluations": total_evaluations,
                        "average_relevance": avg_relevance,
                        "average_accuracy": avg_accuracy,
                        "total_feedback": total_feedback,
                        "average_rating": avg_rating,
                        "total_documents": total_docs
                    }
                }
            }
            # 替换最后一个结果为详细版本
            if self.test_results and self.test_results[-1]["test_name"] == test_name:
                self.test_results[-1] = stats_result
            else:
                self.test_results.append(stats_result)

            # 显示结果
            status_icon = "✅"
            print(f"{status_icon} {test_name}: PASS ({duration:.2f}s)")
            print(f"     {details}")
            print()

            return True

        except Exception as e:
            duration = time.time() - start_time
            details = f"错误: {str(e)}"

            # 创建异常时的详细结果
            stats_result = {
                "test_name": test_name,
                "status": "FAIL",
                "details": details,
                "duration": duration,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "response": {
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            }

            if self.test_results and self.test_results[-1]["test_name"] == test_name:
                self.test_results[-1] = stats_result
            else:
                self.test_results.append(stats_result)

            # 显示结果
            status_icon = "❌"
            print(f"{status_icon} {test_name}: FAIL ({duration:.2f}s)")
            print(f"     {details}")
            print()

            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print(" 开始RAG API综合测试")
        print("=" * 60)
        print(f" 测试目标: {self.base_url}")
        print(f" 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        total_start_time = time.time()

        # 运行所有测试
        tests = [
            # ("健康检查", self.test_health_check),
            ("流式对话", self.test_stream_chat),
            # ("普通查询", self.test_query),
            # ("反馈收集", self.test_feedback),
            # ("系统统计", self.test_stats)
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            print(f"🔍 正在测试: {test_name}")
            if test_func():
                passed += 1
            else:
                failed += 1
            time.sleep(1)  # 测试间隔

        total_duration = time.time() - total_start_time

        # 生成测试报告
        print("=" * 60)
        print(" 测试结果汇总")
        print("=" * 60)
        print(f" 通过: {passed}")
        print(f" 失败: {failed}")
        print(f" 成功率: {passed/(passed+failed)*100:.1f}%")
        print(f"  总耗时: {total_duration:.2f}秒")
        print(f" 完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 详细结果
        print(" 详细测试结果:")
        print("-" * 60)
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test_name']}: {result['status']} ({result['duration']:.2f}s)")
            if result['details']:
                print(f"     {result['details']}")

        # 返回测试结果
        return {
            "total_tests": passed + failed,
            "passed": passed,
            "failed": failed,
            "success_rate": passed/(passed+failed)*100 if (passed+failed) > 0 else 0,
            "total_duration": total_duration,
            "results": self.test_results
        }

def main():
    """主函数"""
    print(" RAG API 综合测试工具")
    print("=" * 60)

    # 检查服务器是否可用
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print("⚠️ 服务器响应异常，但继续测试...")
    except:
        print("❌ 无法连接到服务器，请确保服务器正在运行在 http://localhost:8000")
        print("💡 启动命令: python3 web_app.py")
        sys.exit(1)

    print()

    # 创建测试器并运行测试
    tester = APITester()
    results = tester.run_all_tests()

    # 保存测试结果到文件
    report_file = "api_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n  测试报告已保存到: {report_file}")

    # 返回退出码
    if results["failed"] == 0:
        print("🎉 所有测试通过！")
        return 0
    else:
        print(f"⚠️  有 {results['failed']} 个测试失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)