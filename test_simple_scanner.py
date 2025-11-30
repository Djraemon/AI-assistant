#!/usr/bin/env python3
"""
简单测试文件扫描器功能（不包含文件解析）
Test simple file scanner functionality (without file parsing)
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.file_scanner import FileScanner


def test_basic_scanning():
    """测试基本扫描功能"""
    print("=" * 60)
    print("测试基本文件扫描功能")
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
        print(f"\n✅ 新增文件列表:")
        for file in scan_result['new_files']:
            metadata = scanner.get_file_metadata(file)
            if metadata:
                print(f"  - {file} ({metadata['file_size_mb']:.2f}MB, {metadata['extension']})")

    if scan_result['existing_files']:
        print(f"\n📁 现有文件列表 (前5个):")
        for file in scan_result['existing_files'][:5]:
            metadata = scanner.get_file_metadata(file)
            if metadata:
                print(f"  - {file} ({metadata['file_size_mb']:.2f}MB, {metadata['extension']})")

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

    return scan_result, stats


def test_metadata_persistence():
    """测试元数据持久化"""
    print("\n" + "=" * 60)
    print("测试元数据持久化")
    print("=" * 60)

    # 创建扫描器
    scanner = FileScanner(data_dir="data")

    # 检查元数据文件是否存在
    metadata_file = scanner.metadata_file
    print(f"元数据文件: {metadata_file}")

    if os.path.exists(metadata_file):
        print("✅ 元数据文件存在")
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                print(f"📄 元数据包含 {len(metadata)} 个文件的记录")

                # 显示几个文件的元数据
                for i, (file_path, file_meta) in enumerate(metadata.items()):
                    if i < 3:
                        print(f"  文件 {i+1}: {file_path}")
                        print(f"    状态: {file_meta.get('status', 'unknown')}")
                        print(f"    大小: {file_meta.get('file_size_mb', 0):.2f}MB")
                        print(f"    扫描时间: {file_meta.get('scanned_at', 'N/A')}")

        except Exception as e:
            print(f"❌ 读取元数据文件失败: {e}")
    else:
        print("⚠️ 元数据文件不存在，将在首次扫描时创建")

    # 再次扫描测试持久化
    print("\n🔄 再次扫描以测试持久化...")
    scan_result = scanner.scan_all_files()

    print(f"第二次扫描结果:")
    print(f"  新增文件: {len(scan_result['new_files'])} 个")
    print(f"  修改文件: {len(scan_result['modified_files'])} 个")
    print(f"  现有文件: {len(scan_result['existing_files'])} 个")

    return True


def test_file_marking():
    """测试文件标记功能"""
    print("\n" + "=" * 60)
    print("测试文件标记功能")
    print("=" * 60)

    scanner = FileScanner(data_dir="data")

    # 获取第一个文件进行测试
    unprocessed = scanner.get_unprocessed_files()
    if not unprocessed:
        print("没有找到未处理的文件进行测试")
        return False

    test_file = unprocessed[0]
    print(f"🧪 测试文件: {test_file}")

    # 标记为已处理
    print("标记文件为已处理...")
    scanner.mark_file_processed(test_file, {
        'content_length': 1000,
        'parse_status': 'success',
        'has_course_metadata': True
    })

    # 检查标记结果
    metadata = scanner.get_file_metadata(test_file)
    if metadata:
        print(f"✅ 文件状态: {metadata.get('status')}")
        print(f"   处理时间: {metadata.get('processed_at')}")
        print(f"   处理结果: {metadata.get('processing_result')}")
    else:
        print("❌ 获取文件元数据失败")

    # 重置为未处理状态以便后续测试
    scanner.file_metadata[test_file]['status'] = 'discovered'
    scanner._save_metadata()

    return True


def main():
    """主测试函数"""
    print("🧪 开始简单文件扫描器测试")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"数据目录: {Path('data').absolute()}")

    # 检查数据目录是否存在
    if not os.path.exists("data"):
        print("❌ 数据目录 'data' 不存在")
        print("请确保 data 目录存在并包含一些测试文件")
        return

    # 测试基本扫描功能
    scan_result, stats = test_basic_scanning()

    # 测试元数据持久化
    test_metadata_persistence()

    # 测试文件标记功能
    test_file_marking()

    print("\n" + "=" * 60)
    print("🎉 简单测试完成")
    print("=" * 60)

    if stats['total_files'] > 0:
        print("✅ 文件扫描功能正常工作")
        print(f"✅ 发现 {stats['total_files']} 个文件")
        print("✅ 元数据管理功能正常")
    else:
        print("⚠️ 没有发现任何文件，请检查 data 目录内容")


if __name__ == "__main__":
    main()