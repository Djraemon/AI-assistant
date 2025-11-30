#!/usr/bin/env python3
"""
测试文件扫描器功能
Test file scanner functionality
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.file_scanner import FileScanner, AutoIndexer
from src.config import CONFIG


def test_file_scanner():
    """测试文件扫描器基本功能"""
    print("=" * 60)
    print("测试文件扫描器基本功能")
    print("=" * 60)

    # 创建扫描器
    scanner = FileScanner(data_dir="data")

    # 执行扫描
    scan_result = scanner.scan_all_files()

    print(f"\n📂 扫描结果:")
    print(f"  新增文件: {len(scan_result['new_files'])} 个")
    print(f"  修改文件: {len(scan_result['modified_files'])} 个")
    print(f"  现有文件: {len(scan_result['existing_files'])} 个")
    print(f"  错误文件: {len(scan_result['error_files'])} 个")

    if scan_result['new_files']:
        print(f"\n新增文件列表:")
        for file in scan_result['new_files']:
            print(f"  - {file}")

    if scan_result['modified_files']:
        print(f"\n修改文件列表:")
        for file in scan_result['modified_files']:
            print(f"  - {file}")

    # 显示统计信息
    stats = scanner.get_stats()
    print(f"\n📊 统计信息:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  总大小: {stats['total_size_mb']:.2f} MB")
    print(f"  按状态分布: {stats['by_status']}")
    print(f"  按类型分布: {stats['by_extension']}")

    # 获取未处理文件
    unprocessed = scanner.get_unprocessed_files()
    print(f"\n🔄 未处理文件: {len(unprocessed)} 个")
    if unprocessed:
        for file in unprocessed[:5]:  # 只显示前5个
            print(f"  - {file}")
        if len(unprocessed) > 5:
            print(f"  ... 还有 {len(unprocessed) - 5} 个文件")

    return scan_result


def test_auto_indexer():
    """测试自动索引器功能"""
    print("\n" + "=" * 60)
    print("测试自动索引器功能")
    print("=" * 60)

    try:
        # 创建自动索引器
        auto_indexer = AutoIndexer(data_dir="data")

        # 执行扫描和处理
        result = auto_indexer.scan_and_process()

        print(f"\n📋 自动索引结果:")
        scan_result = result['scan_result']
        process_result = result['process_result']

        print(f"  扫描发现:")
        print(f"    新增: {len(scan_result['new_files'])} 个")
        print(f"    修改: {len(scan_result['modified_files'])} 个")
        print(f"    现有: {len(scan_result['existing_files'])} 个")

        print(f"  处理结果:")
        print(f"    成功: {process_result['processed_count']} 个")
        print(f"    失败: {process_result['failed_count']} 个")
        print(f"    消息: {process_result['message']}")

        if process_result['processed_files']:
            print(f"\n✅ 成功处理的文件:")
            for file in process_result['processed_files']:
                metadata = auto_indexer.scanner.get_file_metadata(file)
                if metadata and metadata.get('processing_result'):
                    proc_result = metadata['processing_result']
                    print(f"    - {file} (内容长度: {proc_result.get('content_length', 0)} 字符)")
                else:
                    print(f"    - {file}")

        if process_result['failed_files']:
            print(f"\n❌ 处理失败的文件:")
            for file in process_result['failed_files']:
                metadata = auto_indexer.scanner.get_file_metadata(file)
                error_msg = metadata.get('error_message', '未知错误') if metadata else '未找到元数据'
                print(f"    - {file}: {error_msg}")

        return result

    except Exception as e:
        print(f"❌ 自动索引器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_sample_file_processing():
    """测试单个文件处理"""
    print("\n" + "=" * 60)
    print("测试单个文件处理")
    print("=" * 60)

    # 创建自动索引器
    auto_indexer = AutoIndexer(data_dir="data")

    # 获取第一个未处理的文件
    unprocessed = auto_indexer.scanner.get_unprocessed_files()
    if not unprocessed:
        print("没有找到未处理的文件")
        return

    test_file = unprocessed[0]
    print(f"🔍 测试处理文件: {test_file}")

    try:
        result = auto_indexer.process_file(test_file)
        if result:
            print(f"✅ 文件处理成功:")
            print(f"  相对路径: {result['relative_path']}")
            print(f"  内容长度: {result['content_length']}")
            print(f"  源类型: {result['source_type']}")
            print(f"  源目录: {result['source_dir']}")
            print(f"  有课程元数据: {'是' if result['course_metadata'] else '否'}")

            if result['course_metadata']:
                print(f"  课程主题: {result['course_metadata'].get('course_topic', '无')[:50]}...")
        else:
            print(f"❌ 文件处理失败")

    except Exception as e:
        print(f"❌ 文件处理出错: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("🧪 开始测试文件扫描器功能")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"数据目录: {Path('data').absolute()}")

    # 检查数据目录是否存在
    if not os.path.exists("data"):
        print("❌ 数据目录 'data' 不存在")
        return

    # 测试基本扫描功能
    scan_result = test_file_scanner()

    # 测试单个文件处理
    test_sample_file_processing()

    # 测试自动索引功能
    auto_index_result = test_auto_indexer()

    print("\n" + "=" * 60)
    print("🎉 测试完成")
    print("=" * 60)

    if auto_index_result:
        print("✅ 文件扫描和自动索引功能正常工作")
    else:
        print("⚠️ 部分功能可能存在问题，请检查错误信息")


if __name__ == "__main__":
    main()